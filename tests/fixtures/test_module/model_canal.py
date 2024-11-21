"""
Test model to represent a canal.
"""
__author__ = "Josh Reed"

# Local code
from tests.fixtures.test_module import Base

# Other libs
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer

# Base python

class Canal(Base):

	__tablename__ = "canal"

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	width: Mapped[int] = mapped_column(Integer)
	name: Mapped[str] = mapped_column(String(32))
	read_only: Mapped[int] = mapped_column(Integer)
	internal_only: Mapped[str] = mapped_column(String(16))

	def __init__(self, width, name):
		self.width = width
		self.name = name
		self.read_only = 5
		self.internal_only = "secret"