"""
Tests to ensure the documentation code snippets actually execute.

2024
"""
__author__ = "Josh Reed"

# Local code

# Other libs

# Base python



def test_quickstart():
	"""Test that the quickstart code snippet actually launches.
	"""

	## Outside Services - flask
	from flask import Flask

	def init_app():
		"""Application factory method that returns the Flask app within the app context.
		"""
		# Instantiate the app
		app: Flask = Flask('restlink_test')

		# Initialize extensions
		app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///./test.db"
		db_flask.init_app(app)
		rest_exposer.init_app(app)

		# Create context
		with app.app_context():

			Base.metadata.drop_all(bind=db_flask.engine)
			Base.metadata.create_all(bind=db_flask.engine)
			return app
		
	## Outside Services - database
	from flask_sqlalchemy import SQLAlchemy

	db_flask = SQLAlchemy()

	## Outside Services - model

	from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
	from sqlalchemy import Integer

	class Base(DeclarativeBase):
		pass

	class ModelBasic(Base):

		__tablename__ = "basic"

		id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
		val: Mapped[int] = mapped_column(Integer)

		def __init__(self, val):
			self.val = val

	## The Exposer Singleton

	from restlink import ExposerFlask

	rest_exposer = ExposerFlask()

	@rest_exposer.database_session_getter
	def db_getter():
		return db_flask.session

	## The Schema

	from restlink import SchemaDB
	from marshmallow import fields, validate, post_load

	class SchemaBasic(SchemaDB):
		
		_db_model_ = ModelBasic
		_rest_path_ = "/basic"
		_allowed_methods_ = ["GET", "POST", "PUT", "DELETE"]

		id = fields.Int(strict=True, dump_only=True)
		val = fields.Integer()

		@post_load
		def make_basic(self, data: dict, **kwargs):
			"""Create a new database record for this schema.

			Args:
				data (dict): request data

			Returns:
				ModelBasic: New database record, added to database.
			"""
			rec = ModelBasic(data['val'])
			rest_exposer.database_session.add(rec)
			rest_exposer.database_session.commit()
			return rec
		
			
		def validate_can_read(self, id) -> bool:
			return True
		
		def validate_can_write(self, id) -> bool:
			return True
		
	## The API
	from restlink import API

	api = API('test', 'v1', "Test API")

	## Putting It All Together
	schema = SchemaBasic()
	rest_exposer.register_schema(api, schema)

	# Can uncomment these to actually run this and check curl commands
	#app = init_app()
	#app.run(debug=True)