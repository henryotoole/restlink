"""
This is a test module which exists so that the invocation process for the singleton and associated
import structure works correctly in an environment that is similar to real end-use code.

2024
"""
__author__ = "Josh Reed"

# Local code
from restlink import API

# Other libs
from sqlalchemy.orm import DeclarativeBase

# Base python


### Setup our declarative base ###
class Base(DeclarativeBase):
	pass



### Import flask app constructors ###
from tests.fixtures.test_module.app import init_app, rest_exposer



### Import and instantiate schema / API structure ###
from tests.fixtures.test_module.schema_canal import SchemaCanal, SchemaCanalRW

api = API('api', 'v1', "Test API")
schema_canal = SchemaCanal(exclude=['internal_only'])
schema_canal_rw = SchemaCanalRW(exclude=['internal_only'])

# Bind schema's to the exposer
rest_exposer.register_schema(api, schema_canal)
rest_exposer.register_schema(api, schema_canal_rw)