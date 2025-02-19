import re
from peewee import *
from .database import BaseModel


class Permission(BaseModel):
    """Represents a CRLUD permission (create, read, list, update, delete)."""
    name = CharField(max_length=50, unique=True)
