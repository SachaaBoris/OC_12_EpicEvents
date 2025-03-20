import pytest
from peewee import IntegrityError
from datetime import datetime, timezone, timedelta
from epicevents.models.contract import Contract
from epicevents.models.user import User
from epicevents.models.role import Role
from tests.conftest import MockRole, MockUser
from tests.conftest import mock_customer


# Tests pour Contract
def test_contract_save(monkeypatch):
    """Test de la méthode save() de Contract"""
    # Créer des objets mock en utilisant ceux du conftest
    mock_customer = MockUser(1, "customer", "customer@example.com", "Customer", "User", "0123456789", 
                             MockRole("customer", 5))
    mock_user = MockUser(2, "manager", "manager@example.com", "Manager", "User", "0123456789", 
                         MockRole("management", 2))
    
    # Créer un compteur d'appels
    calls = {
        'base_save': 0,
        'validate_signed': 0,
        'validate_amounts': 0,
        'validate_date': 0,
        'validate_team_contact': 0
    }
    
    # Fonctions de remplacement
    def mock_base_save(self):
        calls['base_save'] += 1
    
    def mock_validate_signed(self):
        calls['validate_signed'] += 1
    
    def mock_validate_amounts(self):
        calls['validate_amounts'] += 1
    
    def mock_validate_date(self):
        calls['validate_date'] += 1
    
    def mock_validate_team_contact(self):
        calls['validate_team_contact'] += 1
    
    # Appliquer les patches
    monkeypatch.setattr('epicevents.models.contract.BaseModel.save', mock_base_save)
    monkeypatch.setattr(Contract, '_validate_signed', mock_validate_signed)
    monkeypatch.setattr(Contract, '_validate_amounts', mock_validate_amounts)
    monkeypatch.setattr(Contract, '_validate_date', mock_validate_date)
    monkeypatch.setattr(Contract, '_validate_team_contact', mock_validate_team_contact)
    
    # Créer une instance de contrat
    contract = Contract(
        customer=mock_customer,
        signed=True,
        amount_total=1000.0,
        amount_due=500.0,
        team_contact_id=mock_user
    )
    
    # Appeler la méthode save()
    contract.save()
    
    # Vérifier que toutes les méthodes de validation ont été appelées
    assert calls['validate_signed'] == 1
    assert calls['validate_amounts'] == 1
    assert calls['validate_date'] == 1
    assert calls['validate_team_contact'] == 1
    assert calls['base_save'] == 1


def test_contract_validate_signed():
    """Test de la méthode _validate_signed de Contract"""
    # Créer une instance avec signed=None (invalide)
    contract = Contract(signed=None)
    
    # La validation devrait lever une IntegrityError
    with pytest.raises(IntegrityError) as excinfo:
        contract._validate_signed()
    
    # Vérifier le message d'erreur
    assert "Le Contrat doit être signé" in str(excinfo.value)
    
    # Tester avec une valeur valide
    contract.signed = True
    contract._validate_signed()  # Ne devrait pas lever d'exception


def test_contract_validate_date():
    """Test de la méthode _validate_date de Contract"""
    # Créer une instance avec une date invalide (pas un datetime)
    contract = Contract()
    contract.date_created = "not-a-date"
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        contract._validate_date()
    
    # Vérifier le message d'erreur
    assert "format datetime valide" in str(excinfo.value)
    
    # Tester avec une date valide
    contract.date_created = datetime.now()
    contract._validate_date()  # Ne devrait pas lever d'exception


def test_contract_validate_amounts_valid(monkeypatch):
    """Test de validation des montants valides d'un contrat"""
    # Simuler la méthode save pour éviter l'accès à la base de données
    monkeypatch.setattr('epicevents.models.contract.Contract.save', lambda self: None)
    
    # Créer un contrat avec des montants valides
    contract = Contract(amount_total=1000, amount_due=500)
    
    # Appeler la méthode de validation
    contract._validate_amounts()
    
    # Aucune exception ne devrait être levée


