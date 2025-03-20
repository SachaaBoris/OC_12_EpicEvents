import pytest
import os
from datetime import datetime
from peewee import SqliteDatabase
import epicevents.models.database as db_module

# Créer une base SQLite en mémoire
test_db = SqliteDatabase(':memory:')
db_module.psql_db = test_db # Remplacer db_module postgre par la base SQLite

# Mettre à jour la base utilisée par tous les modèles via BaseModel
from epicevents.models.database import BaseModel
BaseModel._meta.database = test_db

from typer.testing import CliRunner
from epicevents.models.database import BaseModel
from epicevents.models.role import Role
from epicevents.models.user import User
from epicevents.models.company import Company
from epicevents.models.customer import Customer
from epicevents.models.contract import Contract
from epicevents.models.event import Event
import epicevents.models.database as db_module


# Fermer toute connexion existante
if test_db.is_closed():
    test_db.connect()

# Créer les tables et les rôles de test
test_db.create_tables([Role, User, Company, Customer, Contract, Event])
roles = ["admin", "management", "sales", "support"]
role_objs = {role: Role.get_or_create(name=role)[0] for role in roles}


@pytest.fixture
def setup_db_tables():
    """Crée les tables nécessaires dans la base de données en mémoire."""
    # Récupérer la base de données SQLite en mémoire depuis BaseModel
    test_db = BaseModel._meta.database
    
    # S'assurer que la base de données est ouverte
    if test_db.is_closed():
        test_db.connect()
    
    # Supprimer les tables si elles existent déjà
    test_db.drop_tables([Event, Contract, Customer, Company, User, Role], safe=True)
    
    # Créer les tables nécessaires pour les tests
    test_db.create_tables([Role, User, Company, Customer, Contract, Event])
    
    # Configurer la variable d'environnement pour le test
    import os
    os.environ["CURRENCY"] = "EUR"
    
    return test_db


@pytest.fixture
def create_test_data(monkeypatch):
    """Crée des données de test et configure l'environnement."""
    # Configurer la variable d'environnement pour la devise
    monkeypatch.setenv("CURRENCY", "EUR")
    
    # Créer des rôles et des utilisateurs de test
    from epicevents.models.role import Role
    admin_role = Role.get_or_create(name="admin")[0]
    management_role = Role.get_or_create(name="management")[0]
    sales_role = Role.get_or_create(name="sales")[0]
    support_role = Role.get_or_create(name="support")[0]
    
    # Créer un utilisateur de gestion
    manager = User.get_or_create(
        username="manager",
        defaults={
            "email": "manager@epicevents.com",
            "first_name": "Manager",
            "last_name": "Test",
            "phone": "0123456789",
            "password": "password123",
            "role": management_role
        }
    )[0]
    
    # Créer une entreprise et un client
    from epicevents.models.company import Company
    company = Company.get_or_create(name="Test Company")[0]
    
    customer = Customer.get_or_create(
        email="client@test.com",
        defaults={
            "first_name": "Client",
            "last_name": "Test",
            "phone": "0987654321",
            "company": company,
            "team_contact_id": manager
        }
    )[0]
    
    # Créer un contrat de test
    contract = Contract.get_or_create(
        customer=customer,
        defaults={
            "signed": True,
            "amount_total": 1000.0,
            "amount_due": 500.0,
            "team_contact_id": manager
        }
    )[0]
    
    # Data
    return {
        "admin_role": admin_role,
        "management_role": management_role,
        "sales_role": sales_role,
        "support_role": support_role,
        "manager": manager,
        "company": company,
        "customer": customer,
        "contract": contract
    }

# Fixture de nettoyage à la fin de chaque test
@pytest.fixture(autouse=True)
def db_teardown():
    yield
    if not test_db.is_closed():
        test_db.close()


# Classe pour une pseudo-base de données qui ne fait rien
class MockDB:
    @staticmethod
    def execute_sql(*args, **kwargs):
        pass

# Fixture pour le runner CLI
@pytest.fixture
def runner():
    return CliRunner()


# Classes de simulation
class MockRole:
    def __init__(self, name, id):
        self.name = name
        self.id = id

    def __int__(self):
        return self.id


class MockUser:
    def __init__(self, id, username, email, first_name, last_name, phone, role):
        self.id = id
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.role = role

    def __int__(self):
        return self.id

    def get_data(self):
        return {
            "user_id": self.id,
            "email": self.email,
            "role_id": self.role,
        }


class MockCompany:
    def __init__(self, id, name):
        self.id = id
        self.name = name
    
    def __int__(self):
        return self.id


