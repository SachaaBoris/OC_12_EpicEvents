from dotenv import get_key
from datetime import datetime, timedelta
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

def create_test_data():
    # Creating test users
    test_users = [
        ("Admin_test", "ADMIN_PASS", "Admin", "Test", "admin_test@email.com", "0102030405", "admin"),
        ("Manage_test", "MANAGE_PASS", "Management", "Test", "manage_test@email.com", "0102030405", "management"),
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

    # Creating test customers
    test_customers = [
        ("John", "Doe", "john.doe@email.com", "0601020304", "Super Corp", 3),
        ("Emily", "Smith", "emily.smith@email.com", "0604030201", "Mega Corp", 3)
    ]

    for first_name, last_name, email, phone, company_name, team_contact_id in test_customers:
        try:
            company, created = Company.get_or_create(name=company_name)
            Customer.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                company=company,  # FK
                team_contact_id=User.get_by_id(team_contact_id)  # FK
            )
            print(f"✅ Customer {first_name} {last_name} created successfully.")
        except Exception as e:
            print(f"❌ Failed to create customer {first_name} {last_name}: {e}")

    # Creating test contracts
    test_contracts = [
        (1, True, 5000.0, 0.0, 2),
        (2, True, 2000.0, 2000.0, 2)
    ]

    for customer_id, signed, amount_total, amount_due, team_contact_id in test_contracts:
        try:
            Contract.create(
                customer=Customer.get_by_id(customer_id),  # FK
                signed=signed,
                amount_total=amount_total,
                amount_due=amount_due,
                team_contact_id=User.get_by_id(team_contact_id)  # FK
            )
            print(f"✅ Contract for customer {customer_id} created successfully.")
        except Exception as e:
            print(f"❌ Failed to create contract for customer {customer_id}: {e}")

    # Creating test events
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
                contract=Contract.get_by_id(contract_id),  # FK
                name=name,
                location=location,
                event_date=datetime.strptime(event_date, "%Y-%m-%d %H:%M:%S"),
                attendees=attendees,
                notes=notes,
                team_contact_id=User.get_by_id(team_contact_id)  # FK
            )
            print(f"✅ Event {name} created successfully.")
        except Exception as e:
            print(f"❌ Failed to create event {name}: {e}")

    try:
        """Closing the database."""
        psql_db.close()
        print("✅ Database connection closed.")
    except Exception as e:
        print(f"❌ Failed to close the database connection: {e}")

if __name__ == "__main__":
    create_test_data()
