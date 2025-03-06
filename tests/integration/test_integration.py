import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

# Fixture pour le runner CLI
@pytest.fixture
def runner():
    return CliRunner()

# Fixture pour simuler un utilisateur connecté
@pytest.fixture
def mock_sales_user():
    """Crée un utilisateur admin mock"""
    mock_role = MagicMock()
    mock_role.name = "sales"
    mock_role.id = 1
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "sales"
    mock_user.email = "sales@example.com"
    mock_user.first_name = "Sales"
    mock_user.last_name = "User"
    mock_user.phone = "0123456789"
    mock_user.role = mock_role
    
    return mock_user

# Test d'intégration basique du workflow d'authentification
@patch('epicevents.permissions.auth.PasswordHasher.verify', return_value=True)
@patch('epicevents.permissions.auth.generate_token', return_value="fake_token")
@patch('epicevents.permissions.auth.welcome_user')
def test_auth_workflow(mock_welcome, mock_generate_token, mock_verify, runner, mock_sales_user, mock_admin_user):
    """Test simplifié du workflow d'authentification"""
    from epicevents.cli.users import app as users_app

    # Patcher User.get pour retourner un utilisateur factice
    with patch('epicevents.permissions.auth.User.get', return_value=mock_sales_user):
        # Exécuter la commande login
        result_login = runner.invoke(users_app, ["login", "-u", "admin", "-p", "password"])

    # Vérifier que l’authentification a réussi
    assert result_login.exit_code == 0
    assert "connecté en tant que" in result_login.output.lower()

    # Exécuter la commande logout avec utilisateur connecté
    with patch('epicevents.permissions.auth.is_logged', return_value=mock_admin_user):
        with patch('epicevents.permissions.auth.check_auth', return_value=True):
            result_logout = runner.invoke(users_app, ["logout"])

    # Vérifier que le logout a réussi
    assert result_logout.exit_code == 0

# Test d'intégration simplifié pour les commandes utilisateur
@patch('epicevents.cli.users.User')
def test_user_commands_integration(mock_user_model, mock_admin_user, runner):
    """Test simplifié des commandes utilisateur"""
    from epicevents.cli.users import app as users_app
    
    # Simuler que l'utilisateur est connecté avec des droits admin
    with patch('epicevents.permissions.auth.is_logged', return_value=mock_admin_user):
        with patch('epicevents.permissions.auth.check_auth', return_value=True):
            # Test de la commande list
            result_list = runner.invoke(users_app, ["list"])
            assert result_list.exit_code == 0
            
            # Test de la commande read
            # Configurer le mock pour get_or_none
            mock_user_model.get_or_none.return_value = mock_admin_user
            
            # Exécuter la commande
            result_read = runner.invoke(users_app, ["read", "1"])
            assert result_read.exit_code == 0