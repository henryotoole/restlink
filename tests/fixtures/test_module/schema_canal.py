"""
Holds one of the test schema classes.

2024
"""
__author__ = "Josh Reed"

# Local code
from restlink import SchemaDB
from tests.fixtures.test_module.model_canal import Canal
from tests.fixtures.test_module.app import rest_exposer

# Other libs
from marshmallow import fields, post_load, validate

# Base python

class SchemaCanal(SchemaDB):
	
	_db_model_ = Canal
	_rest_path_ = "/canal"
	_allowed_methods_ = ["GET", "POST", "PUT", "DELETE"]

	id = fields.Int(strict=True, dump_only=True)
	width = fields.Integer()
	name = fields.String(validate=validate.Length(min=1, max=32))
	read_only = fields.Integer(dump_only=True)
	internal_only = fields.String()

	@post_load
	def make_canal(self, data: dict, **kwargs) -> Canal:
		"""Make a new page with json data which will be validated. This will create a new database record.

		Args:
			data (dict): request data

		Returns:
			Page: New page, instantiated from data. Will include ID.
		"""
		rec = Canal(data['width'], data['name'])
		rest_exposer.database_session.add(rec)
		rest_exposer.database_session.flush()
		return rec
	
		
	def validate_can_read(self, id) -> bool:
		# Read access is granted always, for this class
		return True
	
	def validate_can_write(self, id) -> bool:
		# Write access is only granted if there is an accessor, which is determined (simply) by the presence
		# of a certain param in the request.
		return rest_exposer.current_accessor is not None
	
	def _list(self, **kwargs):
		"""Return 'werk' if custom addition is used.
		"""
		if 'custom_addition' in kwargs:
			return 'werk'
		return super()._list(**kwargs)
	
class SchemaCanalRW(SchemaCanal):

	_rest_path_ = "/canal_rw"

	def validate_can_read(self, id) -> bool:
		if rest_exposer.current_accessor is None: return False
		return rest_exposer.current_accessor['extra'] == '1'
	
	def validate_can_write(self, id) -> bool:
		if rest_exposer.current_accessor is None: return False
		return rest_exposer.current_accessor['extra'] == '2'
	
SchemaCanal._method_map_["GET"]["general"]["params"]["custom_addition"] = {
	'required': False,
	'description': "Testing custom additions"
}