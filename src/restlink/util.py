"""
Contains stateless utility functions used by restlink.

2024
"""
__author__ = "Josh Reed"

# Local code

# Other libs

# Base python

def python_type_to_openapi_type_string(python_type) -> str:
	"""Convert a python type to an openAPI string.

	Args:
		python_type (type): A python type, like str, list, or int

	Returns:
		str: The OpenAPI-compatible type designator string
	"""
	mapping = {
		'list': list,
		'integer': int,
		'string': str
	}
	for k, vt in mapping:
		if vt == python_type:
			return k
		
	raise ValueError(f"Python type {python_type} not in mapping.")