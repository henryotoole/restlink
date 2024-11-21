"""
Copied directly from hacutils (another library of mine) directly into the codebase here so curious minds can see
a way to manage the database session. Also so that I don't have to include hacutils in the imports.

2024
"""
__author__ = "Josh Reed"

# Other libraries
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy.schema import MetaData

# Base python
from contextlib import contextmanager
import os

class Database():
	"""The Database attempts to streamline the use of SQLAlchemy's Session. Sessions are pretty complex, and
	warrant deep understanding (especially if optimization is required).

	However, in many cases the use of the Session is straighforwards: open it, do some things, commit, and close.
	If an exception occurs, create a rollback.

	This database class should be instantiated once in a module and preferably made available to the entire
	module as an 'env' variable (using my own vernacular here). All actions should be done in a session scope
	block:
	```
	db = Database(uri)
	with db.session_scope():
		db.session.do_stuff()
	```
	"""

	def __init__(self, db_uri):
		"""Instantiate a database session/engine pair which can be used consistently to 
		interact with a database.

		Args:
			db_uri (String): the database string like 'mysql+pymysql://root:mysql_password@localhost/dbname'
		"""
		self.engine = create_engine(db_uri)
		# https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.sessionmaker
		# Used so that we can instantiate the session as a var and expose it as a property.
		self.SessionMaker = sessionmaker(self.engine)
		self._session = None

	@property
	def session(self):
		if self._session is None:
			raise ValueError("Cannot use env.db.session outside of a session scope. Place this operation within "+\
				"'with db.session_scope():' block.")
		return self._session

	@property
	def database_name(self):
		"""
		Returns:
			str: The name of the database we are connected to
		"""
		return str(self.engine.url).split("/")[-1]

	@contextmanager
	def session_scope(self):
		"""Create a new session scope. The session itself will be accessible with db.session within this scope.
		All db-operations should be wrapped in this scope.

		If an exception is raised, the session will be rolled back.

		session.commit() should not be called during this scope. flush() should be used, if addition's primary
		keys etc. are needed mid scope.

		Multiple transactions will probably be used under the hood during long session scopes.
		"""
		self._session = self.SessionMaker()

		self._session.begin()
		try:
			# Here we return, to perhaps do a variety of things with the current session.
			yield
			self._session.commit()
		except:
			self._session.rollback()
			raise
		finally:
			self._session.close()
			self._session = None

class DatabaseTesting(Database):
	"""A 'testing' database is just a little convenience wrapping for the classic Database object. It's intended
	to be pointed at a dedicated 'test' database which mirrors the project's real database, whatever that might
	be. It should be given the declarative base model definition used for the module's models - 'Base' below:
	```
	from sqlalchemy.orm import DeclarativeBase
	class Base(DeclarativeBase):
		pass
		
	This is used to infer the table structure and create / drop tables when tests are run.
	```

	It's best to instantiate such a database 
	"""

	def __init__(self, db_uri, decl_base):
		"""Instantiate a connection to the test database. It will be emptied upon instantiation and repopulated
		with the current models in accordance with the provided decl_base.

		Args:
			db_uri (str): The database URI
			decl_base (DeclarativeBaseClassDef): The declarative base used for the module's models.
		"""
		super().__init__(db_uri)

		self.metadata: MetaData = decl_base.metadata
		self.reset_all_tables()

	def drop_all_tables(self):
		"""Drop all tables in this database as known in the decl_base that was provided to
		DatabaseTesting on instantiation.
		"""
		self.metadata.drop_all(bind=self.engine)

	def reset_all_tables(self):
		"""Drop and then create all tables in this database as known in the decl_base that was provided to
		DatabaseTesting on instantiation.
		"""
		self.metadata.drop_all(bind=self.engine)
		self.metadata.create_all(bind=self.engine)

	@contextmanager
	def session_scope(self):
		"""This method differs from base Database method in that it will properly catch and handle integrity
		errors even when using pytest. This is actually a pretty tricky thing to do, and I don't fully understand
		it.

		It appears that, even though except: rollback() is the same here as in Database.session_scope(), it's
		not triggered properly or something if commit() is allowed to be called around the yield statement.

		If we wish to keep permanence with this scope, simply call commit() after adding stuff in your test
		fixture.
		"""
		if self._session is not None:
			raise ValueError("Cannot start a new session scope within another session scope!")
		
		session = self.SessionMaker()
		try:
			self._session = session
			yield session
		except:
			# Note that we don't actually catch exceptions from test functions here, due to the nature of pytest
			session.rollback()
			raise
		finally:
			session.rollback()
			session.close()
			self._session = None

	def teardown(self):
		"""Rollback all changes made to this test database.
		"""
		# Roll back the top level transaction and disconnect from the database
		#self.transaction.rollback()
		#self.connection.close()
		self.engine.dispose()

def mkdirs(fpath, folder=False):
	"""Make all needed directories to fpath. If fpath is intended to be a folder, then folder should be
	set to True to ensure that folder itself is created.

	Args:
		fpath (str): Absolute fileystem path
		folder (bool, optional): If set to True, interpet the endpoint of the provided path as a folder and create
			it. Default False.
	"""
	# If the endpoint is not specified as a folder and is not an existing folder in filesys, shorten the path.
	if (not folder) and (not os.path.isdir(fpath)):
		fpath = os.path.split(fpath)[0]
	# https://stackoverflow.com/questions/273192/how-can-i-safely-create-a-nested-directory
	# While a naive solution may first use os.path.isdir followed by os.makedirs, the solution 
	# above reverses the order of the two operations. In doing so, it prevents a common race 
	# condition having to do with a duplicated attempt at creating the directory, and also disambiguates 
	# files from directories.
	try:
		os.makedirs(fpath)
	except OSError:
		if not os.path.isdir(fpath):
			raise