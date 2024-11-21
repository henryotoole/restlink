"""
Tests for the API class.

2024
"""
__author__ = "Josh Reed"

# Local code
from restlink import API, SchemaDB
from tests.fixtures.schemas import schema_simple

# Other libs
import pytest

# Base python
import json

@pytest.fixture
def api():
	return API("test", "v1", "Test API")

def test_doc_basic_setup(api: API):
	"""Test that servers and info blocks are correct.
	"""
	api.doc_set_servers("/base_path")

	target = {
		"servers": [
			{"url": "/base_path/test/v1"}
		],
		"paths": {},
		"info": {"title": "Test API", "version": "v1"},
		"openapi": "3.1.0"
	}
	
	assert api.doc_view_fn() == target

def test_doc_addition_schema(api: API, schema_simple: SchemaDB):
	"""Test that a schema can be added to the documentation an that update edge trigger properly. This action
	adds both the base schema as a component and all possible paths.
	"""
	schema_simple._method_map_ = {
		"GET": {
			"specific": {
				"function": "get",
				"responses": {
					"200": "_schema_",
				}
			},
			"general": {
				"params": {
					'filter': {
						'required': False,
						'description': "ETC",
					}
				},
				"function": "list",
				"responses": {
					"200": {
						'type': 'list',
						'items': {'type': 'integer'}
					},
				}
			}
		},
		"POST": {
			"general": {
				"data": "_schema_",
				"function": "post",
				"responses": {
					"200": "_schema_",
					"400": {'type': 'object', 'properties': { 'error': {'type': 'string'}}},
					"404": {'type': 'object', 'properties': { 'error': {'type': 'string'}}},
				}
			}
		},
		"PUT": {
			"specific": {
				"data": "_schema_",
				"function": "put",
				"responses": {
					"200": "_schema_",
				}
			},
		},
		"DELETE": {
			"specific": {
				"function": "delete",
				"responses": {
					"200": None,
				}
			},
		}
	}

	api.doc_add_schema(schema_simple)

	target_components = {
		"schemas": {
			"simple": {
				"type": "object",
				"properties": {
					"id": {
						"type": "integer", "readOnly": True
					},
					"field_a": {
						"type": "integer"
					}, 
					"field_b": {
						"type": "string", 
						"minLength": 1, 
						"maxLength": 16
					}
				}
			}
		}
	}

	target_paths = {
		"simple/{id}": {
			"get": {
				"parameters": [
					{
						"name": "id",
						"in": "path",
						"description": "simple ID",
						"required": True,
						"schema": {"type": "integer"},
					}
				],
				"responses": {
					"200": {
						"content": {
							"application/json": {
								"schema": {"$ref": "#/components/schemas/simple"}
							}
						}
					}
				},
			},
			"put": {
				"parameters": [
					{
						"name": "id",
						"in": "path",
						"description": "simple ID",
						"required": True,
						"schema": {"type": "integer"},
					}
				],
				"responses": {
					"200": {
						"content": {
							"application/json": {
								"schema": {"$ref": "#/components/schemas/simple"}
							}
						}
					}
				},
				"requestBody": {
					"content": {
						"application/json": {
							"schema": {"$ref": "#/components/schemas/simple"}
						}
					}
				},
			},
			"delete": {
				"parameters": [
					{
						"name": "id",
						"in": "path",
						"description": "simple ID",
						"required": True,
						"schema": {"type": "integer"},
					}
				],
				"responses": {"200": {"description": "Operation success"}},
			},
		},
		"simple": {
			"get": {
				"parameters": [
					{
						"name": "filter",
						"in": "query",
						"description": "ETC",
						"required": False,
					}
				],
				"responses": {
					"200": {
						"content": {
							"application/json": {
								"schema": {"type": "list", "items": {"type": "integer"}}
							}
						}
					}
				},
			},
			"post": {
				"parameters": [],
				"responses": {
					"200": {
						"content": {
							"application/json": {
								"schema": {"$ref": "#/components/schemas/simple"}
							}
						}
					},
					"400": {
						"content": {
							"application/json": {
								"schema": {
									"type": "object",
									"properties": {"error": {"type": "string"}},
								}
							}
						}
					},
					"404": {
						"content": {
							"application/json": {
								"schema": {
									"type": "object",
									"properties": {"error": {"type": "string"}},
								}
							}
						}
					},
				},
				"requestBody": {
					"content": {
						"application/json": {
							"schema": {"$ref": "#/components/schemas/simple"}
						}
					}
				},
			},
		},
	}


	docs = api.doc_view_fn()
	
	assert docs['components'] == target_components
	assert docs['paths'] == target_paths

def test_doc_external_modification(api: API):
	"""Ensure the external modification path correctly updates the doc view.
	"""

	api.doc_set_servers("/base_path")

	with api.doc_api_spec() as spec:
		spec.options['servers'] = [
			{
				"url": "ALTERED"
			}
		]

	docs = api.doc_view_fn()

	assert docs['servers'][0]['url'] == 'ALTERED'