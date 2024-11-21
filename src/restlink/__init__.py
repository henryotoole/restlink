"""
This is `restlink`.

This code aims to complete the critical last leg of automation between Marshmallow schema's, SQL alchemy, and
a REST API exposed on Flask and adhering to OpenAPI. This task is somewhat conditional and I suspect that
any attempt to do it truly universally will result in frustration. This small library is my own take on this
problem and tailored to my own needs. Perhaps some other person with similar needs might use it one day.

The structure here is based fundamentally around the Schema class from marshmallow. By default marshmallow
operates by providing a `Schema` class which is extended to define more complex datastructures. Restlink takes
this concept and extends it by providing a handful of different `SchemaX` classes. Each of these extensions
provides a different sort of additional functionality. `SchemaDB`, for example, connects a child class
implementation to a database.

On the other side, the `Exposer` class exposes a set of `Schema`'s to the internet. This is potentially
framework-agnostic; however I have only bothered to write an implementation for Flask so far. In the flask
case, all routes needed to expose the provided `Schema`'s to the internet are created automatically and adhere
to OpenAPI standards. Further writing on the `Exposure` will assume flask (until such point as I write an
alternative implementation).

The general connection 

Everything that's *worth testing* should be downstream of the WhateverSchema class. Upstream functionality
should really just be minimum-possible boilerplate and docstrings for Swagger.

Graphically, the flow of execution is as follows:

```
.. highlight:: python
.. code-block:: text

#TODO update this once finished with bulk code.

#                                 +--( SchemaRFS )--------> File System
#                                 |                         + Upload and download
#                                 |                         
#                                 |                         
# pytest -------------> Schema ---+--( SchemaRSA )--------> SQLAlchemy Model
#                     ^  + Creates DAO behavior             + cognatio/core
#                     |  + Marshmallow for serialization    + DB Access
#                     |  + Marshmallow for validation       
#                     |  + Does not use flask app context   
#                     |  + **Validates** user
# REST API -> Flask  -/
#             Routes
#             + Setup by Exposer class execution.
#             + Uses flask app context
#             + **Authenticates** user
			
```
2024
"""
__author__ = "Josh Reed"

from restlink.exceptions import RESTException
from restlink.api import API
from restlink.schema import SchemaREST
from restlink.schema_db import SchemaDB
from restlink.exposer_flask import ExposerFlask
from restlink.exposer import Exposer