"""
Tests for the base SchemaREST class.

2024
"""
__author__ = "Josh Reed"

# Local code
from restlink import SchemaDB
from restlink.exceptions import RESTException
from tests.fixtures.schemas import schema_simple

# Other libs
import pytest

# Base python

def test_exposed_methods(schema_simple: SchemaDB):
	"""Test that the schema exposed_methods() function behaves as expected.
	"""

	schema_simple._method_map_ = {
		"GET": {
			"specific": {
				"function": "get",
				"responses": {
					"200": "ETC"
				}
			},
			"general": {
				"params": {
					'param1': "ETC",
					'param2': "ETC",
				},
				"function": "list",
				"responses": {
					"200": "ETC"
				}
			}
		},
		"POST": {
			"general": {
				"function": "post",
				"responses": {
					"200": "ETC"
				},
				"data": "_schema_"
			}
		},
	}

	target = [
		('GET', 'specific', 'get', {}),
		('GET', 'general', 'list', {'param1': 'ETC', 'param2': 'ETC'}),
		('POST', 'general', 'post', {})
	]

	assert schema_simple.exposed_methods == target

def test_exceptions(schema_simple: SchemaDB):
	"""Test that validation errors are converted correctly.
	"""
	with pytest.raises(RESTException):
		schema_simple.load({'field_a': 1, 'field_b': "morethansixteencharacter"})

# TODO As complexity grows, it will be prudent to test the individual doc_get methods of the Schema as well.