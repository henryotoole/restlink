# Schemas

The `Schema` is explained in general in the `Usage Overview` document. This guide provides information of a little more depth.

## Marshmallow Notation Quirks

Marshmallow has (for good reasons, I expect) a very specific vocabulary it uses to describe data fields. Some of these words are a bit confusing when used within the context of a REST API.

### Read-Only Fields

Very often, a field will need to be visible to the API but read-only. In Marshmallow parlance, `dump_only` is used to indicate this behavior to a field.

```python
id = fields.Int(strict=True, dump_only=True)
```

### Non-Accessible Fields

Sometimes a field should be completely obscure from the REST API. For example, no request should return the password hash for a User database entry. This is achieved when the `Schema` is instantiated rather than in the class definition. Below is an example of a UserSchema from another one of my projects.

```python

class UserSchema(SchemaRSA):

	__db_model__ = User
	__rest_path__ = "/user"
	__allowed_methods__ = ["GET"]

	id = fields.Int(strict=True, dump_only=True)
	email = fields.Email()
	passhash = fields.String(dump_only=True)
	# The password is a temporary variable only used during create
	password = fields.String(load_only=True)

	@post_load
	def make_user(self, data: dict, **kwargs) -> User:
		"""Make a new user with json data which will be validated. This will create a new database record.

		Args:
			data (dict): request data. Should contain email and password.

		Returns:
			User: New user, instantiated from data. Will include ID.
		""" 
		rec = User(data['email'], data['password'])
		env.db.session.add(rec)
		env.db.session.flush()
		return rec
```

The passhash is excluded specifically when the `Schema` is instantiated:

```python
user_schema = SchemaUser(exclude='passhash')
```

### Instantiation-Only Fields

When a field is only ever to be used during instantiation, give it the `load_only` kwarg.

```python
password = fields.String(load_only=True)
```