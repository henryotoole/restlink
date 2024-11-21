"""
Test fixtures module file

2024
"""
__author__ = "Josh Reed"

# Local code

# Other libs

# Base python


# Here is some state management for accessing a database singleton.
_state = {
	'db': "WILL_BE_SET_BY_FIXTURE"
}
def get_db():
	return _state['db']