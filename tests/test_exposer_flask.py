"""
Test the Flask exposer methods as robustly as possible. These are more integration tests than unit tests.

2024
"""
__author__ = "Josh Reed"

# Local code
from tests.fixtures.db import db_sqlite_test, test_db_module, test_db
from tests.fixtures.flask import test_client
from tests.fixtures.util import Database
from tests.fixtures.test_module.model_canal import Canal

# Other libs
from flask.testing import FlaskClient
import pytest

# Base python
import json
import urllib.parse

auth_query = {'handshake': urllib.parse.quote(json.dumps("trustworthy"))}

@pytest.fixture
def db_records(test_db):

	c1 = Canal(7, "Oxford Canal")
	c2 = Canal(14, "Grand Junction")
	test_db.session.add(c1)
	test_db.session.add(c2)
	test_db.session.commit()

def test_flask_routes(test_db: Database, test_client: FlaskClient):
	"""Ensure that configured routes exist and behave as generally expected.
	"""
	d1 = json.dumps({'width': 7, 'name': "Oxford Canal"})
	d2 = json.dumps({'width': 14, 'name': "Grand Junction"})
	d3 = json.dumps({'width': 11, 'name': "Middle Level Navigations"})

	# Setup the database via a series of queries
	assert test_client.get("/api/v1/canal").get_json() == []
	assert test_client.post(
		f"/api/v1/canal",
		data=d1,
		query_string=auth_query,
		content_type="application/json"
	).status_code == 200
	assert test_client.post(
		f"/api/v1/canal",
		data=d2,
		query_string=auth_query,
		content_type="application/json"
	).status_code == 200
	assert test_client.get("/api/v1/canal").get_json() == [1, 2]

	# Test all basic allowed REST methods
	# LIST
	assert test_client.get("/api/v1/canal").get_json() == [1, 2]
	assert test_client.get(
		"/api/v1/canal",
		query_string={'filter': urllib.parse.quote(json.dumps({'width': 14}))}
	).get_json() == [2]
	# GET
	assert test_client.get("/api/v1/canal/1").get_json() == {
		'id': 1,
		'name': 'Oxford Canal',
		'read_only': 5,
		'width': 7
	}
	assert test_client.get("/api/v1/canal/99").status_code == 404
	# POST
	assert test_client.post(
		f"/api/v1/canal",
		data=d3,
		query_string=auth_query,
		content_type="application/json"
	).get_json() == {
		'id': 3,
		'name': 'Middle Level Navigations',
		'read_only': 5,
		'width': 11
	}
	# PUT
	assert test_client.put(
		f"/api/v1/canal/2",
		data=json.dumps({'width': 99}),
		query_string=auth_query,
		content_type="application/json"
	).get_json() == {
		'id': 2,
		'name': 'Grand Junction',
		'read_only': 5,
		'width': 99
	}
	# DELETE
	assert test_client.delete(
		f"/api/v1/canal/2",
		query_string=auth_query,
		content_type="application/json"
	).status_code == 200
	assert test_db.session.get(Canal, 2) is None
	assert test_db.session.get(Canal, 1) is not None

def test_flask_routes_security(db_records, test_db: Database, test_client: FlaskClient):
	"""Ensure that field that are 'internal/excluded', 'read_only/dump_only', etc. are treated properly.
	"""
	# Ensure that read_only and internal_only fields are honored.
	assert test_client.put(
		f"/api/v1/canal/2",
		data=json.dumps({'read_only': 99}),
		query_string=auth_query,
		content_type="application/json"
	).status_code == 400
	assert 'internal_only' not in test_client.get("/api/v1/canal/1").get_json()

	# Ensure that internal fields can't be filtered by.
	assert test_client.get(
		"/api/v1/canal",
		query_string={'filter': urllib.parse.quote(json.dumps({'internal_only': 14}))}
	).status_code == 401

def test_documentation_route(test_db: Database, test_client: FlaskClient):
	"""Test that documentation is available and accurate.
	"""
	doc_json = test_client.get("/api/v1/docs").get_json()
	
	assert 'servers' in doc_json
	assert 'components' in doc_json

def test_accessor_controls(test_db: Database, test_client: FlaskClient):
	"""Ensure that the use of the validate_can_x() will correctly prohibit access.
	"""

	d1 = json.dumps({'width': 11, 'name': "Middle Level Navigations"})

	auth_query_none = {'handshake': urllib.parse.quote(json.dumps("trustworthy"))}
	auth_query_read = {
		'handshake': urllib.parse.quote(json.dumps("trustworthy")),
		'extra': urllib.parse.quote(json.dumps("1")),
	}
	auth_query_write = {
		'handshake': urllib.parse.quote(json.dumps("trustworthy")),
		'extra': urllib.parse.quote(json.dumps("2")),
	}

	# Read doesn't work without correct auth extras
	assert test_client.get(
		f"/api/v1/canal_rw",
		query_string=auth_query_none
	).status_code == 403
	assert test_client.get(
		f"/api/v1/canal_rw/1",
		query_string=auth_query_none
	).status_code == 403

	# Read does work with correct auth extras
	assert test_client.get(
		f"/api/v1/canal_rw",
		query_string=auth_query_read
	).get_json() == []

	# Write doesn't work without aux extras
	assert test_client.post(
		f"/api/v1/canal_rw",
		data=d1,
		query_string=auth_query_read,
		content_type="application/json"
	).status_code == 403