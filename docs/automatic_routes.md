# Automatic Routes

REST is a tremendously capable standard. Only a small subset of possible routes are automatically generated for RESTLink `Schema`'s. These are summarized below in the below table. Note that 'noun' refers to the name of a resource as specified in the `_rest_path_` configuration variable.

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

In order to standardize inputs and outputs, the following conventions are observed by RESTLink:
+ Any data key/value pair conveyed via URL parameter is expected to have its value JSON-stringified and URLEncoded.
+ POST and PUT data is expected to be in the body of the request in JSON form.
+ Any data returned as part of a request will be in JSON form.