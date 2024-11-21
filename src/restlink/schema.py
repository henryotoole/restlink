"""
Contains the base SchemaREST class, which itself extends the Marshmallow schema.

2024
"""
__author__ = "Josh Reed"

# Our code
from restlink.exceptions import RESTException

# Other libs
from marshmallow import Schema, ValidationError

# Base python
from pathlib import Path
import typing
import json

if typing.TYPE_CHECKING:
	from restlink.exposer import Exposer

class SchemaREST(Schema):
	"""This is the base class to represent a specific backend resource (like a database table). It is the 'noun'
	in the REST route URL.

	This is a basic extension of the Marshmallow schema with behaviors modified for use with REST API's.
	This class provides a base level *implementation* of a resource that will be exposed to REST routes. The
	methods that are 'exposed' are listed below:
	+ get()			- Get
	+ post()		- Creation
	+ put()			- Update
	+ delete()		- Delete
	+ list() 		- Get a list of ID's with optional filtering

	Not all methods are, of course, available for all schema's. Whether or not a methods is intended to be
	exposed for a certain schema is controlled by the `_allowed_methods_` class attribute. If, for example,
	"GET" was an allowed method, then all rest functions that begin with `get` would be exposed.

	**On Configuration**

	Use of a `SchemaREST` will naturally need some information from the end-use code in order to operate.
	The route name must be defined. If a database is to be accessed, the table name must be provided. In
	general, to configure a `SchemaREST`'s behavior, two mechanisms are possible:
	
	1. Single-underscore class attributes - These are used when a configuration value is shared across all
	possible instances of the schema. For example, a schema that accesses a table will *always* access
	the *same* table.
	2. Class method overwrite - This allows the end-code to define custom methods for complex operations,
	like validating an accessor's write access via lookup in a junction table.

	**Permissions**

	Permissions are handled by validate_can_read() and validate_can_write(). These functions will need to be
	overwritten for all non-public Schema's. They are given an "id" and "accessor identity" and should return
	a boolean that indicates whether that accessor has read or write access to that ID.

	`GET` is considered a read operation, and `PUT`, `POST`, and `DELETE` are all considered write operations.

	**On Implementations**

	Implementations of this class will find that every action (for example, `get()`) is broken into two steps:
	1. The original `action()` function, which is called. It validates access and then forwards the action to:
	2. A sub-function `_action()`, which actually does the action.

	A child class can override the `action()` function to change the nature of validation or the `_action()`
	function to change the nature of the action itself.

	The base SchemaREST class does not provide **any** default implementation for the `_action()` functions,
	as it does not make assumptions about what is upstream from the schema. Possible 'upstream' targets could
	be SQLAlchemy or a filesystem.
	"""

	# Single-underscore configuration defaults.
	_rest_path_ = None
	"""Base path for this schema to be exposed at. This can be as simple as 'noun' or a proper full path like
	'this/that/noun'. This is relative to the path defined by the API this schema is associated with.
	
	Note that this also sets the 'noun' or 'name' of this resource from the point of view of the API.
	"""
	_allowed_methods_ = []
	"""A list of HTTP methods that are allowed to be exposed to the web, e.g. GET, POST, PUT and DELETE. By
	default, no methods are allowed. The end-use code must manually specify them."""
	_method_map_ = {
		"GET": {
			"specific": {
				"function": "get",
				"responses": {
					"200": "_schema_",
					"403": {'type': 'object', 'properties': { 'error': {'type': 'string'}}},
					"404": {'type': 'object', 'properties': { 'error': {'type': 'string'}}},
				}
			},
			"general": {
				"params": {
					'filter': {
						'required': False,
						# I suppose this could be pulled from the docstring of the function, but I'm not overly
						# fond of that type of thing for a couple reasons...
						'description': "URL-encoded key/value data which is used to filter the returned ID list.",
					}
				},
				"function": "list",
				"responses": {
					# The key to a response is the HTTP Code, and the value becomes the 'schema' for the response
					# in the open api documentation. Two special values are allowed:
					# + None - in which an empty response of this code is sent
					# + "_schema_" - in which a reference to the relevant schema is used.
					#
					# In all cases where something is returned, it is encoded as application/json
					"200": {
						'type': 'list',
						'items': {'type': 'integer'}
					},
					"400": {'type': 'object', 'properties': { 'error': {'type': 'string'}}},
					"403": {'type': 'object', 'properties': { 'error': {'type': 'string'}}},
				}
			}
		},
		"POST": {
			"general": {
				# Data refers to what JSON data should be in the body of the request for this resource. This
				# value becomes the 'schema' part of the api doc requestBody unless it is "_schema_", in which
				# case a reference to a schema is used.
				"data": "_schema_",
				"function": "post",
				"responses": {
					"200": "_schema_",
					"400": {'type': 'object', 'properties': { 'error': {'type': 'string'}}},
					"403": {'type': 'object', 'properties': { 'error': {'type': 'string'}}},
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
					"400": {'type': 'object', 'properties': { 'error': {'type': 'string'}}},
					"403": {'type': 'object', 'properties': { 'error': {'type': 'string'}}},
					"404": {'type': 'object', 'properties': { 'error': {'type': 'string'}}},
				}
			},
		},
		"DELETE": {
			"specific": {
				"function": "delete",
				"responses": {
					"200": None,
					"400": {'type': 'object', 'properties': { 'error': {'type': 'string'}}},
					"403": {'type': 'object', 'properties': { 'error': {'type': 'string'}}},
					"404": {'type': 'object', 'properties': { 'error': {'type': 'string'}}},
				}
			},
		}
	}
	"""A mapping that configures what methods are available and some metadata about what's allowed. End-use
	code child classes will not generally need to alter this. I know it's rather imperfect, but the documentation
	for use of the _method_map_ lies in the comments within *this* method map above."""
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self._exposer = None
		"""A back-reference to the exposer that's set when a schema is registered.
		"""

	@property
	def exposer(self) -> 'Exposer':
		"""Returns:
			Exposer: The exposer singleton, which is back-referenced to this schema instance when it is registered.
		"""
		if self._exposer is None:
			raise ValueError("Schema has no back-reference to exposer singleton. Maybe it wasn't registered?")
		return self._exposer

	@property
	def path(self) -> str:
		"""Get the path for this schema specifically. The ultimate, resulting path for the schema's access
		will be a function of both the path of this schema and the path of the `API` it is associated with.
		
		Returns:
			str: The path for this schema, as a relative path.
		"""
		if self._rest_path_ is None:
			raise ValueError(f"Schema {self.__class__.__name__} has not defined an _rest_path_ variable.")
		return self._rest_path_.lstrip('/')

	@property
	def name(self) -> str:
		"""The 'name' of this resource. This is the word at the end of the url that this resource is accessed
		at. It is interpreted from the path.

		Returns:
			str: Name of the resource
		"""
		return Path(self.path).stem
	
	@property
	def allowed_methods(self) -> 'list[str]':
		"""A whitelist of HTTP Methods that may be exposed to the internet for a REST API.
		
		Returns:
			list[str]: List of allowed HTTP methods, by name and in all caps (e.g. GET, POST, PUT)
		"""
		valid = self._method_map_.keys()
		for method in self._allowed_methods_:
			if not method in valid:
				raise ValueError(f"Invalid method: {method}. Must be one of '{valid}'.")
		return self._allowed_methods_
	
	@property
	def exposed_methods(self) -> list:
		"""Get a flat list of all methods that are both allowed and implemented in this schema.

		Returns:
			list: Of tuples containing (
				http_verb (str), route_type (str), function_name (str), allowed_params (list)
			)
		"""
		outlist = []
		for http_verb, types in self._method_map_.items():
			for route_type, method_data in types.items():

				if http_verb in self._allowed_methods_:
					outlist.append(
						(http_verb, route_type, method_data.get('function'), method_data.get('params', {}))
					)
		return outlist

	def handle_error(self, exc: ValidationError, data, **kwargs):
		"""Raise a custom exception when (de)serialization fails as per the docs. Here is where SchemaRSA
		converts ValidationError to HTTPException

		Args:
			exc (ValidationError): The raised validation error
			data (dict): The original data dict, some or all of which failed validation.
		"""
		#raise exc
		raise RESTException(400, f"Validation failed for: {json.dumps(exc.messages)}")
	
	def method_get(self, http_verb, route_type) -> dict:
		"""Get the method name and allowed kwargs / params for a given verb and route type. Route type can be
		either "general" or "specific". General URLs end in .../noun; specific URLs include an identifier in
		the URL itself e.g. .../noun/4

		Args:
			http_verb (str): The verb, GET/POST/etc.
			type (str): The type of url to get the method for; either "specific" or "general"

		Raises:
			ValueError if no such method exists in the method map.

		Returns:
			dict: Method data dict.
		"""
		method_data = self._method_map_.get(http_verb, {}).get(route_type)

		if method_data is None:
			raise ValueError(
				f"{__class__.__name__} does not provide a method for {http_verb} on {route_type} routes in its " + \
				"method map."
			)
		
		return method_data
	
	def validate_can_read(self, id) -> bool:
		"""This is a base method that should be implemented by a child Schema class. This validates an already-
		authenticated credential for read access to this instance of the schema.

		The `accessor_identity` can be gotten by using the exposer.current_accessor. Merely import the
		exposer singleton in the end-code child class implementation.

		"Read access" refers to any operation that gets information about a resource. This would include the
		classical get() method and the list() method.

		Args:
			id (*): The ID of the schema instance to be read or None if a list is attempted.

		Returns:
			bool: Whether or not the accessor has read access to instances of this schema
		"""
		return True
	
	def validate_can_write(self, id) -> bool:
		"""This is a base method that should be implemented by a child Schema class. This validates an already-
		authenticated credential for write access to this instance of the schema.

		The `accessor_identity` can be gotten by using the exposer.current_accessor. Merely import the
		exposer singleton in the end-code child class implementation.

		"Write access" refers to any operation that modifies a resource. This would include the classical
		create, update, and delete methods.

		Args:
			id (*): The ID of the schema instance to be written or None if a creation is attempted.

		Returns:
			bool: Whether or not the accessor has write access to instances of this schema
		"""
		return False
	
	def get(self, id: int) -> dict:
		"""Validate and perform the basic GET operation on a schema instance of the provided ID.

		Args:
			id (int): An integer ID

		Returns:
			dict: 'serialized' data of this Schema
		"""
		if not self.validate_can_read(id): raise RESTException(
			403,
			f"Accessor does not have read access to {self.name}"
		)

		return self._get(id)
		
	def post(self, data: dict) -> dict:
		"""Validate and perform the basic POST operation on a schema instance of the provided ID. By default
		this will create a new instance. See _create().

		Args:
			id (int): An integer ID

		Returns:
			dict: 'serialized' data of this Schema
		"""
		if not self.validate_can_write(None):
			raise RESTException(
				403,
				f"Accessor does not have write access to {self.name}"
			)

		return self._create(data)
		
	def put(self, id: int, data: dict) -> dict:
		"""Validate and perform the basic PUT operation on a schema instance of the provided ID. By default, this
		will update an existing record with the provided data. See _update().

		Args:
			id (int): The ID of the resource to update
			data (dict): The data that came along with the request

		Returns:
			dict: 'serialized' data of the record after update
		"""
		if not self.validate_can_write(id): 
			raise RESTException(
				403,
				f"Accessor does not have write access to {self.name}"
			)

		return self._update(id, data)
	
	def delete(self, id: int):
		"""Validate and delete a record by its ID.

		Args:
			id (int): An integer ID of the record to delete
		"""
		if not self.validate_can_write(id):
			raise RESTException(
				403,
				f"Accessor does not have write access to {self.name}"
			)

		return self._delete(id)
	
	def list(self, filter=None) -> list:
		"""Return a list of ID's for all available ID's in this Schema's table.

		**On Filtering**
		Filtering is made automatically possible via the included 'filter' arg. When it is provided,
		it will take the form {"k1": "v1", "k2": "v2", ...}. The returned ID's should all have record data
		rows "k1" that have value "v1" and "k2" with "v2", etc.

		Record data that is excluded from serialization (for example, user passhash) is not allowed for filtering
		and will trip an error.

		Args:
			filter (dict, optional): Key/value data which is used to filter the returned ID.

		Returns:
			list: Of integer ID's.
		"""
		if not self.validate_can_read(None):
			raise RESTException(
				403,
				f"Accessor does not have read access to {self.name}"
			)
		
		return self._list(filter=filter)
	
	def _get(self, id: int) -> dict:
		"""Implements the actual action of performing get().

		Args:
			id (int): An integer ID

		Returns:
			dict: 'serialized' data of this Schema
		"""
		pass
	
	def _create(self, data: dict) -> dict:
		"""Implements the actual action of performing create().

		Args:
			data (dict): The data that came along with the request

		Returns:
			dict: 'serialized' data of the new record
		"""
		pass
	
	def _update(self, id: int, data: dict) -> dict:
		"""Implements the actual action of performing update().

		Args:
			id (int): An integer ID of the record to update
			data (dict): The data that came along with the request

		Returns:
			dict: 'serialized' data of the record after update
		"""
		pass
	
	def _delete(self, id: int):
		"""Implements the actual action of performing delete().

		Args:
			id (int): An integer ID of the record to delete
		"""
		pass

	def _list(self, filter=None):
		"""Implements the actual action of performing list().

		Args:
			filter (dict, optional): Key/value data which is used to filter the returned ID.

		Returns:
			list: Of integer ID's.
		"""
		pass

	def doc_get_operation_params(self, http_verb, route_type) -> list:
		"""Get the params for an operation for this schema. Params is a list of all non-request-body data
		used by an OpenAPI request, as per the specs. This will use the _method_map_ config for this schema.

		https://swagger.io/docs/specification/v3_0/describing-parameters/

		Args:
			http_verb (str): The verb, GET/POST/etc.
			type (str): The type of url to get the method for; either "specific" or "general"

		Returns:
			list: of dicts to represent individual parameters in the form expected by APISpec
		"""

		allowed_params = self.method_get(http_verb, route_type).get('params', {})

		# Determine parameters.
		parameters = []
		if route_type == "specific":
			parameters.append({
				'name': 'id',
				'in': 'path',
				'description': f"{self.name} ID",
				'required': True,
				'schema': {
					'type': 'integer'
				}
			})

		for param_name, param_data in allowed_params.items():
			parameters.append({
				'name': param_name,
				'in': 'query',
				'description': param_data['description'],
				'required': param_data['required']
			})

		return parameters
	
	def doc_get_operation_request_body(self, http_verb, route_type) -> dict:
		"""Get the documentation dict for the request body (`requestBody` in OpenAPI parlance). The data in
		this body is *always* json data, so all that needs specification in the _method_map_ is the expected
		schema. Most of the time, this will simply be this very schema.

		Args:
			http_verb (str): The verb, GET/POST/etc.
			type (str): The type of url to get the method for; either "specific" or "general"

		Returns:
			dict: that represents the expected request body data in the form expected by APISpec
		"""

		request_data = self.method_get(http_verb, route_type).get('data', None)

		request_body = None
		if request_data is not None:
			
			schema_data = None
			if request_data == '_schema_':
				# APISpec does automatic translation of name to #/path
				schema_data = self.name
			else:
				schema_data = request_data
			request_body = {
				'content': {
					'application/json': {
						'schema': schema_data
					}
				}
			}
		
		return request_body
	
	def doc_get_operation_response(self, http_verb, route_type) -> dict:
		"""Get the documentation dict for possible responses to an operation. This data is also always
		json-encoded, so all that needs specification in the _method_map_ config is the expected schema
		of each response code.

		Args:
			http_verb (str): The verb, GET/POST/etc.
			type (str): The type of url to get the method for; either "specific" or "general"

		Returns:
			dict: that represents the expected request body data in the form expected by APISpec
		"""
		response_map = self.method_get(http_verb, route_type).get('responses', {})

		responses = {}
		for http_code, response_data in response_map.items():
			if response_data is None:
				responses[http_code] = {'description': "Operation success"}
			else:
				schema_data = None
				if response_data == '_schema_':
					# APISpec does automatic translation of name to #/path
					schema_data = self.name
				else:
					schema_data = response_data

				responses[http_code] = {
					'content': {
						'application/json': {
							'schema': schema_data
						}
					}
				}
		
		return responses