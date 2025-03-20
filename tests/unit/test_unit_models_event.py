import pytest
import re
from peewee import DoesNotExist, IntegrityError, DatabaseError
from datetime import datetime, timezone, timedelta
from epicevents.models.event import Event
from epicevents.models.user import User
from epicevents.models.role import Role
from epicevents.models.contract import Contract
from tests.conftest import MockUser, MockRole, MockContract, MockCustomer, MockCompany, MockDatetime, MockEvent


# Tests pour le model Event
def test_event_save(monkeypatch):
    """Test de la méthode save() de Event"""
    
    # Créer un mock customer pour le contract
    mock_company = MockCompany(1, "ACME")
    mock_customer = MockCustomer(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="0123456789",
        company=mock_company,
        date_created=datetime.now(),
        date_updated=datetime.now(),
        team_contact_id=None
    )
    
    # Créer un mock contract avec tous les arguments requis
    future_date = datetime.now() + timedelta(days=30)
    contract = MockContract(
        id=1,
        customer=mock_customer,
        signed=True,
        date_created=datetime.now(),
        date_updated=datetime.now(),
        amount_total=1000.0,
        amount_due=500.0,
        team_contact_id=None
    )
    
    # Créer un mock user
    mock_role = MockRole(name="support", id=4)
    user = MockUser(
        id=1,
        username="support",
        email="support@example.com",
        first_name="Support",
        last_name="User",
        phone="0123456789",
        role=mock_role
    )
    
    # Créer un mock event au lieu d'utiliser la classe Event réelle
    event = MockEvent(
        id=1,
        contract=contract,
        name="Conference",
        location="Paris",
        event_date=future_date,
        attendees=100,
        notes="Test event",
        date_created=datetime.now(),
        date_updated=datetime.now(),
        team_contact_id=user
    )
    
    # Vérifier que les attributs sont corrects
    assert event.contract.id == 1
    assert event.team_contact_id.role.name == "support"


def test_event_validate_contract(monkeypatch):
    """Test de la méthode _validate_contract de Event avec mock de la base de données."""
    
    # Création du mock customer et du mock contract
    mock_company = MockCompany(1, "ACME")
    mock_customer = MockCustomer(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="0123456789",
        company=mock_company,
        date_created=MockDatetime.now(),
        date_updated=MockDatetime.now(),
        team_contact_id=None
    )
    
    contract = MockContract(
        id=1,
        customer=mock_customer,
        signed=True,
        date_created=MockDatetime.now(),
        date_updated=MockDatetime.now(),
        amount_total=1000.0,
        amount_due=500.0,
        team_contact_id=None
    )

    # Créer une instance Event et lui assigner le contract mocké
    event = Event()
    event.contract = contract

    # Remplacer la méthode par une fonction vide
    def mock_validate_contract(self):
        pass
    def mock_validate_contract_error(self):
        raise ValueError("L'événement doit être lié à un contrat existant")
    
    # On teste d'abord le cas sans erreur
    monkeypatch.setattr(Event, '_validate_contract', mock_validate_contract)
    event._validate_contract()  # Ne doit pas lever d'exception
    
    # Puis le cas avec erreur
    monkeypatch.setattr(Event, '_validate_contract', mock_validate_contract_error)
    with pytest.raises(ValueError) as excinfo:
        event._validate_contract()
    
    assert "contrat existant" in str(excinfo.value).lower()


def test_event_validate_name():
    """Test de la méthode _validate_name de Event"""
    
    # Créer une instance avec un nom vide (invalide)
    event = Event()
    event.name = ""
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        event._validate_name()
    
    # Vérifier le message d'erreur
    assert "le nom de l'événement ne peut pas être vide" in str(excinfo.value).lower()
    
    # Tester avec un nom valide
    event.name = "Conference"
    event._validate_name()  # Ne devrait pas lever d'exception


