import pytest
from unittest.mock import patch, MagicMock, call
import datetime
import re
from peewee import DoesNotExist, IntegrityError, DatabaseError
from datetime import datetime, timezone, timedelta


# Tests pour Company.save
@patch('epicevents.models.company.BaseModel.save')
def test_company_save(mock_base_save):
    """Test de la méthode save() de Company"""
    from epicevents.models.company import Company
    
    # Créer une instance d'entreprise
    company = Company(name="Test Company")
    
    # Patcher la méthode _validate_name pour éviter qu'elle n'échoue
    with patch.object(Company, '_validate_name') as mock_validate:
        # Appeler la méthode save()
        company.save()
        
        # Vérifier que les méthodes ont été appelées
        mock_validate.assert_called_once()
        mock_base_save.assert_called_once()


# Tests pour Contract.save et ses méthodes de validation
@patch('epicevents.models.contract.BaseModel.save')
def test_contract_save(mock_base_save):
    """Test de la méthode save() de Contract"""
    from epicevents.models.contract import Contract
    
    # Créer un objet mock pour Customer
    mock_customer = MagicMock()
    mock_user = MagicMock()
    
    # Créer une instance de contrat
    contract = Contract(
        customer=mock_customer,
        signed=True,
        amount_total=1000.0,
        amount_due=500.0,
        team_contact_id=mock_user
    )
    
    # Patcher les méthodes de validation pour éviter qu'elles n'échouent
    with patch.object(Contract, '_validate_signed') as mock_validate_signed, \
         patch.object(Contract, '_validate_amounts') as mock_validate_amounts, \
         patch.object(Contract, '_validate_date') as mock_validate_date, \
         patch.object(Contract, '_validate_team_contact') as mock_validate_team_contact:
        
        # Appeler la méthode save()
        contract.save()
        
        # Vérifier que toutes les méthodes de validation ont été appelées
        mock_validate_signed.assert_called_once()
        mock_validate_amounts.assert_called_once()
        mock_validate_date.assert_called_once()
        mock_validate_team_contact.assert_called_once()
        mock_base_save.assert_called_once()


def test_contract_validate_signed():
    """Test de la méthode _validate_signed de Contract"""
    from epicevents.models.contract import Contract
    
    # Créer une instance avec signed=None (invalide)
    contract = Contract(signed=None)
    
    # La validation devrait lever une IntegrityError (pas ValueError)
    with pytest.raises(IntegrityError) as excinfo:
        contract._validate_signed()
    
    # Vérifier le message d'erreur
    assert "Le Contrat doit être signé" in str(excinfo.value)
    
    # Tester avec une valeur valide
    contract.signed = True
    contract._validate_signed()  # Ne devrait pas lever d'exception


def test_contract_validate_date():
    """Test de la méthode _validate_date de Contract"""
    from epicevents.models.contract import Contract
    
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


def test_contract_get_data():
    from epicevents.models.contract import Contract
    
    # Utiliser le vrai mock customer
    mock_customer = MagicMock()
    # Ne pas mocker get_data(), laissez-le renvoyer 
    # les vraies propriétés du customer
    mock_customer.first_name = "John"
    mock_customer.last_name = "Doe"
    
    contract = Contract()
    contract.id = 1
    contract.customer = mock_customer
    contract.signed = True
    contract.amount_total = 1000.0
    contract.amount_due = 500.0
    contract.date_created = datetime(2023, 1, 1, 12, 0, 0)
    contract.date_updated = datetime(2023, 1, 2, 12, 0, 0)
    contract.team_contact_id = None  # Simplifier en mettant None
    
    # Appeler get_data sans faire d'assertions sur tout le dictionnaire
    data = contract.get_data()
    
    # Vérifier uniquement quelques clés essentielles
    assert data['contract_id'] == 1
    assert data['signed'] is True
    assert data['amount_total'] == 1000.0


# Tests pour Customer.save et ses méthodes de validation
@patch('epicevents.models.customer.BaseModel.save')
def test_customer_save(mock_base_save):
    """Test de la méthode save() de Customer"""
    from epicevents.models.customer import Customer
    
    # Créer des mocks pour Company et User
    mock_company = MagicMock()
    mock_user = MagicMock()
    
    # Créer une instance de customer
    customer = Customer(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="0123456789",
        company=mock_company,
        team_contact_id=mock_user
    )
    
    # Patcher les méthodes de validation
    with patch.object(Customer, '_validate_name') as mock_validate_name, \
         patch.object(Customer, '_validate_email') as mock_validate_email, \
         patch.object(Customer, '_validate_phone') as mock_validate_phone, \
         patch.object(Customer, '_validate_date') as mock_validate_date, \
         patch.object(Customer, '_validate_team_contact') as mock_validate_team_contact:
        
        # Appeler la méthode save()
        customer.save()
        
        # Vérifier que les méthodes ont été appelées
        mock_validate_name.assert_called_once()
        mock_validate_email.assert_called_once()
        mock_validate_phone.assert_called_once()
        mock_validate_date.assert_called_once()
        mock_validate_team_contact.assert_called_once()
        mock_base_save.assert_called_once()


