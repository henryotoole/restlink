"""
Holds an implementation of a `SchemaREST` that represents a record from a database table.

2024
"""
__author__ = "Josh Reed"

# Local code
from restlink.schema import SchemaREST
from restlink.exceptions import RESTException

# Other libs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy import select

# Base python

class SchemaDB(SchemaREST):
	"""The `SchemaDB` schema provides `_action()` methods that allow a schema to automatically push and pull
	from a database table. SQLAlchemy is used to achieve this.

	Even if access to the table is basic and no default methods need to be changed to allow interaction with
	the table, end-use code child classes of this Schema will need to implement the `validate_can_read()` and
	`validate_can_write()` methods (unless the default read-only public access is desired). The implementation
	will also need to create a load() method (which is a basic Marshmallow feature).

	Use of the automatic get/create/update/delete functions contained within this schema will also require
	the Exposer singleton to be assigned a database session getter function. See `Exposer.
	"""

	_db_model_ = None
	"""The database model class definition (e.g. UserModel) should be placed here by child Schema class
	"""
	_field_db_remap_ = {}
	"""A map of field names to db column names, for use when they are not identical (for example, when using
	getter/setters).
	"""

	def record_get_from_db(self, id: int) -> DeclarativeBase:
		"""Method used by update(), get(), and delete() to actually retrieve the db record needed to perform
		actions on. If there is a peculiarity with getting this model by ID, this is the method to alter.

		Args:
			id (int): The ID of the record

		Returns:
			DeclarativeBase: Record instance or None if there's not one of that ID
		"""
		if self.__class__._db_model_ is None:
			raise Exception(f"_db_model_ was not declared for {self.__class__.__name__}")
		return self.exposer.database_session.get(self.__class__._db_model_, id)

	def _get(self, id: int, **kwargs) -> dict:
		"""Performs the default get operation. This simply checks the data table for this schema for a record that
		matches the provided ID and returns serialized data that is appropriate for the frontend in accordance
		with this schema's filtering and dump-only properties.

		This method, rather than get(), should be extended if more complex behavior is demanded by a child schema.

		Args:
			id (int): An integer ID

		Returns:
			dict: 'serialized' data of this Schema
		"""
		rec = self.record_get_from_db(id)
		if rec is None:
			raise RESTException(
				404,
				f"{self.name} ID={id} does not exist."
			)
		return self.dump(rec)
	
	def _create(self, data: dict, **kwargs) -> dict:
		"""Perform the default create operation. This will leverage the @post_load method, which must be defined
		in the child schema as creating a new instance of anything (but especially a database record) is
		often unique.

		This will, presumably, create a new database record. Flush will be called and autoincr ID included.

		Args:
			data (dict): The data that came along with the request

		Returns:
			dict: 'serialized' data of the new record
		"""
		record = self.load(data)
		return self.dump(record)
	
	def _update(self, id: int, data: dict, **kwargs) -> dict:
		"""Basic REST UPDATE operation. By default, any key/value pair in the provided 'data' dict will be
		applied to database record instance with setattr(). Validation will be performed in accordance with
		this schema's configuration beforehand.

		Some update behavior is pretty custom, and this REST function will likely need to be overwritten
		on occasion.

		Keep in mind that advanced update behavior may be more cleanly handled, in some cases, by using
		a getter/setter pair in the sqlalchemy model class.

		Args:
			id (int): An integer ID of the record to update
			data (dict): The data that came along with the request

		Returns:
			dict: 'serialized' data of the record after update
		"""
		# Ensure record exists
		rec = self.record_get_from_db(id)
		if rec is None:
			raise RESTException(
				404,
				f"{self.name} ID={id} does not exist."
			)

		# Validate supplied data
		self.validate(data)
		
		# Apply key/value pairs as attributes.
		for k, v in data.items():
			setattr(rec, k, v)

		self.exposer.database_session.commit()

		return self.dump(rec)
	
	def _delete(self, id: int, **kwargs):
		"""Delete a record by its ID. By default, this simply calls db.session.delete() on the record.

		Args:
			id (int): An integer ID of the record to delete
		"""
		# Ensure record exists
		rec = self.record_get_from_db(id)
		if rec is None:
			raise RESTException(
				404,
				f"{self.name} ID={id} does not exist."
			)

		self.exposer.database_session.delete(rec)
		self.exposer.database_session.commit()

	def _list(self, filter=None, **kwargs):
		"""Actually perform get list operation post-validation.

		Args:
			filter (dict, optional): Key/value data which is used to filter the returned ID.

		Returns:
			list: Of integer ID's.
		"""
		Model = self.__class__._db_model_
		field_db_remap = self.__class__._field_db_remap_
		if Model is None:
			raise Exception(f"_db_model_ was not declared for {self.__class__.__name__}")
		
		pk_cols = list(Model.__table__.primary_key)
		if len(pk_cols) > 1:
			raise NotImplementedError("No implementation for composite primary keys.")
		pk_col_name = pk_cols[0].name
		
		stmt = select(getattr(Model, pk_col_name))

		# Add WHERE statements for every filter param.
		if(filter is not None):
			for filter_k, filter_v in filter.items():
				# Remap is a poor way to solve this problem, but direct and simple.
				if filter_k in field_db_remap:
					filter_k = field_db_remap[filter_k]
					
				if not hasattr(Model, filter_k):
					raise RESTException(
						400,
						f"Can not filter by '{filter_k}' on {self.name} - no such field."
					)
				if not isinstance(getattr(Model, filter_k), InstrumentedAttribute):
					# It is not possible to evaluate the property without getting an instance of the model.
					raise RESTException(
						400,
						f"Can not filter by '{filter_k}' on {self.name}'s table. Double check that the " +
						f"is not using a getter for that property. If so, use _field_db_remap_.",
					)
				if filter_k in self.exclude:
					raise RESTException(
						401,
						f"Can not filter by excluded property '{filter_k}' on {self.name}"
					)
				stmt = stmt.where(
					getattr(Model, filter_k) == filter_v
				)

		exist = self.exposer.database_session.execute(stmt).all()
		ids = [x[0] for x in exist]
		return ids
	