def test_contract_validate_amounts_negative_total(monkeypatch):
    """Test de validation d'un montant total négatif"""
    # Simuler la méthode save pour éviter l'accès à la base de données
    monkeypatch.setattr('epicevents.models.contract.Contract.save', lambda self: None)
    
    # Créer un contrat avec un montant total négatif
    contract = Contract(amount_total=-100, amount_due=50)
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        contract._validate_amounts()
    
    # Vérifier le message d'erreur
    assert "ne peut pas être inférieur à zéro" in str(excinfo.value).lower()


def test_contract_validate_amounts_due_higher_than_total(monkeypatch):
    """Test de validation d'un montant dû supérieur au montant total"""
    
    # Simuler la méthode save pour éviter l'accès à la base de données
    def mock_save(self):
        pass
    
    monkeypatch.setattr('epicevents.models.contract.Contract.save', mock_save)
    
    # Créer un contrat avec un montant dû supérieur au montant total
    contract = Contract(amount_total=100, amount_due=150)
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        contract._validate_amounts()
    
    # Vérifier le message d'erreur
    assert "ne peut pas être supérieur au montant total" in str(excinfo.value).lower()


def test_contract_validate_team_contact_valid(monkeypatch):
    """Test de validation d'un contact d'équipe valide"""
    # Utiliser MockRole et MockUser de conftest
    role = MockRole("management", 2)
    user = MockUser(2, "manager", "manager@example.com", "Manager", "User", "0123456789", role)
    
    # Simuler la méthode save pour éviter l'accès à la base de données
    monkeypatch.setattr('epicevents.models.contract.Contract.save', lambda self: None)
    
    # Simuler User.get pour retourner notre utilisateur
    monkeypatch.setattr('epicevents.models.user.User.get', lambda *args, **kwargs: user)
    
    # Créer un contrat avec un contact valide
    contract = Contract(team_contact_id=user)
    
    # Appeler la méthode de validation
    contract._validate_team_contact()
    
    # Aucune exception ne devrait être levée


def test_contract_validate_team_contact_invalid_role(monkeypatch):
    """Test de validation d'un contact d'équipe avec un rôle invalide"""
    
    # Simuler la méthode save pour éviter l'accès à la base de données
    def mock_save(self):
        pass
    
    # Créer des classes mock
    class MockRole:
        def __init__(self, name):
            self.name = name
    
    class MockUser:
        def __init__(self):
            self.role = MockRole("sales")  # Rôle invalide pour un contrat
    
    # Créer un mock pour User.get
    def mock_get(*args, **kwargs):
        return MockUser()
    
    # Appliquer les patches
    monkeypatch.setattr('epicevents.models.contract.Contract.save', mock_save)
    monkeypatch.setattr('epicevents.models.user.User.get', mock_get)
    
    # Créer un contrat avec un contact invalide
    contract = Contract(team_contact_id=MockUser())
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        contract._validate_team_contact()
    
    # Vérifier le message d'erreur
    assert "rôle de 'gestionnaire'" in str(excinfo.value).lower()


def test_contract_get_data(monkeypatch, mock_customer):
    """Test de la méthode get_data de Contract"""
    # Utiliser monkeypatch pour remplacer la méthode get de Customer
    monkeypatch.setattr("epicevents.models.customer.Customer.get", lambda *args, **kwargs: mock_customer)

    # Créer une instance de contrat
    contract = Contract()
    contract.id = 1
    contract.customer = mock_customer
    contract.signed = True
    contract.amount_total = 1000.0
    contract.amount_due = 500.0
    contract.date_created = datetime(2023, 1, 1, 12, 0, 0)
    contract.date_updated = datetime(2023, 1, 2, 12, 0, 0)
    contract.team_contact_id = None

    # Appeler get_data
    data = contract.get_data()

    # Vérifier les clés essentielles
    assert data['contract_id'] == 1
    assert data['signed'] is True
    assert data['amount_total'] == 1000.0
    assert data['amount_due'] == 500.0
    assert data['date_created'] == datetime(2023, 1, 1, 12, 0, 0)
    assert data['date_updated'] == datetime(2023, 1, 2, 12, 0, 0)
    assert data['customer'] == mock_customer.get_data()
