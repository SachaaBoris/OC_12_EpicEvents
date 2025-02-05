import re
from peewee import *
from .database import BaseModel


class Role(BaseModel):
    """Represents a role in the CRM system (Admin, Sales, Support)."""
    name = CharField(max_length=50, unique=True)
