from create_test_data import create_test_data
from dotenv import get_key
from models.database import psql_db
from models.role import Role
from models.permission import Permission
from models.rolepermission import RolePermission
from models.user import User
from models.company import Company
from models.customer import Customer
from models.contract import Contract
from models.event import Event


ADMIN_EMAIL = get_key(".env", "ADMIN_EMAIL")
ADMIN_PASSWORD = get_key(".env", "ADMIN_PASSWORD")

def create_db():
    try:
        """Connecting to the database."""
        psql_db.connect()
        print("✅ Connection to the database established successfully.")
    except Exception as e:
        print(f"❌ Failed to connect to the database: {e}")
        exit(1)

    try:
        """Table creation."""
        psql_db.create_tables([Role, Permission, RolePermission, User, Company, Customer, Contract, Event])
        print("✅ Tables created successfully.")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        exit(1)

    try:
        """Initializes roles and permissions in the database."""
        roles = ["admin", "management", "sales", "support"]
        settings = ["user", "customer", "contract", "event"]
        actions = ["create", "read", "list", "update", "delete"]

        role_objs = {role: Role.get_or_create(name=role)[0] for role in roles}

        # Creates `setting_action` permissions (ex: `user_create`)
        perm_objs = {}
        for setting in settings:
            for action in actions:
                perm_name = f"{setting}_{action}"
                perm_objs[perm_name] = Permission.get_or_create(name=perm_name)[0]

        perm_objs["user_read_self"] = Permission.get_or_create(name="user_read_self")[0]
        perm_objs["user_update_self"] = Permission.get_or_create(name="user_update_self")[0]
        perm_objs["user_delete_self"] = Permission.get_or_create(name="user_delete_self")[0]
        
        # Give roles permissions
        role_permissions = {
            "admin": list(perm_objs.keys()),  # full access

            "management": [
                "user_create", "user_read", "user_read_self", "user_list", "user_update", "user_update_self", "user_delete", "user_delete_self",
                "customer_read", "customer_list",
                "contract_create", "contract_read", "contract_list", "contract_update",
                "event_read", "event_list", "event_update", "event_delete"
            ],

            "sales": [
                "user_read_self","user_list", "user_update_self", "user_delete_self",
                "customer_create", "customer_read", "customer_list", "customer_update",
                "contract_read", "contract_list", "contract_update",
                "event_create", "event_read", "event_list", "event_update"
            ],

            "support": [
                "user_read_self","user_list", "user_update_self", "user_delete_self",
                "customer_read", "customer_list",
                "contract_read", "contract_list",
                "event_read", "event_list", "event_update"
            ],
        }

        for role, perms in role_permissions.items():
            for perm in perms:
                RolePermission.get_or_create(role=role_objs[role], permission=perm_objs[perm])

        print("✅ Roles and permissions created successfully!")
    except Exception as e:
        print(f"❌ Failed to create roles and permissions: {e}")
        exit(1)

    try:
        """Closing the database."""
        psql_db.close()
        print("✅ Database connection closed.")
    except Exception as e:
        print(f"❌ Failed to close the database connection: {e}")


def prompt_create_test_data():
    user_input = input("Voulez-vous créer des données de test ? (o/n) : ").strip().lower()
    if user_input == "o":
        create_test_data()

if __name__ == "__main__":
    create_db()
    prompt_create_test_data()
