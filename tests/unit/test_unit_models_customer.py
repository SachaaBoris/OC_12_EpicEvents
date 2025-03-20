import pytest
from peewee import IntegrityError, DoesNotExist, DatabaseError
from datetime import datetime, timezone, timedelta
from epicevents.models.customer import Customer
from tests.conftest import MockRole, MockUser, MockCompany


# Tests pour Customer
def test_customer_save(monkeypatch):
    """Test de la méthode save() de Customer"""
    mock_company = MockCompany(1, "ACME")
    mock_user = MockUser(3, "sales", "sales@example.com", "Sales", "User", "0123456789", 
                         MockRole("sales", 3))
    
    # Créer un compteur d'appels
    calls = {
        'base_save': 0,
        'validate_name': 0,
        'validate_email': 0,
        'validate_phone': 0,
        'validate_date': 0,
        'validate_team_contact': 0
    }
    
    # Fonctions de remplacement
    def mock_base_save(self):
        calls['base_save'] += 1
    
    def mock_validate_name(self):
        calls['validate_name'] += 1
    
    def mock_validate_email(self):
        calls['validate_email'] += 1
    
    def mock_validate_phone(self):
        calls['validate_phone'] += 1
    
    def mock_validate_date(self):
        calls['validate_date'] += 1
    
    def mock_validate_team_contact(self):
        calls['validate_team_contact'] += 1
    
    # Appliquer les patches
    monkeypatch.setattr('epicevents.models.customer.BaseModel.save', mock_base_save)
    monkeypatch.setattr(Customer, '_validate_name', mock_validate_name)
    monkeypatch.setattr(Customer, '_validate_email', mock_validate_email)
    monkeypatch.setattr(Customer, '_validate_phone', mock_validate_phone)
    monkeypatch.setattr(Customer, '_validate_date', mock_validate_date)
    monkeypatch.setattr(Customer, '_validate_team_contact', mock_validate_team_contact)
    
    # Créer une instance de customer
    customer = Customer(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="0123456789",
        company=mock_company,
        team_contact_id=mock_user
    )
    
    # Appeler la méthode save()
    customer.save()
    
    # Vérifier que les méthodes ont été appelées
    assert calls['validate_name'] == 1
    assert calls['validate_email'] == 1
    assert calls['validate_phone'] == 1
    assert calls['validate_date'] == 1
    assert calls['validate_team_contact'] == 1
    assert calls['base_save'] == 1


def test_customer_validate_name():
    """Test de la méthode _validate_name de Customer"""
    # Créer une instance avec first_name vide
    customer = Customer(first_name="", last_name="Doe")
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        customer._validate_name()
    
    # Vérifier le message d'erreur
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


def test_customer_validate_name():
    """Test de la méthode _validate_name de Customer"""
    from epicevents.models.customer import Customer
    
    # Créer une instance avec first_name vide
    customer = Customer(first_name="", last_name="Doe")
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        customer._validate_name()
    
    # Vérifier le message d'erreur
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
    
    # Créer une instance avec une date invalide
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


def test_customer_validate_email(monkeypatch):
    """Test complet de la méthode _validate_email de Customer"""
    
    # Simuler la méthode save pour éviter l'accès à la base de données
    def mock_save(self):
        pass
    
    monkeypatch.setattr('epicevents.models.customer.Customer.save', mock_save)
    
    # Test avec un email valide
    customer = Customer()
    customer.email = "test@example.com"
    customer._validate_email()  # Ne devrait pas lever d'exception
    
    # Test avec différents emails invalides
    invalid_emails = [
        "",                  # Email vide
        "test",              # Sans @ ni domaine
        "test@",             # Sans domaine
        "test@domain",       # Sans extension
        "@domain.com",       # Sans nom d'utilisateur
        "test@domain..com",  # Double point
        "test@@domain.com"   # Double @
    ]
    
    for invalid_email in invalid_emails:
        customer.email = invalid_email
        with pytest.raises(ValueError) as excinfo:
            customer._validate_email()
        assert "email valide" in str(excinfo.value).lower()


