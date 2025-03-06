import pytest
from unittest.mock import patch, MagicMock
import datetime
from peewee import DoesNotExist, IntegrityError, DatabaseError

# Tests pour le modèle Company
@patch('epicevents.models.company.Company.save')
def test_company_validate_name_valid(mock_save):
    """Test de validation d'un nom d'entreprise valide"""
    from epicevents.models.company import Company
    
    # Créer une entreprise avec un nom valide
    company = Company(name="Valid Company Name")
    
    # Appeler la méthode de validation
    company._validate_name()
    
    # Aucune exception ne devrait être levée


@patch('epicevents.models.company.Company.save')
def test_company_validate_name_empty(mock_save):
    """Test de validation d'un nom d'entreprise vide"""
    from epicevents.models.company import Company
    
    # Créer une entreprise avec un nom vide
    company = Company(name="")
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        company._validate_name()
    
    # Vérifier le message d'erreur
    print(f"{str(excinfo.value)}")
    assert "ne peut pas être vide." in str(excinfo.value).lower()


# Tests pour le modèle Contract
@patch('epicevents.models.contract.Contract.save')
def test_contract_validate_amounts_valid(mock_save):
    """Test de validation des montants valides d'un contrat"""
    from epicevents.models.contract import Contract
    
    # Créer un contrat avec des montants valides
    contract = Contract(amount_total=1000, amount_due=500)
    
    # Appeler la méthode de validation
    contract._validate_amounts()
    
    # Aucune exception ne devrait être levée


@patch('epicevents.models.contract.Contract.save')
def test_contract_validate_amounts_negative_total(mock_save):
    """Test de validation d'un montant total négatif"""
    from epicevents.models.contract import Contract
    
    # Créer un contrat avec un montant total négatif
    contract = Contract(amount_total=-100, amount_due=50)
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        contract._validate_amounts()
    
    # Vérifier le message d'erreur
    assert "ne peut pas être inférieur à zéro" in str(excinfo.value).lower()


@patch('epicevents.models.contract.Contract.save')
def test_contract_validate_amounts_due_higher_than_total(mock_save):
    """Test de validation d'un montant dû supérieur au montant total"""
    from epicevents.models.contract import Contract
    
    # Créer un contrat avec un montant dû supérieur au montant total
    contract = Contract(amount_total=100, amount_due=150)
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        contract._validate_amounts()
    
    # Vérifier le message d'erreur
    assert "ne peut pas être supérieur au montant total" in str(excinfo.value).lower()


@patch('epicevents.models.contract.Contract.save')
def test_contract_validate_team_contact_valid(mock_save):
    """Test de validation d'un contact d'équipe valide"""
    from epicevents.models.contract import Contract
    from epicevents.models.user import User
    from epicevents.models.role import Role
    
    # Créer un mock pour Role et User
    mock_role = MagicMock(spec=Role)
    mock_role.name = "management"
    
    mock_user = MagicMock(spec=User)
    mock_user.role = mock_role
    
    # Créer un contrat avec un contact valide
    contract = Contract(team_contact_id=mock_user)
    
    # Patcher la méthode get pour retourner notre mock
    with patch('epicevents.models.user.User.get', return_value=mock_user):
        # Appeler la méthode de validation
        contract._validate_team_contact()
    
    # Aucune exception ne devrait être levée


@patch('epicevents.models.contract.Contract.save')
def test_contract_validate_team_contact_invalid_role(mock_save):
    """Test de validation d'un contact d'équipe avec un rôle invalide"""
    from epicevents.models.contract import Contract
    from epicevents.models.user import User
    from epicevents.models.role import Role
    
    # Créer un mock pour Role et User
    mock_role = MagicMock(spec=Role)
    mock_role.name = "sales"  # Rôle invalide pour un contrat
    
    mock_user = MagicMock(spec=User)
    mock_user.role = mock_role
    
    # Créer un contrat avec un contact invalide
    contract = Contract(team_contact_id=mock_user)
    
    # Patcher la méthode get pour retourner notre mock
    with patch('epicevents.models.user.User.get', return_value=mock_user):
        # La validation devrait lever une ValueError
        with pytest.raises(ValueError) as excinfo:
            contract._validate_team_contact()
    
    # Vérifier le message d'erreur
    assert "rôle de 'gestionnaire'" in str(excinfo.value).lower()


# Tests pour le modèle Customer
@patch('epicevents.models.customer.Customer.save')
def test_customer_validate_email_valid(mock_save):
    """Test de validation d'un email valide"""
    from epicevents.models.customer import Customer
    
    # Créer un client avec un email valide
    customer = Customer(email="valid.email@example.com")
    
    # Appeler la méthode de validation
    customer._validate_email()
    
    # Aucune exception ne devrait être levée


@patch('epicevents.models.customer.Customer.save')
def test_customer_validate_email_invalid(mock_save):
    """Test de validation d'un email invalide"""
    from epicevents.models.customer import Customer
    
    # Créer un client avec un email invalide
    customer = Customer(email="invalid-email")
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        customer._validate_email()
    
    # Vérifier le message d'erreur
    assert "email valide" in str(excinfo.value).lower()