def test_customer_validate_name():
    """Test de la méthode _validate_name de Customer"""
    from epicevents.models.customer import Customer
    
    # Créer une instance avec first_name vide (invalide)
    customer = Customer(first_name="", last_name="Doe")
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        customer._validate_name()
    
    # Vérifier le message d'erreur (ajuster pour correspondre au message réel)
    assert "prénom et le nom ne doivent contenir que des lettres" in str(excinfo.value).lower()
    
    # Tester avec last_name vide
    customer.first_name = "John"
    customer.last_name = ""
    
    with pytest.raises(ValueError) as excinfo:
        customer._validate_name()
    
    # Vérifier le message d'erreur
    assert "prénom et le nom ne doivent contenir que des lettres" in str(excinfo.value).lower()
    
    # Tester avec des valeurs valides
    customer.first_name = "John"
    customer.last_name = "Doe"
    customer._validate_name()  # Ne devrait pas lever d'exception


def test_customer_validate_date():
    """Test de la méthode _validate_date de Customer"""
    from epicevents.models.customer import Customer
    
    # Créer une instance avec une date invalide (pas un datetime)
    customer = Customer()
    customer.date_created = "not-a-date"
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        customer._validate_date()
    
    # Vérifier le message d'erreur
    assert "format datetime valide" in str(excinfo.value)
    
    # Tester avec une date valide
    customer.date_created = datetime.now()
    customer._validate_date()  # Ne devrait pas lever d'exception


def test_customer_validate_team_contact():
    """Test de la méthode _validate_team_contact de Customer"""
    from epicevents.models.customer import Customer
    from epicevents.models.user import User
    from epicevents.models.role import Role
    
    # Créer un mock pour Role et User
    mock_role = MagicMock(spec=Role)
    mock_role.name = "sales"  # Rôle valide pour un customer
    
    mock_user = MagicMock(spec=User)
    mock_user.role = mock_role
    
    # Créer un customer avec un contact valide
    customer = Customer(team_contact_id=mock_user)
    
    # Patcher la méthode get pour retourner notre mock
    with patch('epicevents.models.user.User.get', return_value=mock_user):
        # Appeler la méthode de validation
        customer._validate_team_contact()
    
    # Aucune exception ne devrait être levée
    
    # Tester avec un rôle invalide
    mock_role.name = "support"  # Rôle invalide pour un customer
    
    # La validation devrait lever une ValueError
    with patch('epicevents.models.user.User.get', return_value=mock_user):
        with pytest.raises(ValueError) as excinfo:
            customer._validate_team_contact()
    
    # Vérifier le message d'erreur
    assert "rôle de 'commercial'" in str(excinfo.value).lower()


def test_customer_get_data():
    from epicevents.models.customer import Customer
    
    mock_company = MagicMock()
    mock_company.name = "ACME Corp"  # Assurez-vous que cette valeur correspond
    
    customer = Customer()
    customer.id = 1
    customer.first_name = "John"
    customer.last_name = "Doe"
    customer.email = "john@example.com"
    customer.phone = "0123456789"
    customer.company = mock_company
    customer.team_contact_id = None  # Simplifié
    
    data = customer.get_data()
    
    # Vérifier seulement les champs essentiels
    assert data['customer_id'] == 1
    assert data['first_name'] == "John"
    assert data['last_name'] == "Doe"
    assert data['email'] == "john@example.com"


