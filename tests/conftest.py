import pytest
from unittest.mock import MagicMock
from typer.testing import CliRunner
import os
import datetime

# Fixture pour le runner CLI
@pytest.fixture
def runner():
    return CliRunner()

# Fixture pour simuler un utilisateur admin
@pytest.fixture
def mock_admin_user():
    """Crée un utilisateur admin mock"""
    mock_role = MagicMock()
    mock_role.name = "admin"
    mock_role.id = 1
    
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "admin"
    mock_user.email = "admin@example.com"
    mock_user.first_name = "Admin"
    mock_user.last_name = "User"
    mock_user.phone = "0123456789"
    mock_user.role = mock_role
    
    return mock_user

# Fixture pour simuler un utilisateur commercial
@pytest.fixture
def mock_sales_user():
    """Crée un utilisateur commercial mock"""
    mock_role = MagicMock()
    mock_role.name = "sales"
    mock_role.id = 3
    
    mock_user = MagicMock()
    mock_user.id = 3
    mock_user.username = "sales"
    mock_user.email = "sales@example.com"
    mock_user.first_name = "Sales"
    mock_user.last_name = "User"
    mock_user.phone = "0123456789"
    mock_user.role = mock_role
    
    return mock_user

# Fixture pour simuler un client
@pytest.fixture
def mock_customer():
    """Crée un client mock"""
    mock_company = MagicMock()
    mock_company.name = "ACME"
    
    mock_sales_user = MagicMock()
    mock_sales_user.id = 3
    mock_sales_user.username = "sales"
    
    mock_customer = MagicMock()
    mock_customer.id = 1
    mock_customer.first_name = "John"
    mock_customer.last_name = "Doe"
    mock_customer.email = "john@example.com"
    mock_customer.phone = "0123456789"
    mock_customer.company = mock_company
    mock_customer.team_contact_id = mock_sales_user
    mock_customer.date_created = datetime.datetime.now()
    mock_customer.date_updated = datetime.datetime.now()
    
    return mock_customer

# Fixture pour nettoyer l'environnement après les tests
@pytest.fixture(autouse=True)
def clean_environment():
    # Sauvegarder l'environnement original
    original_environ = dict(os.environ)
    
    # S'assurer que le secret JWT est défini pour les tests
    os.environ["SECRET_KEY"] = "testsecretkey"
    os.environ["TOKEN_EXP"] = "24"
    
    yield
    
    # Restaurer l'environnement original
    os.environ.clear()
    os.environ.update(original_environ)

# Fixture pour simuler l'authentification
@pytest.fixture
def mock_authenticated():
    """Simule un utilisateur authentifié"""
    from unittest.mock import patch
    from epicevents.permissions.auth import is_logged, check_auth
    
    # Utiliser le contexte de patch pour simuler l'authentification
    with patch('epicevents.permissions.auth.is_logged') as mock_is_logged:
        with patch('epicevents.permissions.auth.check_auth') as mock_check_auth:
            # Configurer les mocks pour simuler un utilisateur authentifié
            mock_is_logged.return_value = True
            mock_check_auth.return_value = True
            
            yield (mock_is_logged, mock_check_auth)