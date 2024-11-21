"""
Tests for the database-accessing schema.

2024
"""
__author__ = "Josh Reed"

# Local code
from restlink import SchemaDB, Exposer, API, RESTException
from tests.fixtures.schemas import schema_simple, SchemaSimple
from tests.fixtures.db import Simple, test_db_module, test_db, db_sqlite_test
from tests.fixtures.util import DatabaseTesting

# Other libs
import pytest
from sqlalchemy import select

# Base python

@pytest.fixture
def db_records(test_db):

	data = [
		(1, "1"),
		(2, "2"),
		(3, "3"),
	]

	for a, b in data:
		rec = Simple(a, b)
		test_db.session.add(rec)
		test_db.session.commit()

@pytest.fixture
def schema_simple_db(test_db, schema_simple):
	"""Return the schema_simple instance, but attached to an exposer so that database action can be taken.
	"""
	api = API("test", "v1", "Test API")

	exposer = Exposer()
	exposer.register_schema(api, schema_simple)

	@exposer.database_session_getter
	def get_db_session():
		return test_db.session
	
	return schema_simple

def test_get(schema_simple_db: SchemaSimple, test_db: DatabaseTesting, db_records):
	"""Test the basic _get action method().
	"""

	assert schema_simple_db._get(1) == {'id': 1, 'field_a': 1, 'field_b': '1'}
	assert schema_simple_db._get(2) == {'id': 2, 'field_a': 2, 'field_b': '2'}
	with pytest.raises(RESTException) as exc:
		assert schema_simple_db._get(4) == None

def test_list(schema_simple_db: SchemaSimple, test_db: DatabaseTesting, db_records):
	"""Test the basic _list action method().
	"""

	assert schema_simple_db._list() == [1, 2, 3]
	assert schema_simple_db._list(filter={'field_a': 2}) == [2]

def test_create(schema_simple_db: SchemaSimple, test_db: DatabaseTesting, db_records):
	"""Test the basic _create action method().
	"""
	assert schema_simple_db._create({'field_a': 3, 'field_b': '3'}) == {'field_a': 3, 'field_b': '3'}
	assert test_db.session.execute(select(Simple).filter_by(field_a=3)).scalar().id == 3

def test_update(schema_simple_db: SchemaSimple, test_db: DatabaseTesting, db_records):
	"""Test the basic _update action method().
	"""
	assert schema_simple_db._update(2, {'field_a': 99}) == {'id': 2, 'field_a': 99, 'field_b': '2'}
	assert test_db.session.execute(select(Simple).filter_by(id=2)).scalar().field_a == 99

def test_delete(schema_simple_db: SchemaSimple, test_db: DatabaseTesting, db_records):
	"""Test the basic _delete action method().
	"""
	schema_simple_db._delete(2)
	assert test_db.session.get(Simple, 2) is None