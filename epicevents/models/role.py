import re
from peewee import *
from .database import BaseModel


class Role(BaseModel):
    """Represents a role in the CRM system (1 Admin, 2 Sales, 3 Support)."""
    name = CharField(max_length=50, unique=True)