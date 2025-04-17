"""
Subclass of exposer for use with Flask projects.

2024
"""
__author__ = "Josh Reed"

# Local code
from restlink.api import API
from restlink.exposer import Exposer
from restlink.exceptions import RESTException

# Other libs
from flask import Flask, request, jsonify
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

# Base python
import json
import urllib.parse

class ExposerFlask(Exposer):
	"""The ExposerFlask class follows the usual pattern of flask extensions. It can be immediately instantiated
	or lazy loaded with init_app(). Otherwise, it behaves much like the original Exposer class and merely
	overwrites a few methods in order to work with flask.
	"""

	def __init__(self, app=None, **kwargs):
		"""Instantiate the Exposer class. This should only be done once - the result is a singleton.

		The flask app can be provided at time of instantiation or later with `init_app()`, as is customary
		with flask extensions.
		"""
		super().__init__(**kwargs)

		self._url_rule_queue = []
		"""A queue of URL rule tuples that have not yet been added to flask because the app was not initialized
		yet.
		"""
		self._flask_app: Flask = None
		"""Reference to the flask application singleton that might not exist yet.
		"""
		
		if app is not None:
			self.init_app(app)

	def init_app(self, app: Flask):
		"""Initialize the exposer instance with the core flask application object. This gives the Exposer
		singleton access to the flask app and binds the exposer to the application object as 'restlink_exposer'

		Args:
			app (Flask): Flask application instance
		"""
		self._flask_app = app

		self._flask_app.restlink_exposer = self

		# Add any deferred URL rules.
		for rule, endpoint, transfer_function, http_verb in self._url_rule_queue:
			self._flask_app.add_url_rule(rule, endpoint, transfer_function, methods=[http_verb])

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
		# If the flask app is known, call _route_create(). Otherwise, add it to the 'deferred' stack
		# to have routes created whenever init_app() is called
		if self._flask_app is None:
			self._url_rule_queue.append((rule, endpoint, transfer_function, http_verb))
		else:
			self._flask_app.add_url_rule(rule, endpoint, transfer_function, methods=[http_verb])

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
		# The 'id' is optionally provided by the <string:id> url rule matcher. Whether it is used depends on
		# the route, but it's the only direct argument to this function so having it as a kwarg here will catch
		# it either way.
		def wrapped(id=None): 

			try:
				params = {}
				for param_name in request.values.keys():

					param_val = json.loads(urllib.parse.unquote(request.values[param_name]))
					params[param_name] = param_val


				data = request.get_json(silent=True)
				
				#print(f"URL: {request.url} Data: {data} Params: {params}")
				return jsonify(transfer_function(id, data, params))
			except RESTException as exc:
				# Translate rest exception into flask HTTPException
				return jsonify({'error': exc.message}), exc.http_code

		return wrapped