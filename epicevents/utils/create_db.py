from dotenv import get_key
from epicevents.utils.create_test_data import create_test_data
from epicevents.models.database import psql_db
from epicevents.models.role import Role
from epicevents.models.user import User
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
    close_db()
    prompt_create_test_data()


if __name__ == "__main__":
    generate_working_db()
