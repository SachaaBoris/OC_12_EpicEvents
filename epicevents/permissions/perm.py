from typing import Any
from peewee import DoesNotExist
from epicevents.models.user import User
from epicevents.models.customer import Customer
from epicevents.models.contract import Contract
from epicevents.models.event import Event


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

def is_my_customer(user, event_id):
    """
    Checks if a user owns the customer linked to an event through its contract.
    
    Args:
        user: The user attempting to perform the action
        event_id: The ID of the event
    
    Returns:
        tuple: (success, error_message) where success is a boolean and error_message is None or a string
    """
    from epicevents.models.contract import Contract
    from epicevents.models.event import Event
    from peewee import DoesNotExist
    
    try:
        # Get the Event from database using the ID
        event = Event.get_by_id(event_id)
        
        # Ensure the event has a contract
        if not hasattr(event, 'contract'):
            return False, "L'événement n'a pas de contrat associé."
            
        if not event.contract:
            return False, "L'événement n'a pas de contrat associé."
        
        # Get the contract
        contract = Contract.get_by_id(event.contract.id)
        
        if contract:
            # Ensure the contract is signed
            if not contract.signed:
                return False, "Le contrat n'est pas encore signé."
            
            # Check if user is the contact for the customer
            if contract.customer_id:
                result = Customer.select().where(
                    (Customer.id == contract.customer_id) & 
                    (Customer.team_contact_id == user.id)
                ).exists()
                
                if result:
                    return True, None
                else:
                    return False, "Vous n'êtes pas le commercial associé à ce client."
            else:
                return False, "Le contrat n'a pas de client associé."
        else:
            return False, "Impossible de trouver le contrat associé à cet événement."
            
    except DoesNotExist:
        return False, f"L'événement {event_id} n'existe pas."
    except Exception as e:
        return False, f"Erreur lors de la vérification des permissions: {str(e)}"

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
            "update": is_self
        },
        "customer": {
            "read": always_true,
            "list": always_true
        },
        "contract": {
            "create": always_true,
            "read": always_true,
            "list": always_true,
            "update": always_true
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
            "create": is_my_customer,
            "read": always_true,
            "list": always_true,
            "update": is_my_customer
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
            "read": always_true
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

def has_permission(user: User, resource: str, action: str, target: Any = None) -> bool:
    """ Checks if user has permission to perform a specific action on a given resource.

    Args:
        user: Actual user attempting to perform the action
        resource: The targeted resource (user, customer, contract, event)
        action: The action to perform (create, read, list, update, delete)
        target: The object targeted by the action (optional)

    Returns:
        tuple: (success, error_message) where success is a boolean and error_message is None or a string
    """

    # Admin has all permissions
    if user.role.name == "admin":
        return True, None

    role_perms = ROLES_PERMISSIONS.get(user.role.name, {})
    resource_perms = role_perms.get(resource, {})
    permission_func = resource_perms.get(action)

    if permission_func is None:
        return False, f"Votre rôle ({user.role.name}) n'a pas l'autorisation pour '{action}' sur '{resource}'."

    # Special case for is_my_customer which returns a tuple (success, error_message)
    if permission_func == is_my_customer:
        return permission_func(user, target)

    # For other permission functions that only return a boolean
    if target is None:
        result = permission_func()
    else:
        result = permission_func(user, target)
 
    if result:
        return True, None
    else:
        # Generic error message for other permission functions
        return False, f"Vous n'avez pas l'autorisation requise pour cette action."
