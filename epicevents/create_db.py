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
    roles = ["admin", "sales", "support"]
    permissions = ["create", "read", "update", "delete"]

    # Creating roles
    role_objs = {role: Role.get_or_create(name=role)[0] for role in roles}

    # Creating permissions
    perm_objs = {perm: Permission.get_or_create(name=perm)[0] for perm in permissions}

    # Permissions and role attribution
    role_permissions = {
        "admin": list(permissions),
        "sales": ["create", "read", "update"],
        "support": ["read", "update"],
    }

    for role, perms in role_permissions.items():
        for perm in perms:
            RolePermission.get_or_create(role=role_objs[role], permission=perm_objs[perm])

    print("✅ Roles and permissions created successfully!")
except Exception as e:
    print(f"❌ Failed to create roles and permissions: {e}")
    exit(1)

# Creating test users
test_users = [
    ("Admin_test", "ADMIN_PASS", "Admin", "Test", "admin_test@email.com", "0102030405", "admin"),
    ("Sales_test", "SALES_PASS", "Sales", "Test", "sales_test@email.com", "0102030405", "sales"),
    ("Support_test", "SUPPORT_PASS", "Support", "Test", "support_test@email.com", "0102030405", "support"),
]

for username, password, first_name, last_name, email, phone, role in test_users:
    try:
        User.create(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            role=Role.get(name=role)  # FK
        )
        print(f"✅ {role.capitalize()} user created successfully.")
    except Exception as e:
        print(f"❌ Failed to create {role} user: {e}")

try:
    """Closing the database."""
    psql_db.close()
    print("✅ Database connection closed.")
except Exception as e:
    print(f"❌ Failed to close the database connection: {e}")
