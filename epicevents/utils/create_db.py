from dotenv import get_key
from epicevents.utils.create_test_data import create_test_data
from epicevents.models.database import psql_db
from epicevents.models.role import Role
from epicevents.models.user import User
#from epicevents.models.permission import Permission
#from epicevents.models.rolepermission import RolePermission
from epicevents.models.company import Company
from epicevents.models.customer import Customer
from epicevents.models.contract import Contract
from epicevents.models.event import Event


ADMIN_EMAIL = get_key(".env", "ADMIN_EMAIL")
ADMIN_PASSWORD = get_key(".env", "ADMIN_PASSWORD")

def postgre_connect():
    """Connecting to the database."""
    try:
        psql_db.connect()
        print("✅ Connection to database established.")
    except Exception as e:
        print(f"❌ Failed to connect to the database: {e}")
        exit(1)

def create_db():
    """Table creation."""
    try:
        psql_db.create_tables([Role, User, Company, Customer, Contract, Event])
        print("✅ Tables created successfully!")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        exit(1)

def create_roles():
    """Creates roles."""
    try:
        roles = ["admin", "management", "sales", "support"]
        role_objs = {role: Role.get_or_create(name=role)[0] for role in roles}

        print("✅ Roles created successfully!")
        return role_objs
    except Exception as e:
        print(f"❌ Failed to create roles : {e}")
        exit(1)

def create_permissions():
    """Creates permissions combinations."""
    try:
        settings = ["user", "customer", "contract", "event"]
        actions = ["create", "read", "list", "update", "delete"]

        perm_objs = {}
        for setting in settings:
            for action in actions:
                perm_name = f"{setting}_{action}"
                perm_objs[perm_name] = Permission.get_or_create(name=perm_name)[0]

        print("✅ Permissions created successfully!")
        return perm_objs
    except Exception as e:
        print(f"❌ Failed to create permissions: {e}")
        exit(1)

def give_roles_permissions(role_objs, perm_objs):
    # Give roles permissions
    try:
        role_permissions = {
            "admin": list(perm_objs.keys()),  # full access

            "management": [
                "user_create", "user_read", "user_list", "user_update", "user_delete",
                "customer_read", "customer_list", "customer_update", "customer_delete",
                "contract_create", "contract_read", "contract_list", "contract_update", "contract_delete",
                "event_read", "event_list", "event_update", "event_delete"
            ],

            "sales": [
                "user_list",
                "customer_create", "customer_read", "customer_list", "customer_update",
                "contract_read", "contract_list", "contract_update",
                "event_create", "event_read", "event_list", "event_update"
            ],

            "support": [
                "user_list",
                "customer_read", "customer_list",
                "contract_read", "contract_list",
                "event_read", "event_list", "event_update"
            ],
        }

        for role, perms in role_permissions.items():
            for perm in perms:
                RolePermission.get_or_create(role=role_objs[role], permission=perm_objs[perm])

        print("✅ Roles were given permissions successfully!")
    except Exception as e:
        print(f"❌ Failed to give roles their permissions: {e}")
        exit(1)

def close_db():
    """Closes db connection"""
    try:
        psql_db.close()
        print("✅ Database connection closed.")
    except Exception as e:
        print(f"❌ Failed to close the database connection: {e}")

def prompt_create_test_data():
    """Create test data prompt."""
    user_input = input("Voulez-vous créer des données de test ? (o/n) : ").strip().lower()
    if user_input == "o":
        create_test_data()

def generate_working_db():
    postgre_connect()
    create_db()
    create_roles()
    # Unused since switched to ABAC
    #role_objs = create_roles()
    #perm_objs = create_permissions()
    #give_roles_permissions(role_objs, perm_objs)
    close_db()
    prompt_create_test_data()

if __name__ == "__main__":
    generate_working_db()