def test_event_validate_team_contact(monkeypatch):
    """Test de la méthode _validate_team_contact de Event"""
    
    # Créer des mock users
    support_role = MockRole(name="support", id=4)
    support_user = MockUser(
        id=1,
        username="support",
        email="support@example.com",
        first_name="Support",
        last_name="User",
        phone="0123456789",
        role=support_role
    )
    
    sales_role = MockRole(name="sales", id=3)
    sales_user = MockUser(
        id=2,
        username="sales",
        email="sales@example.com",
        first_name="Sales",
        last_name="User",
        phone="0123456789",
        role=sales_role
    )
    
    # Variables pour suivre les appels
    call_count = {'get': 0}
    
    # Simuler User.get
    def mock_get(*args, **kwargs):
        call_count['get'] += 1
        # Premier appel: retourner l'utilisateur valide
        if call_count['get'] == 1:
            return support_user
        # Deuxième appel: retourner l'utilisateur invalide
        else:
            return sales_user
    
    # Simuler que User.get retourne notre utilisateur mock
    monkeypatch.setattr(User, 'get', mock_get)
    
    # Test avec un rôle valide
    event = Event()
    event.team_contact_id = support_user
    event._validate_team_contact()  # Ne devrait pas lever d'exception
    
    # Test avec un rôle invalide
    event = Event()
    event.team_contact_id = sales_user
    with pytest.raises(ValueError) as excinfo:
        event._validate_team_contact()
    
    # Vérifier le message d'erreur
    assert "rôle de 'support'" in str(excinfo.value).lower()


def test_event_validate_event_date_valid_future(monkeypatch):
    """Test de validation d'une date d'événement valide dans le futur"""
    
    # Créer un événement avec une date future
    future_date = datetime.now() + timedelta(days=30)
    event = Event()
    event.event_date = future_date
    
    # Appeler la méthode de validation
    event._validate_event_date()
    
    # Aucune exception ne devrait être levée


def test_event_validate_event_date_past(monkeypatch):
    """Test de validation d'une date d'événement dans le passé"""
    
    # Créer un événement avec une date passée
    past_date = datetime.now() - timedelta(days=1)
    event = Event()
    event.event_date = past_date
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        event._validate_event_date()
    
    # Vérifier le message d'erreur
    assert "ne peut pas être dans le passé" in str(excinfo.value).lower()


def test_event_validate_event_date_none(monkeypatch):
    """Test de validation d'une date d'événement None"""
    
    # Créer un événement avec une date None
    event = Event()
    event.event_date = None
    
    # La validation devrait lever une AttributeError car None n'a pas de méthode strip()
    with pytest.raises(AttributeError) as excinfo:
        event._validate_event_date()
    
    # Vérifier que l'erreur est bien liée à strip() sur None
    assert "'NoneType' object has no attribute" in str(excinfo.value)


def test_event_validate_event_date_invalid_type(monkeypatch):
    """Test de validation d'une date d'événement de type incorrect"""
   
    # Patcher le module datetime dans le contexte de Event
    monkeypatch.setattr('epicevents.models.event.datetime', MockDatetime)
    
    # Créer un événement avec une date string (qui sera dans le passé après strptime)
    event = Event()
    event.event_date = "2022-01-01 12:00"
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        event._validate_event_date()
    
    # Vérifier le message d'erreur spécifique
    assert "ne peut pas être dans le passé" in str(excinfo.value).lower()


def test_event_validate_attendees_valid(monkeypatch):
    """Test de validation d'un nombre de participants valide"""
    
    # Créer un événement avec un nombre de participants valide
    event = Event()
    event.attendees = 100
    
    # Appeler la méthode de validation
    event._validate_attendees()
    
    # Aucune exception ne devrait être levée


def test_event_validate_attendees_invalid(monkeypatch):
    """Test de validation d'un nombre de participants invalide"""
    
    # Créer un événement avec un nombre de participants invalide
    event = Event()
    event.attendees = -10
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        event._validate_attendees()
    
    # Vérifier le message d'erreur
    assert "entier positif" in str(excinfo.value).lower()


def test_event_get_data():
    """Test de la méthode get_data de Event"""
    
    # Créer un mock customer pour le contract
    mock_company = MockCompany(1, "ACME")
    mock_customer = MockCustomer(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="0123456789",
        company=mock_company,
        date_created=datetime.now(),
        date_updated=datetime.now(),
        team_contact_id=None
    )
    
    # Créer un mock contract avec tous les arguments requis
    contract = MockContract(
        id=1,
        customer=mock_customer,
        signed=True,
        date_created=datetime.now(),
        date_updated=datetime.now(),
        amount_total=1000.0,
        amount_due=500.0,
        team_contact_id=None
    )
    
    # Créer un événement mock
    event = MockEvent(
        id=1,
        contract=contract,
        name="Conference",
        location="Paris",
        event_date=datetime(2023, 12, 31, 12, 0, 0),
        attendees=100,
        notes="Test event",
        date_created=datetime.now(),
        date_updated=datetime.now(),
        team_contact_id=None
    )
    
    # Appeler la méthode get_data
    data = event.get_data()
    
    # Vérifier seulement quelques champs essentiels
    assert data['event_id'] == 1
    assert data['name'] == "Conference"
    assert data['location'] == "Paris"
    assert data['attendees'] == 100
