# Authentication and Validation

There are two places where you will need to write some code to deal with accessor identity and whether an accessor has access to a resource.

## Authentication

The first is authentication. This step authenticates the identity of an accessor that is attempting to use the API. There are a great many ways authentication can be done, and all of them are beyond the scope of RESTLink's operations. Instead, RESTLink provides a decorator (`Exposer.authenticator`) that is used to specify some arbitrary set of code that uses request context to determine the identity of an accessor.

```python
@rest_exposer.authenticator
def auth_fn():
	# Should return an object that represents the identity of the accessor or None, if credentials are lacking.
```

Any sort of object can be returning from this function. RESTLink will merely pass it onwards to the validation step. A very straightforwards example of an authenticator function leverages the flask-login module:

```python
from flask_login import LoginManager
from flask_login import current_user

login_manager = LoginManager()

# ... login_manager will have to have it's init_app() function called etc...

@rest_exposer.authenticator
def auth_fn():
	# Only returns the current_user object if not anonymous.
	if current_user is None: return None
	if current_user.is_anonymous: return None
	return current_user
```

## Validation

Once authenticated, an accessor may have access to some resources but not others. Validation of an accessor's access to a specific resource is handled by two functions that are overridden in `Schema` implementations. A snippet of the `SchemaBasic` class from an earlier document is shown below. The one of the two validation methods is called for every single request against this resource. If a validation method returns True, access is allowed. Otherwise, a 403 error is returned.

```python
from restlink import SchemaDB

class SchemaBasic(SchemaDB):
	
	# ...
	# ...
	# ...
		
	def validate_can_read(self, id) -> bool:
		"""Controls access to GET operations.
		"""
		return True
	
	def validate_can_write(self, id) -> bool:
		"""Controls access to POST, PUT, and DELETE operations.
		"""
		return True
```

The `SchemaBasic` example provides public read and write access. However, if the `Exposer` has had an authenticator assigned, that identity can be used to selectively provide access. For example, the following validator would only grant write access to a user with an ID of 2.

```python
def validate_can_write(self, id) -> bool:
	"""Controls access to POST, PUT, and DELETE operations.
	"""
	return rest_exposer.current_accessor.id == 2
```

Or, as is common, if the following conditions are true:
+ The accessor is an instance of a `User` model
+ A junction table relates users to a resource

Then something like the following could be written:

```python
def validate_can_write(self, id) -> bool:
	"""Controls access to POST, PUT, and DELETE operations.
	"""
	jcn_rec = rest_exposer.database_session.execute(
		select(UserResourceJunctionTable).filter_by(
			user_id=rest_exposer.current_accessor.id,
			resource_id=id
		)
	).first()
	return jcn_rec is not None
```