"""
Test configuration file for all tests for restlink.

2024
"""
__author__ = "Josh Reed"

# Local code
from restlink import api
from tests import test_api
from tests.fixtures.util import mkdirs

# Other libs
import pytest

# Base python
import os
import pathlib

@pytest.fixture(scope="session")
def fpath_dev() -> str:
	"""Fixture that returns the absolute filepath to the 'dev' directory.
	"""
	
	fpath = os.path.join(pathlib.Path(__file__).parent.parent.resolve(), "dev")
	mkdirs(fpath, folder=True)
	return fpath