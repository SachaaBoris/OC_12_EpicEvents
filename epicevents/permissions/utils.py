from epicevents.models.user import User


def always_true(*args) -> bool:
    """Default permission function that always returns True."""
    return True

def is_self(user, target_user):
    """Checks if target user is the same as the requesting user."""
    return user.id == target_user.id

def is_owner(user, entity):
    """Checks if user is the owner of the entity."""
    if hasattr(entity, 'team_contact_id'):
        return entity.team_contact_id == user.id
    return False

# Defining all pemission cases
ROLES_PERMISSIONS = {
    "admin": {
        "*": {
            "*": lambda *args: True  # Admin has all rights
        }
    },
    "management": {
        "user": {
            "create": always_true,
            "read": always_true,
            "list": always_true,
            "update": always_true
        },
        "customer": {
            "read": always_true,
            "list": always_true
        },
        "contract": {
            "create": always_true,
            "read": always_true,
            "list": always_true,
            "update": is_owner
        },
        "event": {
            "read": always_true,
            "list": always_true,
            "update": always_true
        }
    },
    "sales": {
        "user": {
            "list": always_true,
            "read": is_self,
            "update": is_self
        },
        "customer": {
            "create": always_true,
            "read": always_true,
            "list": always_true,
            "update": is_owner
        },
        "contract": {
            "read": always_true,
            "list": always_true,
            "update": is_owner
        },
        "event": {
            "create": always_true,
            "read": always_true,
            "list": always_true,
            "update": always_true
        }
    },
    "support": {
        "user": {
            "list": always_true,
            "read": is_self,
            "update": is_self
        },
        "customer": {
            "read": always_true,
            "list": always_true
        },
        "contract": {
            "read": always_true,
            "list": always_true
        },
        "event": {
            "list": always_true,
            "read": is_owner,
            "update": is_owner
        }
    }
}

def get_all_permissions():
    """Returns a list of all permissions in the system."""
    all_permissions = []
    admin_permission = {
        "Rôle": "admin",
        "Ressource": "*",
        "Action": "*"
    }
    all_permissions.append(admin_permission)

    for role, resources in ROLES_PERMISSIONS.items():
        if role == "admin":
            continue  # Ignore admin wildcard

        # Group actions by resource
        resource_actions = {}
        for resource, actions in resources.items():
            action_list = []
            for action, func in actions.items():
                if func == always_true:
                    action_list.append(action)
                elif func == is_self:
                    action_list.append(f"{action}_self")
                elif func == is_owner:
                    action_list.append(f"{action}_own")
                # Ignore False permissions (func is None)

            if action_list:  # Only add if there are actions
                resource_actions[resource] = ", ".join(action_list)

        # Add grouped permissions to the list
        for resource, actions in resource_actions.items():
            permission = {
                "Rôle": role,
                "Ressource": resource,
                "Action": actions
            }
            all_permissions.append(permission)

    return all_permissions