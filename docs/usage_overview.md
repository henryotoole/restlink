# Usage Overview

## Outside Services

In order to demonstrate the components of RESTLink, we will need to setup some external services. For starters, a backend framework is needed that can expose routes to the internet. For this guide, we will be using Flask. The factory method of flask app instantiation is generally preferable, as indicated below:

```python
from flask import Flask

def init_app():
	"""Application factory method that returns the Flask app within the app context.
	"""
	# Instantiate the app
	app: Flask = Flask('restlink_test')

	# Initialize extensions
	# - We will add more here later.

	# Create context
	with app.app_context():
		return app
```

The app can, of course, be launched in development mode with:

```python
app = init_app()
app.run(debug=True)
```

We will also need a functioning database connection. RESTLink's built-in functions use SQLAlchemy, and as we are already using Flask we may as well use the flask-sqlalchemy extension. Note that any means of reaching the database is possible - all that RESTLink will need is a valid `Session` instance. More on that later.

The flask-sqlalchemy extension can be registered with:

```python

from flask_sqlalchemy import SQLAlchemy

db_flask = SQLAlchemy()
```

And the extension should registered within the `init_app()` factory. See the updated function below. Note that in the interest of brevity I am directly injecting the database URI into the app's config. This is bad practice, and a proper config toolchain should be used in production.

```python
def init_app():
	"""Application factory method that returns the Flask app within the app context.
	"""
	# Instantiate the app
	app: Flask = Flask('restlink_test')

	# Initialize extensions
	app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///./test.db"
	db_flask.init_app(app)

	# Create context
	with app.app_context():
		# These two lines delete and re-add all tables whenever the flask application starts.
		# This ensures that tables exist and are fresh for a test run of the app. They'd be taken out
		# in any real project.
		Base.metadata.drop_all(bind=db_flask.engine)
		Base.metadata.create_all(bind=db_flask.engine)
		return app
```

Of course, to use a database we'll need a basic table. A very basic model is defined below:

```python

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

```

## The Exposer Singleton

Now that the boundaries are established, the two can be established with RESTLink. The first step is to instantiate the `Exposer` singleton or, more specifically, the relevant `Exposer` child class, like `ExposerFlask`. The `Exposer` instance will be the focal point of RESTLink - Schema's and API's are registered against it and it holds references to authentication and backing service fetch methods.

```python
from restlink import ExposerFlask

rest_exposer = ExposerFlask()
```

The `Exposer` instance will need a reference to the flask application, of course. The `ExposerFlask` singleton takes the usual form of a flask extension, and should be linked just like flask-sqlalchemy in the application factory:

```python
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
		return app
```

The `Exposer` singleton will need a couple extra functions bound to it to enable full automation. For now, the only one we need to concern ourselves with is the `database_session_getter` decorator. This decorator wraps a function that returns an SQLAlchemy `Session` instance which can be used to read and write to the database.

There will always be a flask request context when RESTLink is accessing the database, so for this example it's fine to simply return the flask-sqlalchemy session instance. Context is managed by the library.

```python
@rest_exposer.database_session_getter
def db_getter():
	return db_flask.session
```

## The Schema

The Schema class lets you mark a database model for exposure via REST API. It also provides mechanisms for input validation, selective field exposure, and serialization. Most of this is achieved with Marshmallow's native behavior. All the `Schema` classes provided by RESTLink extend the base Marshmallow `Schema`.

Currently RESTLink only features one complete implementation for relational database tables: `SchemaDB`. However, implementing a custom `Schema` child class is only a matter of overwriting a handful of abstract methods.

Every model / database table that shall be exposed with RESTLink will need its own `Schema` child class. Below one is implemented for the `ModelBasic` table above:

```python
from restlink import SchemaDB
from marshmallow import fields, validate, post_load

class SchemaBasic(SchemaDB):
	
	_db_model_ = ModelBasic
	_rest_path_ = "/basic"

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
```

Let's take a look at each piece.

The very first few lines are those odd-looking single-underscore class variables. These represent configuration that effects the schema in general. Some configuration options are optional, and others must be provided or an exception will be raised when RESTLink sets itself up.

Here, most critically, a database model that corresponds to this Schema is specified. Then, the rest path for this specific resource is defined. This path determines the 'name' of this resource as it will appear in the outside world in URLs.

```python
_db_model_ = ModelBasic
_rest_path_ = "/basic"
```

Next we have fields. Fields represent model variables. This is default Marshmallow syntax and behavior. Here, the `id` column is set to `dump_only`, which means that this field can not be altered by REST API calls. The `val` column is simply an integer with no validation at all. Many kinds of field exist and validation for field data is  extensive; consult the [Marshmallow documentation](https://marshmallow.readthedocs.io/en/stable/) for more details.

```python
id = fields.Int(strict=True, dump_only=True)
val = fields.Integer()
```

Another Marshmallow feature used here is the `@post_load` decorated function `make_basic()`. This function is automatically called by RESTLink when the REST API is used to create a new record. In this case, it is responsible for making a new database record and adding it to the database. Note that it references the `rest_exposer` singleton to get the database session. 

```python
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
```

Finally, two methods appear that have absolutely nothing to do with base Marshmallow behavior. These are the `validate_can_read()` and `validate_can_write()` functions:

```python
def validate_can_read(self, id) -> bool:
	return True
	
def validate_can_write(self, id) -> bool:
	return True
```

For this simple example, complete public read and write access is enabled for this resource by setting both of these to simply return True. However, in most real cases data for a resource and schema will have access that is selective and governed by some form of permissions. These two methods allow arbitrary, complex behavior in those cases. See the documentation for "Authentication and Validation" for more details.

## The API

The final piece needed to assemble RESTLink is the `API`. This class represents a conceptual subset of all possible resources on a server. This subset is distinguished both by name and by version and all routes for a given API are downstream of a unique combination of that name and version. Every schema will be attached to at least one API instance.

Creating a new API is very simple. Merely instantiate the `API` class with a programmatic name, a version string, and a human-readable name.

```python
from restlink import API

api = API('test', 'v1', "Test API")
```

The URL for an API will take the form: `/{base_path}/{api.name}/{api.version}/...`. The `base_path` is an optional base URL that can be given to the `Exposer` on instantiation, and in default will simply be omitted.

## Putting It All Together

Once all setup is complete, assembling the pieces is almost trivial. Simply call `exposer.register_schema` with an instance of each `Schema`.

```python
schema = SchemaBasic()
rest_exposer.register_schema(api, schema)
```

When the above is executed, the 'basic' resource we have created will be exposed at `/test/v1/basic`. Complete CRUD (create/read/update/delete) capability is exposed. If we launch the app in development mode with:

```python
app = init_app()
app.run(debug=True)
```

then it is possible to test our basic little API with curl.

```bash
$ curl -X GET localhost:5000/test/v1/basic
[]

$ curl -X POST --data '{"val":3}' -H "Content-Type: application/json" localhost:5000/test/v1/basic
{
  "id": 1,
  "val": 3
}

$ curl -X GET localhost:5000/test/v1/basic
[
  1
]

$ curl -X GET localhost:5000/test/v1/basic/1
{
  "id": 1,
  "val": 3
}
```

## Documentation

Documentation in adherence with OpenAPI standards is generated automatically when a `Schema` is added to the exposer. Each `API` gets its own set of documentation including all associated `Schema`'s that can be viewed in JSON form at `/{base_path}/{api.name}/{api.version}/docs`