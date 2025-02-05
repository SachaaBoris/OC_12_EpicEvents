import re
from peewee import *
from .database import BaseModel
from models.role import Role
from models.permission import Permission

class RolePermission(BaseModel):
    """Associates roles with permissions (many-to-many)."""
    role = ForeignKeyField(Role, backref="permissions", on_delete="CASCADE")
    permission = ForeignKeyField(Permission, backref="roles", on_delete="CASCADE")