def test_customer_validate_phone(monkeypatch):
    """Test complet de la méthode _validate_phone de Customer"""
    
    # Simuler la méthode save pour éviter l'accès à la base de données
    def mock_save(self):
        pass
    
    monkeypatch.setattr('epicevents.models.customer.Customer.save', mock_save)
    
    # Test avec des numéros de téléphone valides
    valid_phones = [
        "0123456789",           # 10 chiffres sans préfixe
        "+33123456789",         # Format international
        "01234567890",          # 11 chiffres
        "0123456789012345",     # 16 chiffres
        "01234567890123456789"  # 20 chiffres (max)
    ]
    
    customer = Customer()
    for valid_phone in valid_phones:
        customer.phone = valid_phone
        customer._validate_phone()  # Ne devrait pas lever d'exception
    
    # Test avec des numéros de téléphone invalides
    invalid_phones = [
        "",                     # Vide
        "123",                  # Trop court (moins de 7 chiffres)
        "abcdefghij",           # Lettres au lieu de chiffres
        "123-456-7890",         # Avec tirets
        "123 456 7890",         # Avec espaces
        "012345678901234567890" # Trop long (plus de 20 chiffres)
    ]
    
    for invalid_phone in invalid_phones:
        customer.phone = invalid_phone
        with pytest.raises(ValueError) as excinfo:
            customer._validate_phone()
        assert "téléphone valide" in str(excinfo.value).lower()


def test_customer_validate_team_contact(monkeypatch):
    """Test de la méthode _validate_team_contact de Customer"""
    # Utiliser les mocks du conftest
    valid_role = MockRole("sales", 3)
    invalid_role = MockRole("support", 4)
    
    valid_user = MockUser(3, "sales", "sales@example.com", "Sales", "User", "0123456789", valid_role)
    invalid_user = MockUser(4, "support", "support@example.com", "Support", "User", "0123456789", invalid_role)
    
    # Variables pour suivre les appels
    call_count = {'get': 0}
    
    # Fonction qui simule User.get
    def mock_get(*args, **kwargs):
        call_count['get'] += 1
        # Premier appel: retourner l'utilisateur valide
        if call_count['get'] == 1:
            return valid_user
        # Deuxième appel: retourner l'utilisateur invalide
        else:
            return invalid_user
    
    # Simuler que User.get retourne notre utilisateur mock
    monkeypatch.setattr('epicevents.models.user.User.get', mock_get)
    
    # Test avec un rôle valide
    customer = Customer(team_contact_id=valid_user)
    customer._validate_team_contact()  # Ne devrait pas lever d'exception
    
    # Test avec un rôle invalide
    customer = Customer(team_contact_id=invalid_user)
    with pytest.raises(ValueError) as excinfo:
        customer._validate_team_contact()
    
    # Vérifier le message d'erreur
    assert "rôle de 'commercial'" in str(excinfo.value).lower()


def test_customer_get_data(monkeypatch):
    """Test de la méthode get_data de Customer"""
    # Créer un mock pour Company du conftest
    company_mock = MockCompany(1, "ACME Corp")
    company_mock.id = 5  # Ajouter un ID
    
    # Créer une instance de customer
    customer = Customer()
    customer.id = 1
    customer.first_name = "John"
    customer.last_name = "Doe"
    customer.email = "john@example.com"
    customer.phone = "0123456789"
    
    # Créer un descripteur de propriété pour la propriété company
    class CompanyProperty:
        def __get__(self, instance, owner):
            return company_mock
    
    # Remplacer le descripteur de la propriété company
    monkeypatch.setattr(Customer, 'company', CompanyProperty())
    
    # Configurer les dates
    customer.date_created = datetime.now()
    customer.date_updated = datetime.now()
    customer.team_contact_id = None
    
    # Appeler get_data
    data = customer.get_data()
    
    # Vérifier les champs essentiels
    assert data['customer_id'] == 1
    assert data['first_name'] == "John"
    assert data['last_name'] == "Doe"
    assert data['email'] == "john@example.com"
    assert data['company'] == "ACME Corp"