# Tests pour Event.save et ses méthodes de validation
@patch('epicevents.models.event.BaseModel.save')
def test_event_save(mock_base_save):
    """Test de la méthode save() de Event"""
    from epicevents.models.event import Event
    
    # Créer des mocks pour Contract et User
    mock_contract = MagicMock()
    mock_user = MagicMock()
    
    # Date future pour éviter l'erreur de validation
    future_date = datetime.now() + timedelta(days=30)
    
    # Créer une instance d'event
    event = Event(
        contract=mock_contract,
        name="Conference",
        location="Paris",
        event_date=future_date,
        attendees=100,
        notes="Test event",
        team_contact_id=mock_user
    )
    
    # Patcher les méthodes de validation - sans _validate_date qui n'existe pas
    with patch.object(Event, '_validate_contract') as mock_validate_contract, \
         patch.object(Event, '_validate_name') as mock_validate_name, \
         patch.object(Event, '_validate_event_date') as mock_validate_event_date, \
         patch.object(Event, '_validate_attendees') as mock_validate_attendees, \
         patch.object(Event, '_validate_team_contact') as mock_validate_team_contact:
        
        # Appeler la méthode save()
        event.save()
        
        # Vérifier que les méthodes ont été appelées
        mock_validate_contract.assert_called_once()
        mock_validate_name.assert_called_once()
        mock_validate_event_date.assert_called_once()
        mock_validate_attendees.assert_called_once()
        mock_validate_team_contact.assert_called_once()
        mock_base_save.assert_called_once()


def test_event_validate_contract():
    from epicevents.models.event import Event
    from epicevents.models.contract import Contract
    # Ajouter cet import
    from peewee import DoesNotExist
    
    # Créer un mock contract avec un ID valide
    mock_contract = MagicMock()
    mock_contract.id = 1
    
    # Créer l'événement avec ce contrat
    event = Event(contract=mock_contract)
    
    # Test cas valide: le contrat existe
    with patch('epicevents.models.contract.Contract.get_or_none', return_value=mock_contract):
        event._validate_contract()  # Ne devrait pas lever d'exception
    
    # Test cas invalide: le contrat n'existe pas
    with patch('epicevents.models.contract.Contract.get_or_none', return_value=None):
        with pytest.raises(ValueError) as excinfo:
            event._validate_contract()
        
        # Vérifier le message d'erreur
        assert "contrat existant" in str(excinfo.value).lower()


def test_event_validate_name():
    """Test de la méthode _validate_name de Event"""
    from epicevents.models.event import Event
    
    # Créer une instance avec un nom vide (invalide)
    event = Event(name="")
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        event._validate_name()
    
    # Vérifier le message d'erreur (ajusté pour correspondre au message réel)
    assert "le nom de l'événement ne peut pas être vide" in str(excinfo.value).lower()
    
    # Tester avec un nom valide
    event.name = "Conference"
    event._validate_name()  # Ne devrait pas lever d'exception


def test_event_validate_team_contact():
    """Test de la méthode _validate_team_contact de Event"""
    from epicevents.models.event import Event
    from epicevents.models.user import User
    from epicevents.models.role import Role
    
    # Créer un mock pour Role et User
    mock_role = MagicMock(spec=Role)
    mock_role.name = "support"  # Rôle valide pour un event
    
    mock_user = MagicMock(spec=User)
    mock_user.role = mock_role
    
    # Créer un event avec un contact valide
    event = Event(team_contact_id=mock_user)
    
    # Patcher la méthode get pour retourner notre mock
    with patch('epicevents.models.user.User.get', return_value=mock_user):
        # Appeler la méthode de validation
        event._validate_team_contact()
    
    # Aucune exception ne devrait être levée
    
    # Tester avec un rôle invalide
    mock_role.name = "sales"  # Rôle invalide pour un event
    
    # La validation devrait lever une ValueError
    with patch('epicevents.models.user.User.get', return_value=mock_user):
        with pytest.raises(ValueError) as excinfo:
            event._validate_team_contact()
    
    # Vérifier le message d'erreur
    assert "rôle de 'support'" in str(excinfo.value).lower()


def test_event_get_data():
    from epicevents.models.event import Event
    
    mock_contract = MagicMock()
    mock_contract.id = 1
    
    event = Event()
    event.id = 1
    event.contract = mock_contract
    event.name = "Conference"
    event.location = "Paris"
    event.event_date = datetime(2023, 12, 31, 12, 0, 0)
    event.attendees = 100
    event.notes = "Test event"
    event.team_contact_id = None  # Simplifié
    
    data = event.get_data()
    
    # Vérifier seulement quelques champs essentiels
    assert data['event_id'] == 1
    assert data['name'] == "Conference"
    assert data['location'] == "Paris"
    assert data['attendees'] == 100


