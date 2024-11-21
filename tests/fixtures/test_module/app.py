"""
Contains the test module flask application factory

2024
"""
__author__ = "Josh Reed"

# Local code
from restlink import ExposerFlask
from tests.fixtures import get_db

# Other libs
from flask import Flask, has_app_context, request

# Base python
import urllib
import json

# Instantiate plugin singletons that need to be importable from elsewhere.
rest_exposer = ExposerFlask()

def init_app():
	"""This method is a factory that produces the Flask application object. This will:
	1. Create the app.
	2. Apply config from the central config file
	3. Initialize any 'plugins' like RESTLink
	4. Create the app context and within that:
		1. Setup routes
		2. Register blueprings
		3. Return the app
	"""
	if has_app_context():
		raise Exception("make_app is being called when an app context already exists.")

	# 1. Create
	app: Flask = Flask('restlink_test')
	
	# 2. Configure
	configure_app(app)

	# 3. Initialize plugins
	rest_exposer.init_app(app)

	# 4. Context
	with app.app_context():
		# 4.1 Routes

		# 4.2 Blueprints

		# 4.3 Return app
		return app


def configure_app(app: Flask):
	"""Apply config keys to the flask app keys. 

	Args:
		app (Flask): Flask application
	"""
	app.config["TESTING"] = True


@rest_exposer.authenticator
def authenticate_accessor():
	"""Here we authenticate an accessor on a simple basis suitable for testing.
	"""
	accessor = None
	if request.args.get('handshake') == '%22trustworthy%22': # Not bothering to URLDecode here
		accessor = {'etc': 'etc'}
	accessor['extra'] = json.loads(urllib.parse.unquote(request.args.get('extra', '""')))
	return accessor

@rest_exposer.database_session_getter
def db_getter():
	
	return get_db().session