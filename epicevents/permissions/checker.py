from typing import Any
from epicevents.models.user import User
from epicevents.permissions.utils import ROLES_PERMISSIONS


def has_permission(user: User, resource: str, action: str, target: Any = None) -> bool:
    """ Checks if user has permission to perform a specific action on a given resource.

    Args:
        user: Actual user attempting to perform the action
        resource: The targeted resource (user, customer, contract, event)
        action: The action to perform (create, read, list, update, delete)
        target: The object targeted by the action (optional)

    Returns:
        bool: True if the user has permission, False otherwise
    """
    if user.role.name == "admin":
        return True

    role_perms = ROLES_PERMISSIONS.get(user.role.name, {})
    resource_perms = role_perms.get(resource, {})
    permission_func = resource_perms.get(action)

    if permission_func is None:
        return False

    if target is None:
        return permission_func()
    return permission_func(user, target)
