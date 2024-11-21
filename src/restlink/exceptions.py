"""
Contains exceptions for internal use..

2024
"""
__author__ = "Josh Reed"

# Local code

# Other libs

# Base python


class RESTException(Exception):
	"""This is a general use exception that's used similarly to Flask's HTTPException. When raised, it cuts
	all the way up the stack to the `transfer_function()` that handles the REST request. Then the exception
	can be translated into the proper response for the route (which might indeed be a Flask HTTPException)
	"""

	def __init__(self, http_code: int, message: str):
		"""Instantiate a new rest exception, providing the HTTP code to respond with and a message that
		explains what went wrong.

		Args:
			http_code (int): HTTP Code like 200, 404, etc.
			message (str): Message that will be included in the response.
		"""
		self.http_code = http_code
		self.message = message