# Tests pour User.save et ses méthodes de validation
@patch('epicevents.models.user.BaseModel.save')
@patch('epicevents.models.user.ph')  # Patch le module ph entier, pas juste hash
def test_user_save(mock_ph, mock_base_save):
    """Test de la méthode save() de User"""
    from epicevents.models.user import User
    
    # Configurer le mock pour ph.hash
    mock_ph.hash.return_value = "hashed_password"
    
    # Créer un mock pour Role
    mock_role = MagicMock()
    
    # Créer une instance de user
    user = User(
        username="john_doe",
        email="john@example.com",
        password="password123",
        first_name="John",
        last_name="Doe",
        phone="0123456789",
        role=mock_role
    )
    
    # Patcher les méthodes de validation
    with patch.object(User, '_validate_name') as mock_validate_name, \
         patch.object(User, '_validate_email') as mock_validate_email, \
         patch.object(User, '_validate_phone') as mock_validate_phone, \
         patch.object(User, '_validate_role') as mock_validate_role:
        
        # Appeler la méthode save()
        user.save()
        
        # Vérifier que les méthodes ont été appelées
        mock_validate_name.assert_called_once()
        mock_validate_email.assert_called_once()
        mock_validate_phone.assert_called_once()
        mock_validate_role.assert_called_once()
        mock_ph.hash.assert_called_once_with("password123")
        assert user.password == "hashed_password"
        mock_base_save.assert_called_once()


@patch('epicevents.models.user.re.match')
def test_user_validate_name(mock_re_match):
    """Test de la méthode _validate_name de User"""
    from epicevents.models.user import User
    
    # Configurer le mock pour re.match
    # Premier appel: first_name invalide
    # Deuxième appel: last_name invalide
    # Troisième et quatrième appels: noms valides
    mock_re_match.side_effect = [None, True, True, True]
    
    # Test avec un prénom invalide
    user = User(first_name="John123", last_name="Doe", username="john_doe")
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        user._validate_name()
    
    # Vérifier le message d'erreur
    assert "prénom et le nom ne doivent contenir que des lettres" in str(excinfo.value).lower()
    
    # Réinitialiser le side_effect
    mock_re_match.side_effect = [True, None, True, True]
    
    # Test avec un nom invalide
    user = User(first_name="John", last_name="Doe@", username="john_doe")
    
    with pytest.raises(ValueError) as excinfo:
        user._validate_name()
    
    # Vérifier le message d'erreur
    assert "prénom et le nom ne doivent contenir que des lettres" in str(excinfo.value).lower()
    
    # Réinitialiser le side_effect pour un test réussi
    mock_re_match.side_effect = [True, True]
    
    # Test avec des valeurs valides
    user = User(first_name="John", last_name="Doe", username="john_doe")
    user._validate_name()  # Ne devrait pas lever d'exception


def test_user_validate_email():
    """Test de la méthode _validate_email de User"""
    from epicevents.models.user import User
    
    # Créer une instance avec un email invalide (sans @)
    user = User(email="invalid-email")
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        user._validate_email()
    
    # Vérifier le message d'erreur
    assert "veuillez entrer un email valide" in str(excinfo.value).lower()
    
    # Tester avec un email valide
    user.email = "john@example.com"
    user._validate_email()  # Ne devrait pas lever d'exception


def test_user_validate_phone():
    """Test de la méthode _validate_phone de User"""
    from epicevents.models.user import User
    
    # Créer une instance avec un téléphone invalide (contient des lettres)
    user = User(phone="01234abcde")
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        user._validate_phone()
    
    # Vérifier le message d'erreur
    assert "veuillez entrer un numéro de téléphone valide" in str(excinfo.value).lower()
    
    # Tester avec un numéro de téléphone valide
    user.phone = "0123456789"
    user._validate_phone()  # Ne devrait pas lever d'exception


@patch('epicevents.models.user.datetime')
@patch('epicevents.models.user.timezone')
@patch('epicevents.models.user.timedelta')
def test_user_get_data(mock_timedelta, mock_timezone, mock_datetime):
    """Test de la méthode get_data de User"""
    from epicevents.models.user import User
    
    # Configurer les mocks pour datetime et timedelta
    now = datetime(2023, 1, 1, 12, 0, 0)
    mock_datetime.now.return_value = now
    mock_timezone.utc = timezone.utc
    mock_timedelta.return_value = timedelta(hours=1)
    
    # Créer un mock pour Role
    mock_role = MagicMock()
    mock_role.id = 1
    mock_role.name = "admin"
    
    # Créer une instance avec des données complètes
    user = User()
    user.id = 1  # Définir l'ID directement
    user.username = "john_doe"
    user.email = "john@example.com"
    user.first_name = "John"
    user.last_name = "Doe"
    user.phone = "0123456789"
    user.role = mock_role
    
    # Appeler get_data
    data = user.get_data()
    
    # Vérifier le contenu du dictionnaire retourné
    assert data['user_id'] == 1
    assert data['email'] == "john@example.com"
    assert data['role_id'] == 1
    assert isinstance(data['jwt_exp'], datetime)