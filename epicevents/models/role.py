import re
from peewee import *
from .database import BaseModel


class Role(BaseModel):
    """Represents a role in the CRM system (1 admin, 2 management, 3 sales, 4 support)."""
    name = CharField(max_length=50, unique=True)
