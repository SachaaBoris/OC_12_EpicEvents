import re
from peewee import *
from .database import BaseModel
from models.role import Role
from models.permission import Permission


""" rolepermission table export :
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃    role    ┃                                       permissions                                        ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│   admin    │      user_create, user_read, user_list, user_update, user_delete, customer_create,       │
│            │     customer_read, customer_list, customer_update, customer_delete, contract_create,     │
│            │      contract_read, contract_list, contract_update, contract_delete, event_create,       │
│            │  event_read, event_list, event_update, event_delete, user_read_self, user_update_self,   │
│            │                                     user_delete_self                                     │
│ management │    user_create, user_read, user_read_self, user_list, user_update, user_update_self,     │
│            │      user_delete, user_delete_self, customer_read, customer_list, contract_create,       │
│            │   contract_read, contract_list, contract_update, event_read, event_list, event_update,   │
│            │                                       event_delete                                       │
│   sales    │     user_read_self, user_list, user_update_self, user_delete_self, customer_create,      │
│            │       customer_read, customer_list, customer_update, contract_read, contract_list,       │
│            │           contract_update, event_create, event_read, event_list, event_update            │
│  support   │      user_read_self, user_list, user_update_self, user_delete_self, customer_read,       │
│            │    customer_list, contract_read, contract_list, event_read, event_list, event_update     │
└────────────┴──────────────────────────────────────────────────────────────────────────────────────────┘
"""

class RolePermission(BaseModel):
    """Associates roles with permissions."""
    role = ForeignKeyField(Role, backref="permissions", on_delete="CASCADE")
    permission = ForeignKeyField(Permission, backref="roles", on_delete="CASCADE")

    class Meta:
        indexes = ((("role", "permission"), True),)