@patch('epicevents.models.customer.Customer.save')
def test_customer_validate_phone_valid(mock_save):
    """Test de validation d'un numéro de téléphone valide"""
    from epicevents.models.customer import Customer
    
    # Créer un client avec un numéro de téléphone valide
    customer = Customer(phone="0123456789")
    
    # Appeler la méthode de validation
    customer._validate_phone()
    
    # Aucune exception ne devrait être levée


@patch('epicevents.models.customer.Customer.save')
def test_customer_validate_phone_invalid(mock_save):
    """Test de validation d'un numéro de téléphone invalide"""
    from epicevents.models.customer import Customer
    
    # Créer un client avec un numéro de téléphone invalide
    customer = Customer(phone="not-a-phone")
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        customer._validate_phone()
    
    # Vérifier le message d'erreur
    assert "téléphone valide" in str(excinfo.value).lower()


# Tests pour le modèle Event
@patch('epicevents.models.event.Event.save')
def test_event_validate_event_date_valid_future(mock_save):
    """Test de validation d'une date d'événement valide dans le futur"""
    from epicevents.models.event import Event
    
    # Créer un événement avec une date future
    future_date = datetime.datetime.now() + datetime.timedelta(days=30)
    event = Event(event_date=future_date)
    
    # Appeler la méthode de validation
    event._validate_event_date()
    
    # Aucune exception ne devrait être levée


@patch('epicevents.models.event.Event.save')
def test_event_validate_event_date_past(mock_save):
    """Test de validation d'une date d'événement dans le passé"""
    from epicevents.models.event import Event
    
    # Créer un événement avec une date passée
    past_date = datetime.datetime.now() - datetime.timedelta(days=1)
    event = Event(event_date=past_date)
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        event._validate_event_date()
    
    # Vérifier le message d'erreur
    assert "ne peut pas être dans le passé" in str(excinfo.value).lower()


@patch('epicevents.models.event.Event.save')
def test_event_validate_attendees_valid(mock_save):
    """Test de validation d'un nombre de participants valide"""
    from epicevents.models.event import Event
    
    # Créer un événement avec un nombre de participants valide
    event = Event(attendees=100)
    
    # Appeler la méthode de validation
    event._validate_attendees()
    
    # Aucune exception ne devrait être levée


@patch('epicevents.models.event.Event.save')
def test_event_validate_attendees_invalid(mock_save):
    """Test de validation d'un nombre de participants invalide"""
    from epicevents.models.event import Event
    
    # Créer un événement avec un nombre de participants invalide
    event = Event(attendees=-10)
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        event._validate_attendees()
    
    # Vérifier le message d'erreur
    assert "entier positif" in str(excinfo.value).lower()


# Tests pour le modèle User
@patch('epicevents.models.user.User.save')
def test_user_validate_role_valid(mock_save):
    """Test de validation d'un rôle valide"""
    from epicevents.models.user import User
    from epicevents.models.role import Role
    
    # Créer un mock pour Role
    mock_role = MagicMock(spec=Role)
    mock_role.name = "admin"
    
    # Créer un utilisateur avec un rôle valide
    user = User(role=mock_role)
    
    # Appeler la méthode de validation
    user._validate_role()
    
    # Aucune exception ne devrait être levée


@patch('epicevents.models.user.User.save')
def test_user_validate_role_invalid(mock_save):
    """Test de validation d'un rôle invalide"""
    from epicevents.models.user import User
    from epicevents.models.role import Role
    
    # Créer un mock pour Role
    mock_role = MagicMock(spec=Role)
    mock_role.name = "invalid_role"
    
    # Créer un utilisateur avec un rôle invalide
    user = User(role=mock_role)
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        user._validate_role()
    
    # Vérifier le message d'erreur
    assert "rôle doit être" in str(excinfo.value).lower()


@patch('epicevents.models.user.User.save')
@patch('epicevents.models.user.ph')
def test_user_verify_password_correct(mock_ph, mock_save):
    """Test de vérification d'un mot de passe correct"""
    from epicevents.models.user import User
    
    # Simuler une vérification correcte
    mock_ph.verify.return_value = True
    
    user = User(password="hashed_password")
    
    # Vérifier le mot de passe
    result = user.verify_password("correct_password")
    
    assert result is True
    mock_ph.verify.assert_called_once_with("hashed_password", "correct_password")


@patch('epicevents.models.user.User.save')
@patch('epicevents.models.user.ph')
def test_user_verify_password_incorrect(mock_ph, mock_save):
    """Test de vérification d'un mot de passe incorrect"""
    from epicevents.models.user import User
    from argon2.exceptions import VerifyMismatchError
    
    # Simuler une vérification incorrecte
    mock_ph.verify.side_effect = VerifyMismatchError
    
    user = User(password="hashed_password")
    
    # Vérifier le mot de passe
    result = user.verify_password("incorrect_password")
    
    assert result is False
    mock_ph.verify.assert_called_once_with("hashed_password", "incorrect_password")
