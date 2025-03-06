from dotenv import get_key
from datetime import datetime, timedelta
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

def create_users():
    """Creates a user per role."""
    test_users = [
        ("Admin_test", "ADMIN_PASS", "Admin", "Test", "admin_test@email.com", "0102030405", "admin"),
        ("Manage_test1", "MANAGE_PASS1", "Management", "Test_One", "manage_test1@email.com", "0102030405", "management"),
        ("Sales_test1", "SALES_PASS1", "Sales", "Test_One", "sales_test1@email.com", "0102030405", "sales"),
        ("Support_test1", "SUPPORT_PASS1", "Support", "Test_One", "support_test1@email.com", "0102030405", "support"),
        ("Manage_test2", "MANAGE_PASS2", "Management", "Test_Two", "manage_test2@email.com", "0102030405", "management"),
        ("Sales_test2", "SALES_PASS2", "Sales", "Test_Two", "sales_test2@email.com", "0102030405", "sales"),
        ("Support_test2", "SUPPORT_PASS2", "Support", "Test_Two", "support_test2@email.com", "0102030405", "support"),
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
                role=Role.get(name=role)
            )
            print(f"✅ {role.capitalize()} user created successfully.")
        except Exception as e:
            print(f"❌ Failed to create {role} user: {e}")

def create_customers():
    """Creates 2 customers."""
    test_customers = [
        ("John", "Doe", "john.doe@email.com", "0601020304", "Super Corp", 3),
        ("Emily", "Smith", "emily.smith@email.com", "0604030201", "Mega Corp", 3)
    ]
    for first_name, last_name, email, phone, company_name, team_contact_id in test_customers:
        try:
            company, _ = Company.get_or_create(name=company_name)
            Customer.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                company=company,
                team_contact_id=User.get_by_id(team_contact_id)
            )
            print(f"✅ Customer {first_name} {last_name} created successfully.")
        except Exception as e:
            print(f"❌ Failed to create customer {first_name} {last_name}: {e}")

def create_contracts():
    """Creates 2 contracts."""
    test_contracts = [
        (1, True, 5000.0, 0.0, 2),
        (2, True, 2000.0, 2000.0, 2)
    ]
    for customer_id, signed, amount_total, amount_due, team_contact_id in test_contracts:
        try:
            Contract.create(
                customer=Customer.get_by_id(customer_id),
                signed=signed,
                amount_total=amount_total,
                amount_due=amount_due,
                team_contact_id=User.get_by_id(team_contact_id)
            )
            print(f"✅ Contract for customer {customer_id} created successfully.")
        except Exception as e:
            print(f"❌ Failed to create contract for customer {customer_id}: {e}")

def create_events():
    """Creates 2 events."""
    current_time = datetime.now()
    test_events = [
        (1, "Conférence annuelle", "26 Waterloo Rd, SE1 8TY, London, UK", 
         (current_time + timedelta(days=180)).strftime("%Y-%m-%d %H:%M:%S"),
         150, "Penser aux croissants.", 4),
        (2, "Blast from the Past", "3 place de l'église, 93100 Montreuil, FR", 
         (current_time + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S"),
         50, "Prévoir un accès PMR.", 4)
    ]
    for contract_id, name, location, event_date, attendees, notes, team_contact_id in test_events:
        try:
            Event.create(
                contract=Contract.get_by_id(contract_id),
                name=name,
                location=location,
                event_date=datetime.strptime(event_date, "%Y-%m-%d %H:%M:%S"),
                attendees=attendees,
                notes=notes,
                team_contact_id=User.get_by_id(team_contact_id)
            )
            print(f"✅ Event {name} created successfully.")
        except Exception as e:
            print(f"❌ Failed to create event {name}: {e}")

def close_db():
    """Closes db connection."""
    try:
        psql_db.close()
        print("✅ Database connection closed.")
    except Exception as e:
        print(f"❌ Failed to close the database connection: {e}")

def create_test_data():
    postgre_connect()
    create_users()
    create_customers()
    create_contracts()
    create_events()
    close_db()

if __name__ == "__main__":
    create_test_data()
