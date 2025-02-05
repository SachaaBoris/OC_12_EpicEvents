import re
from peewee import *
from .database import BaseModel


class Permission(BaseModel):
    """Represents a CRUD permission (create, read, update, delete)."""
    name = CharField(max_length=50, unique=True)