"""
API base class. The API represents a set of Schema's of a certain version. Each API has its own documentation.

2024
"""
__author__ = "Josh Reed"

# Local code
from restlink.schema import SchemaREST
from restlink.util import python_type_to_openapi_type_string

# Other libs
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

# Base python
import os
import json
from contextlib import contextmanager

class API:
	"""The API instance represents a conceptual set of Schema's that are all operating under the same
	'version'. Every instance will have it's own unique documentation spec.

	This class provides both:
	
	1. Internal methods that are used to automatically setup the documentation for restlink schemas and paths
	2. External-facing methods that allow interaction with the documentation for any more complex resources
	   that are added to an API manually (e.g. by defining a bunch of flask routes or something.)
	"""

	def __init__(self, name: str, version: str, title_readable: str, ):
		"""Instantiate a new conceptual API space. Every API must have at least a title and a version. These
		are used (along with the base path set by the Exposer) to compute the overall base path for this
		API's schema's in particular.

		Args:
			name (str): The name (or namespace) of this API for use by the machinery. It will also be used
				to construct this API's URLs.
			version (str): The version of the API. Beware that it is used in the API's URLs, and should not
				contain invalid characters like spaces.
			title_readable (str): A human readable title, used only for viewing purposes.
		"""
		self.title_readable = title_readable
		self.version = version
		self.name = name
		"""The name (or namespace) of this API for use by the machinery. It is used to construct this API's URLs.
		"""

		self._apis = []
		"""All API's that have yet been registered with this Exposer.
		"""

		# Callbacks which are created when certain methods of this class are used as decorators.
		self._authenticator_fn = None
		"""Callback for authenticating an accessor to the API.
		"""

		# Add in our APISpec
		self._spec = APISpec(
			title=self.title_readable,
			version=version,
			openapi_version="3.1.0",
			plugins=[MarshmallowPlugin()]
		)

		self._doc_view_fn = None

	@property
	def key(self) -> str:
		"""Returns:
			str: Unique string based on this API's name and version
		"""
		return f"{self.name}_{self.version}"

	@property
	def doc_view_fn(self) -> 'function':
		"""Returns:
			function: A function that returns the spec object (as a dict)
		"""
		return self._doc_view_fn
	
	@contextmanager
	def doc_api_spec(self) -> APISpec:
		"""This context-managed function is the correct way to interact with the api spec from outside of
		this class. The spec should be modified in a `with` block so that when the context closes the
		class can be sure to update the hosted documentation from the new instruction set.

		Yields:
			APISpec: The active instance of the specification for this API.
		"""
		yield self._spec
		self.docs_regen()

	def docs_regen(self):
		"""Regenerate the documentation view function to reflect the current state of this API.
		"""
		self._doc_json_copy = json.loads(json.dumps(self._spec.to_dict()))
		def fn(*args, **kwargs):
			return self._doc_json_copy
		self._doc_view_fn = fn

	def doc_set_servers(self, base_path: str=None):
		"""Set the servers block for this API. The servers block defines all possible 'root' paths for
		an API. This might include a production and test version of the API. Multiple url's are possible
		per server, as well, if http and https are to be exposed.

		https://swagger.io/docs/specification/v3_0/api-host-and-base-path/

		In restlink, the server block is kept very simple. There's one server url.

		Args:
			base_path (str, optional): An optional base path. All resulting api paths will be downstream if it.
				Treated the same regardless of presence of leading slash.
		"""
		path_root = self.path_root_get(base_path=base_path)

		# Currently doing the lazy thing and using a relative URL. I think this is OK.
		# https://swagger.io/docs/specification/v3_0/api-host-and-base-path/
		self._spec.options['servers'] = [
			{
				"url": path_root
			}
		]

		self.docs_regen()

	def doc_add_schema(self, schema: SchemaREST):
		"""Add a schema to this API's documentation generator.

		Args:
			schema (SchemaREST): The schema to add
		"""
		self._spec.components.schema(schema.name, schema=schema)

		self._doc_add_schema_paths(schema)

		self.docs_regen()

	def _doc_add_schema_paths(self, schema: SchemaREST):
		"""The path descriptor does some heavy lifting for the API spec. There's much complexity; the goal
		of restlink is to abstract away such complexities.

		A call on this method will add path documentation for each route made available by the schema's
		configuration.

		This is a pretty decent overview of OpenAPI's paths.
		https://swagger.io/docs/specification/v3_0/paths-and-operations/

		The APISpec's path() function is best understood by reading the source code.

		Args:
			schema (SchemaREST): The schema instance to add paths for.
		"""
		paths = {}

		for http_verb, route_type, function_name, allowed_params in schema.exposed_methods:
			method_data = schema.method_get(http_verb, route_type)

			# Determine path: relative url to resource.
			url_rel = self.path_resource_get("", schema)
			if route_type == "general":
				url_route = url_rel
			else:
				url_route = url_rel + "/{id}"

			if not url_route in paths:
				paths[url_route] = {}

			# Determine parameters.
			parameters = schema.doc_get_operation_params(http_verb, route_type)

			# Determine requestBody
			request_body = schema.doc_get_operation_request_body(http_verb, route_type)

			# Determine response type
			responses = schema.doc_get_operation_response(http_verb, route_type)

			paths[url_route][http_verb.lower()] = {
				'parameters': parameters,
				'responses': responses
			}
			if request_body is not None:
				paths[url_route][http_verb.lower()]['requestBody'] = request_body

		for url_route, operations in paths.items():
			self._spec.path(
				path=url_route,
				operations=operations
			)

	def path_root_get(self, base_path: str=None) -> str:
		"""Get the absolute 'root' path for this API. All schema resource paths are downstream of it.
		It is computed as follows:

		`/{base_path}/{name}/{version}`

		Args:
			base_path (str, optional): An optional base path. All resulting api paths will be downstream if it.
				Treated the same regardless of presence of leading slash.

		Returns:
			str: Absolute 'root' path for this API.
		"""
		if base_path is None:
			return os.path.join("/", self.name, self.version)
		else:
			return os.path.join("/", base_path, self.name, self.version)
		
	def path_resource_get(self, path_root: str, schema: SchemaREST):
		"""Get the absolute path to the provided schema resource.
		It is computed as follows:

		`/{base_path}/{api.name}/{api.version}/{schema.name}`

		Args:
			path_root (str): The root path for this API (e.g. the result of `path_root_get()`)
			schema (SchemaREST): The schema that defines the resource

		Returns:
			str: Absolute 'resource' path for this API and Schema
		"""
		return os.path.join(path_root, schema.name)
	
	def path_get_docs(self, path_root: str):
		"""Get the absolute path at which documentation is hosted for this API.
		It is computed as follows:

		`/{base_path}/{api.name}/{api.version}/docs`

		Args:
			path_root (str): The root path for this API (e.g. the result of `path_root_get()`)
		"""
		return os.path.join(path_root, 'docs')
	
	def __str__(self) -> str:
		return self.__repr__()
	
	def __repr__(self) -> str:
		"""Returns:
			str: of form <API {name} {version}>
		"""
		return f"<API {self.name} {self.version}>"