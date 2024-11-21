"""
Schema fixtures.

2024
"""
__author__ = "Josh Reed"

# Local code
from restlink import SchemaDB
from tests.fixtures.db import Simple

# Other libs
import pytest
from marshmallow import fields, validate

# Base python

class SchemaSimple(SchemaDB):
	"""A very simple schema representation.
	"""

	_db_model_ = Simple
	_rest_path_ = "/simple"
	_allowed_methods_ = ["GET", "POST", "PUT", "DELETE"]

	id = fields.Int(strict=True, dump_only=True)
	field_a = fields.Integer()
	field_b = fields.String(validate=validate.Length(min=1, max=16))


@pytest.fixture
def schema_simple():

	return SchemaSimple()