class MockCustomer:
    def __init__(self, id, first_name, last_name, email, phone, company, date_created, date_updated, team_contact_id=None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.company = company
        self.date_created = date_created
        self.date_updated = date_updated
        self.team_contact_id = team_contact_id

    def __int__(self):
        return self.id

    def get_data(self):
        return {
            "customer_id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "date_created": self.date_created,
            "date_updated": self.date_updated,
            "team_contact_id": self.team_contact_id
        }


class MockContract:
    def __init__(self, id, customer, signed, date_created, date_updated, amount_total, amount_due, team_contact_id=None):
        self.id = id
        self.customer = customer
        self.signed = signed
        self.date_created = date_created
        self.date_updated = date_updated
        self.amount_total = amount_total
        self.amount_due = amount_due
        self.team_contact_id = team_contact_id

    def __int__(self):
        return self.id

    def get_data(self):
        return {
            "contract_id": self.id,
            "customer": self.customer.get_data() if self.customer else None,
            "signed": self.signed,
            "date_created": self.date_created,
            "date_updated": self.date_updated,
            "amount_total": self.amount_total,
            "amount_due": self.amount_due if self.amount_due else 0.0,
            "team_contact_id": self.team_contact_id,
        }


class MockEvent:
    def __init__(self, id, contract, name, location, event_date, attendees, notes, date_created, date_updated, team_contact_id=None):
        self.id = id
        self.contract = contract
        self.name = name
        self.location = location
        self.event_date = event_date
        self.attendees = attendees
        self.notes = notes
        self.date_created = date_created
        self.date_updated = date_updated
        self.team_contact_id = team_contact_id

    def __int__(self):
        return self.id

    def get_data(self):
        return {
            "event_id": self.id,
            "contract": self.contract.get_data() if self.contract else None,
            "name": self.name,
            "location": self.location,
            "event_date": self.event_date,
            "attendees": self.attendees,
            "notes": self.notes,
            "date_created": self.date_created,
            "date_updated": self.date_updated,
            "team_contact_id": self.team_contact_id,
        }


class MockDatetime:
    @staticmethod
    def now():
        return datetime(2023, 1, 1, 12, 0, 0)
    
    @staticmethod
    def strptime(date_string, format):
        # Déléguer à la vraie fonction strptime
        return datetime.strptime(date_string, format)


class MockContext:
    """Classe pour simuler un contexte Typer."""
    def __init__(self, user):
        self.obj = user


# Fixtures pour simuler des utilisateurs
@pytest.fixture
def mock_admin_user():
    """Crée un utilisateur admin mock"""
    mock_role = MockRole(name="admin", id=1)
    
    mock_user = MockUser(
        id=1,
        username="admin",
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        phone="0123456789",
        role=mock_role
    )
    
    return mock_user


@pytest.fixture
def mock_manager_user():
    """Crée un utilisateur manager mock"""
    mock_role = MockRole(name="management", id=2)
    
    mock_user = MockUser(
        id=3,
        username="manage",
        email="manage@example.com",
        first_name="Manage",
        last_name="User",
        phone="0123456789",
        role=mock_role
    )
    
    return mock_user


@pytest.fixture
def mock_sales_user():
    """Crée un utilisateur commercial mock"""
    mock_role = MockRole(name="sales", id=3)
    
    mock_user = MockUser(
        id=3,
        username="sales",
        email="sales@example.com",
        first_name="Sales",
        last_name="User",
        phone="0123456789",
        role=mock_role
    )
    
    return mock_user


@pytest.fixture
def mock_support_user():
    """Crée un utilisateur support mock"""
    mock_role = MockRole(name="support", id=4)
    
    mock_user = MockUser(
        id=3,
        username="support",
        email="support@example.com",
        first_name="Support",
        last_name="User",
        phone="0123456789",
        role=mock_role
    )
    
    return mock_user
    

# Fixture pour simuler un client
@pytest.fixture
def mock_customer():
    """Crée un client mock"""
    mock_company = MockCompany(1, name="ACME")

    mock_user = MockUser(
        id=3,
        username="sales",
        email="sales@example.com",
        first_name="Sales",
        last_name="User",
        phone="0123456789",
        role=MockRole(name="sales", id=3)
    )

    mock_customer = MockCustomer(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="0123456789",
        company=mock_company,
        date_created=datetime.now(),
        date_updated=datetime.now(),
        team_contact_id=mock_user
    )

    return mock_customer


# Helper pour créer un mock de Peewee QuerySet
def create_query_mock(mocker, items):
    query_mock = mocker.MagicMock()
    query_mock.exists.return_value = bool(items)
    query_mock.__iter__.return_value = iter(items)
    query_mock.__len__.return_value = len(items)
    query_mock.limit.return_value = query_mock
    query_mock.offset.return_value = query_mock
    return query_mock
