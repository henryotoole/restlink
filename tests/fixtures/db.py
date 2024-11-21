"""
Database fixtures.

2024
"""
__author__ = "Josh Reed"

# Local code
from tests.fixtures.test_module import Base
from tests.fixtures.util import DatabaseTesting, mkdirs
from tests.fixtures import _state

# Other libs
import pytest
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer

# Base python
import os


@pytest.fixture(scope="session")
def db_sqlite_test(fpath_dev):
	path = os.path.join(fpath_dev, "db_test.db")
	mkdirs(path)
	return "sqlite:///" + path

@pytest.fixture(scope="session")
def test_db_module(db_sqlite_test):
	"""Create a test database which will hook up to an sql database
	"""

	tdbw = DatabaseTesting(db_sqlite_test, Base)
	
	yield tdbw

	tdbw.teardown()

@pytest.fixture
def test_db(test_db_module: DatabaseTesting):
	"""This doesn't really create the test database, rather it takes the module-wide one and sets
	it up for one test run. Less overhead. We will ensure all tables are empty each time we open a session,
	just in case something was committed during a previous test. Things added with flush() will never persist,
	but production code sometimes makes use of commit().
	"""

	# Check that the persistent var has been cleared.
	if _state['db'] != "WILL_BE_SET_BY_FIXTURE":
		raise ValueError("Persistent database variable has not been cleared properly after test!")

	with test_db_module.session_scope():
		

		test_db_module.session.flush()
		_state['db'] = test_db_module
		yield test_db_module
		_state['db'] = "WILL_BE_SET_BY_FIXTURE"

	# Always clean up lingering records afterwards.
	with test_db_module.session_scope():

		test_db_module.reset_all_tables()
		test_db_module.session.commit()

class Simple(Base):

	__tablename__ = "simple"

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	field_a: Mapped[int] = mapped_column(Integer)
	field_b: Mapped[str] = mapped_column(String(16))

	def __init__(self, field_a, field_b):
		self.field_a = field_a
		self.field_b = field_b