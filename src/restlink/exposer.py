"""
Exposer base class. Responsible for link from Schema 'outwards' towards internet. See class docstring
for deeper information.

2024
"""
__author__ = "Josh Reed"

# Local code
from restlink.api import API
from restlink.schema import SchemaREST
from restlink.exceptions import RESTException

# Other libs
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from sqlalchemy.orm import Session

# Base python
from abc import abstractmethod

class Exposer:
	"""The Exposer class literally exposes a module's REST `Schema`'s to the internet. It takes the form
	of the singleton design pattern. It should only ever be instantiated once and should be accessible
	from anywhere.

	**Lifecycle**

	1. Instantiate the singleton instance, providing any configuration.
	2. Link the instance to the backend framework object (e.g. the Flask app).
	3. Register Schema instances.

	**Architecture**

	Overall, the exposer acts as a focal point for the general operations of RESTLink. Its primary functions are:
	1. To provide an interface for authenticating access and fetching a database session.
	2. To provide a standard point at which to register schema's and API's together.
	3. To provide a set of base operations which can be selectively implemented by a child class to fit whatever
	   backend is in use (e.g. flask).

	The exposer is intended to be a singleton; however, the actual instantiation and access of the singleton
	instance are handled by the end code that uses the exposer.

	**Resulting REST Routes**
	
	The routes that will be set up for a given REST `Schema` depend on the configuration of the specific
	`Schema` being used. However, all *possible* options for an API object are detailed below. For more
	information on any given route, check the `SchemaREST` class's function docstring for whatever function
	is relevant to the method.

	Note that all param values are expected to be url encoded if they accompany a GET request.

	The very basic REST operations:
	```.. code-block:: text
	URL                 | METHOD  | Action
	--------------------+---------+--------------------------------------
	.../noun'           | GET     | Get a list of available ID's. Params:
	                    |         | + filter={"key", "val"}
	--------------------+---------+--------------------------------------
	.../noun'           | POST    | Create a new 'noun'
	--------------------+---------+--------------------------------------
	.../noun/<id>       | GET     | Get data for a specific 'noun'
	--------------------+---------+--------------------------------------
	.../noun/<id>       | PUT     | Update data for a specific 'noun'
	--------------------+---------+--------------------------------------
	.../noun/<id>       | DELETE  | Delete a 'noun'
	--------------------+---------+--------------------------------------
	```

	**Development**

	Development note: While nominally delineated from the 'flask' Exposer, the base Exposer class
	here heavily mirrors flask conventions. This is because I've not yet had the need or chance to try
	out an implementation with another backend. If restlink proves valuable in the long run, I'll
	inevitably refactor this to be more general purpose for a variety of backends.
	"""

	def __init__(self, base_path="/"):
		"""Instantiate the Exposer class. This should only be done once - the result is a singleton.

		Args:
			base_path (str, optional): The base path that all API's will lie under. Default to root.
		"""

		self._apis = {}
		"""All API's that have yet been registered with this Exposer, keyed by the `api.key` property.
		"""
		self._paths_registered = {}
		"""Tracker list of all paths yet registered.
		"""
		self._base_path = base_path
		"""The base path that all API's will lie under.
		"""

		# Callbacks which are created when certain methods of this class are used as decorators.
		self._authenticator_fn = None
		"""Callback for authenticating an accessor to the API.
		"""
		self._db_session_getter_fn = None
		"""Callback for fetching a database session instance.
		"""

	def authenticator(self, callback):
		"""This sets the method that's used to authenticate access to the API. Right now, this leaves all the
		heavy lifting and complexity up to the code that uses restlink. In my own use of this library, I usually
		just return the flask_login `current_user` object.

		It's best to use this method as decorator, so you'd wrap your authenticator function with this. E.g.

		```
		@exposer.authenticator
		def my_auth_method():
			# ... Validate user ...
			return validated_user_object # Or None if can't validate.
		```

		The callback will have no arguments and should return a 'accessor object' if an accessor can be
		authenticated and None otherwise. The 'accessor object' can be anything; restlink does not use
		it itself and just ensures that it's provided to the schema `validate_can_read()` and
		`validate_can_write()` methods.
		"""
		self._authenticator_fn = callback
		return self.authenticator_fn

	@property
	def authenticator_fn(self) -> 'function':
		"""Returns:
			a function that, when called, returns the 'accessor object' for the current accessor
		"""
		if self._authenticator_fn is None:
			raise ValueError(
				"No authenticator function has been provided for this restlink exposer. " + \
				"See Exposer.authenticator() in exposer.py for details."
			)

		return self._authenticator_fn
	
	@property
	def current_accessor(self):
		"""Returns:
			*: the current accessor object, a custom datatype defined by the end-code's provided authenticator
				function. Will be None if no accessor could be authenticated.
		"""
		return self.authenticator_fn()
	
	def database_session_getter(self, callback):
		"""This sets the method that's used to get a valid SQLAlchemy `Session` instance which can be used
		to interact with a database. The callback provided should return a `Session` instance that can
		immediately be used for read or write operations to the database.

		The session will be requested again every time a new operation is completed. It will not be stored
		for long periods of time (e.g. it will be released after every operation) so that there's no concern
		of it growing stale.

		It's best to use this method as decorator, so you'd wrap your session getter function with this. E.g.

		```
		@exposer.database_session_getter
		def get_session():
			# ... Get session ...
			return session
		```

		If using flask-sqlalchemy, getting the DB session can be as simple as returning the flask singleton.
		"""
		self._db_session_getter_fn = callback
		return self._db_session_getter_fn
	
	@property
	def database_session(self) -> Session:
		"""Get a database session instance that can be used to interact with the end-use code's database. This
		will only function if the end-use code has decorated a getter with `Exposer.database_session_getter`

		Accessing this property will call the session getter *every time*.

		Raises:
			ValueError: If no session getter exists.

		Returns:
			Session: live session instance
		"""
		if self._db_session_getter_fn is None:
			raise ValueError(
				"No database session getter function has been provided for this restlink exposer. " + \
				"See Exposer.database_session_getter() in exposer.py for details."
			)
		return self._db_session_getter_fn()

	def register_schema(self, api: API, schema: SchemaREST):
		"""Register a new REST Schema with this Exposer. This will expose RESTful routes to the provided schema
		and add it to the generated and hosted documentation for the provided API. This also back-links the
		exposer instance to the schema for use later.

		Raises:
			ValueError if a schema of this name is already registered against this API.

		Args:
			api (API): The API under which to register the schema.
			schema (SchemaREST): The schema itself to register.
		"""
		# Back-link schema
		schema._exposer = self

		# Detect and add API to known set
		if api.key not in self._apis:
			self._register_api(api)

		# Detect and add Schema under API
		if schema.name in self._apis[api.key]['schemas']:
			raise ValueError(f"Schema of name '{schema.name}' already registered to {api}.")
		self._apis[api.key]['schemas'][schema.name] = schema
		api.doc_add_schema(schema)

		# Call _routes_create()
		self._routes_create(api, schema)

	def _register_api(self, api: API):
		"""Register a new API with this Exposer. This is performed during the public method `register_exposed()`.
		This will add a reference to the API to this Exposer instance and ensure that its documentation
		gets exposed properly.

		Args:
			api (API): API instance
		"""
		api.doc_set_servers(self._base_path)
		self._apis[api.key] = {
			'api': api,
			'schemas': {}
		}
		self._route_create(
			api.path_get_docs(api.path_root_get(self._base_path)),
			f"{api.name}_{api.version}_docs",
			self._transfer_function_wrap(api.doc_view_fn),
			"GET"
		)

	def _routes_create(self, api: API, schema: SchemaREST):
		"""Create the routes required to expose this schema to the internet as it is configured. Also add all
		routes to the documentation of the provided API.

		Args:
			api (API): The API under which this schema is create.
			schema (SchemaREST): The schema instance itself.
		"""
		# Every route requires the following
		# 1. Automatic creation of unique endpoint name (easy)
		# 2. Automatic construction of the route rule (e.g. the URL)
		# 3. Construction of the 'transfer function', which itself must:
		#	1. Authenticate the accessor (move this to the semi-global exposer.current_accessor)
		#	2. Translate associated data (parameters for GET, body data for POST etc.)
		#	3. Actually call the schema's GET/POST/PUT method
		#	4. Return response string for request, probably a JSONified structure.

		for http_verb, route_type, function_name, allowed_params in schema.exposed_methods:

			transfer_function = self._transfer_function_create(
				schema, http_verb, route_type, function_name, allowed_params.keys()
			)
			route_rule = self._route_rule_for(route_type, api, schema)
			endpoint = f"{api.name}_{api.version}_{schema.name}_{http_verb}_{route_type[0]}"

			self._route_create(route_rule, endpoint, transfer_function, http_verb)
			
	def _route_rule_for(self, route_type, api: API, schema: SchemaREST):
		"""Get a route rule for a schema of provided route type under provided API. Route type specifies whether
		the route specifies a certain resource (e.g. .../noun/4) or the resource in general (e.g. .../noun)

		Args:
			route_type (str): Either "specific" or "general".
			api (API): The API under which this schema is registered.
			schema (SchemaREST): The Schema for the route rule

		Returns:
			str: A complete URL rule (or path) for this schema resource, API, and route type
		"""
		# NOTE This might have to change for backends other than flask.
		url_base = api.path_resource_get(api.path_root_get(self._base_path), schema)

		if route_type == "general":
			return url_base
		else:
			return f"{url_base}/<string:id>"

	@abstractmethod
	def _route_create(self, rule, endpoint, transfer_function, http_verb):
		"""This is the ultimate final 'export' point where the machinations of this class are thrown over the
		wall to whatever actually manages HTML routes. With the flask implementation, this will forward to
		the flask app's `add_url_rule()` function.

		On URL rules: https://tedboy.github.io/flask/interface_api.url_route_regis.html#url-route-registrations

		Args:
			rule (str): The route path. Can include flask-style matchers like <string:id>
			endpoint (str): A unique identifier for this route.
			transfer_function (function): The function that's called when a request hits the indicated rule.
			http_verb (str): The HTTP verb for this route
		"""
		pass 

	def _transfer_function_create(self, schema: SchemaREST, http_verb, route_type, function_name, allowed_params):
		"""Create a properly wrapped transfer function for the provided schema and route characteristics.

		This function is a sort of dumping ground for the ugly complexity of routing verbs / route types /
		args and kwargs. It's not beautiful, but the whole point of a black box is that you don't need to
		look inside.

		Args:
			schema (SchemaREST): The schema that provides the actual functionality that we will wrap.
			http_verb (str): The http action, like GET or PUT
			ctype (str): The route type, either "general" or "specific"
			function_name (str): The name of the function within 'schema' that will be called.
			allowed_params (list): Names of params that can be provided to this route and will be expected
				as possible kwargs of the function in question.

		Returns:
			function: A proper transfer function that can be provided to _route_register for creation of a
				URL rule.
		"""
		def transfer_function(id, data, params):

			# Filter out non-allowed param names.
			_params = {}
			for param_name, param_value in params.items():
				if param_name in allowed_params:
					_params[param_name] = param_value

			# Get function to call
			fn = getattr(schema, function_name)

			# Nasty switch case, but I can't think of a better way to ensure that functions get called
			# with nice-looking args (I don't wish to make everything a kwarg.)
			if http_verb == "GET":
				if route_type == "general":
					args = []
				else:
					args = [id]
			elif http_verb == "POST":
				if route_type == "general":
					args = [data]
				else:
					pass # Invalid
			elif http_verb == "PUT":
				if route_type == "general":
					pass # Invalid
				else:
					args = [id, data]
			elif http_verb == "DELETE":
				if route_type == "general":
					pass # Invalid
				else:
					args = [id]
			
			return fn(*args, **_params)
		
		return self._transfer_function_wrap(transfer_function)
	
	@abstractmethod
	def _transfer_function_wrap(self, transfer_function: 'function') -> 'function':
		"""Wrap the provided function such that:
		
		1. Standard input args and kwargs are provided when it is called.
		2. The output is properly formatted as a string for return.
		3. A RESTException raised during the transfer function's execution will propagate as an HTTP error
		   response.

		Args:
			transfer_function (function): A function that takes the args id, data, params.

		Returns:
			function: A function that, when called, will return a call to the provided transfer function having
				provided the correct arguments on the basis of context.
		"""
		pass