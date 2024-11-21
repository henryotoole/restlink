"""
Contains fixtures related a little test flask server that runs on localhost.

2024
"""
__author__ = "Josh Reed"

# Local code
from tests.fixtures.test_module import init_app

# Other libs
import pytest

# Base python



@pytest.fixture
def test_client():
	app = init_app()

	with app.test_client() as client:
		yield client
