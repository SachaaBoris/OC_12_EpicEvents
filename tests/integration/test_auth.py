import pytest
import json
import jwt
import typer
import io
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, mock_open, call
from typer.testing import CliRunner
from epicevents.models.user import User
from epicevents.permissions.auth import generate_token
from epicevents.permissions.auth import verify_token
from epicevents.permissions.auth import remove_token
from epicevents.cli.utils import welcome_user


@patch("epicevents.permissions.auth.generate_token")
@patch("epicevents.permissions.auth.welcome_user")
def test_authenticate_user_successful_mocked(mock_welcome, mock_generate_token):
    """Test de l'authentification réussie avec mocks complets"""
    from epicevents.permissions.auth import authenticate_user
    from epicevents.models.user import User
    
    # Créer un utilisateur mock avec peewee
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.username = "admin"
    mock_user.role = MagicMock()
    mock_user.role.name = "admin"
    
    # Configurer les mocks avec monkeypatch
    with patch("epicevents.permissions.auth.User.get", return_value=mock_user):
        with patch("epicevents.permissions.auth.PasswordHasher.verify", return_value=True):
            # Configurer le mock pour generate_token
            mock_generate_token.return_value = "fake_token"
            
            # Appeler la fonction
            result = authenticate_user("admin", "password")
    
    # Vérifier les résultats
    assert result is not None
    assert result["token"] == "fake_token"
    assert result["user_id"] == 1
    assert result["role"] == "admin"
    
    # Vérifier que welcome_user a été appelé
    mock_welcome.assert_called_once()


@patch("epicevents.permissions.auth.TOKEN_FILE")
def test_remove_token(mock_token_file):
    """Test pour vérifier la fonction remove_token"""
    from epicevents.permissions.auth import remove_token
    
    # Appeler la fonction
    remove_token()
    
    # Vérifier que la méthode unlink a été appelée avec missing_ok=True
    mock_token_file.unlink.assert_called_once_with(missing_ok=True)

@patch("epicevents.permissions.auth.TOKEN_FILE")
def test_token_file_not_exists(mock_token_file):
    """Test pour vérifier le comportement quand le fichier token n'existe pas"""
    from epicevents.permissions.auth import verify_token
    
    # Configurer les mocks
    mock_token_file.exists.return_value = False
    
    # Appeler la fonction
    result = verify_token()
    
    # Vérifier que le résultat est None
    assert result is None


@patch('epicevents.permissions.auth.TOKEN_FILE')
@patch('epicevents.permissions.auth.JWT_SECRET', 'test_secret_key')  # Correction du nom
@patch('epicevents.permissions.auth.JWT_EXPIRE', 24)  # Correction du nom
def test_generate_token(mock_token_file):
    """Test de génération d'un token JWT"""

    # Mock User
    user = MagicMock()
    user.id = 1
    user.role.name = "admin"

    # Mock write_text pour TOKEN_FILE
    mock_token_file.write_text = MagicMock()

    # Appeler la fonction
    token = generate_token(user)

    # Vérifier que le token est généré correctement
    decoded = jwt.decode(token, 'test_secret_key', algorithms=['HS256'])
    assert decoded['user_id'] == user.id
    assert decoded['role'] == user.role.name
    assert 'exp' in decoded

    # Vérifier que le fichier token a été écrit
    mock_token_file.write_text.assert_called_once_with(token)


@patch('epicevents.permissions.auth.TOKEN_FILE')
@patch('epicevents.permissions.auth.JWT_SECRET', 'test_secret_key')
def test_verify_token_valid(mock_token_file):
    """Test de vérification d'un token JWT valide"""

    # Créer un token valide
    user_id = 1
    role = "admin"
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.now(timezone.utc).timestamp() + 3600  # Expire dans 1h
    }
    token = jwt.encode(payload, 'test_secret_key', algorithm='HS256')

    # Mock TOKEN_FILE
    mock_token_file.exists.return_value = True
    mock_token_file.read_text.return_value = token

    # Vérifier le token
    result = verify_token()

    # Vérifications
    assert result is not None
    assert result['user_id'] == user_id
    assert result['role'] == role


@patch('epicevents.permissions.auth.TOKEN_FILE')
@patch('epicevents.permissions.auth.JWT_SECRET', 'test_secret_key')
def test_verify_token_expired(mock_token_file):
    """Test de vérification d'un token JWT expiré"""

    # Créer un token expiré
    user_id = 1
    role = "admin"
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.now(timezone.utc).timestamp() - 14400  # Expiré depuis 4h
    }
    token = jwt.encode(payload, 'test_secret_key', algorithm='HS256')

    # Mock TOKEN_FILE
    mock_token_file.exists.return_value = True
    mock_token_file.read_text.return_value = token

    # Mock remove_token
    with patch('epicevents.permissions.auth.remove_token') as mock_remove_token:
        result = verify_token()

        # Vérifications
        assert result is None
        mock_remove_token.assert_called_once()


@patch('epicevents.permissions.auth.verify_token')
def test_is_logged_authenticated(mock_verify_token):
    """Test de is_logged quand un utilisateur est authentifié"""
    from epicevents.permissions.auth import is_logged
    from epicevents.models.user import User
    
    # Créer un utilisateur mock
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.role = MagicMock()
    mock_user.role.name = "admin"
    
    # Configurer le mock pour verify_token
    mock_verify_token.return_value = {
        'user_id': 1,
        'role': 'admin'
    }
    
    # Patcher User.get pour retourner notre utilisateur mock
    with patch('epicevents.models.user.User.get_by_id', return_value=mock_user):
        # Appeler is_logged
        result = is_logged()
    
    # Vérifier le résultat
    assert result is not None
    assert result.id == 1
    assert result.role.name == "admin"


@patch('epicevents.permissions.auth.verify_token')
def test_is_logged_not_authenticated(mock_verify_token):
    """Test de is_logged quand aucun utilisateur n'est authentifié"""
    from epicevents.permissions.auth import is_logged
    
    # Configurer le mock pour verify_token
    mock_verify_token.return_value = None
    
    # Appeler is_logged
    result = is_logged()
    
    # Vérifier le résultat
    assert result is None




# Tests pour les fonctions d'authentification ayant une couverture insuffisante
@patch('epicevents.permissions.auth.is_logged')
@patch('epicevents.permissions.auth.has_permission')
def test_check_auth_authenticated_with_permission(mock_has_permission, mock_is_logged):
    """Test de check_auth quand l'utilisateur est authentifié et a la permission"""
    from epicevents.permissions.auth import check_auth
    
    # Créer un contexte mock
    mock_ctx = MagicMock()
    mock_ctx.info_name = "customers"
    mock_ctx.invoked_subcommand = "list"
    
    # Créer un utilisateur mock
    mock_user = MagicMock()
    mock_user.role.name = "admin"
    
    # Configurer les mocks
    mock_is_logged.return_value = mock_user
    mock_has_permission.return_value = (True, "")
    
    # Patcher sys.argv pour simuler des arguments de commande
    with patch('sys.argv', ['epicevents', 'customers', 'list']):
        # Appeler check_auth
        check_auth(mock_ctx)
    
    # Vérifier que l'utilisateur a été assigné à ctx.obj
    assert mock_ctx.obj == mock_user
    mock_is_logged.assert_called_once()
    mock_has_permission.assert_called_once()


@patch('epicevents.permissions.auth.is_logged')
@patch('epicevents.permissions.auth.has_permission')
@patch('epicevents.permissions.auth.console.print')
def test_check_auth_authenticated_without_permission(mock_print, mock_has_permission, mock_is_logged):
    """Test de check_auth quand l'utilisateur est authentifié mais n'a pas la permission"""
    from epicevents.permissions.auth import check_auth
    
    # Créer un contexte mock
    mock_ctx = MagicMock()
    mock_ctx.info_name = "customers"
    mock_ctx.invoked_subcommand = "delete"
    
    # Créer un utilisateur mock
    mock_user = MagicMock()
    mock_user.role.name = "sales"
    
    # Configurer les mocks
    mock_is_logged.return_value = mock_user
    mock_has_permission.return_value = (False, "Message d'erreur")
    
    # La fonction devrait lever une exception typer.Exit
    with pytest.raises(typer.Exit):
        # Patcher sys.argv pour simuler des arguments de commande
        with patch('sys.argv', ['epicevents', 'customers', 'delete', '1']):
            check_auth(mock_ctx)
    
    # Vérifier que l'utilisateur a été assigné à ctx.obj
    assert mock_ctx.obj == mock_user
    mock_is_logged.assert_called_once()
    mock_has_permission.assert_called_once()
    # Vérifier que console.print a été appelé pour afficher l'erreur
    mock_print.assert_called()


@patch('epicevents.permissions.auth.is_logged')
@patch('epicevents.permissions.auth.console.print')
def test_check_auth_not_authenticated(mock_print, mock_is_logged):
    """Test de check_auth quand l'utilisateur n'est pas authentifié"""
    from epicevents.permissions.auth import check_auth
    
    # Créer un contexte mock
    mock_ctx = MagicMock()
    mock_ctx.info_name = "customers"
    mock_ctx.invoked_subcommand = "list"
    
    # Configurer le mock pour is_logged
    mock_is_logged.return_value = None
    
    # La fonction devrait lever une exception typer.Exit
    with pytest.raises(typer.Exit):
        check_auth(mock_ctx)
    
    mock_is_logged.assert_called_once()
    # Vérifier que console.print a été appelé pour afficher l'erreur
    mock_print.assert_called()

def test_get_target_id_from_args():
    """Test de get_target_id_from_args avec différents types d'arguments"""
    from epicevents.permissions.auth import get_target_id_from_args
    
    # Tester avec un argument ID après une commande
    args = ['epicevents', 'customers', 'read', '42']
    result = get_target_id_from_args(args)
    assert result == 42
    
    # Tester avec une option après la commande (pas d'ID)
    args = ['epicevents', 'customers', 'create', '--name', 'Test']
    result = get_target_id_from_args(args)
    assert result is None
    
    # Tester avec une liste vide
    args = []
    result = get_target_id_from_args(args)
    assert result is None

def test_welcome_user(capsys):
    """Test de la fonction welcome_user en capturant la sortie"""
    welcome_user()
    
    # Capturer la sortie
    captured = capsys.readouterr()
    
    # Vérifier que le texte attendu est bien présent dans la sortie
    assert "WELCOME TO EPICEVENTS" in captured.out


# Tests pour les fonctions CLI avec une couverture insuffisante
@patch('epicevents.cli.contracts.Contract')
@patch('epicevents.cli.contracts.Customer')
@patch('epicevents.cli.contracts.User')
@patch('epicevents.cli.contracts.console.print')
def test_create_contract(mock_print, mock_user, mock_customer, mock_contract, runner):
    """Test de la commande create_contract"""
    from epicevents.cli.contracts import app as contracts_app
    
    # Créer des mocks pour les modèles
    mock_customer_instance = MagicMock()
    mock_customer_instance.id = 1
    mock_customer_instance.first_name = "John"
    mock_customer_instance.last_name = "Doe"
    mock_customer.get_by_id.return_value = mock_customer_instance
    
    mock_user_instance = MagicMock()
    mock_user_instance.id = 2
    mock_user_instance.role.name = "management"
    mock_user.get_by_id.return_value = mock_user_instance
    
    # Mock pour le nouveau contrat
    fake_contract_instance = MagicMock()
    fake_contract_instance.id = 3
    mock_contract.return_value = fake_contract_instance
    
    # Simuler que la sauvegarde réussit
    fake_contract_instance.save.return_value = None
    
    # Créer un contexte avec un utilisateur connecté
    with patch('epicevents.permissions.auth.check_auth') as mock_check_auth:
        # Configurer un objet mock pour ctx.obj
        mock_obj = MagicMock()
        mock_obj.id = 99  # ID différent du contact_id
        mock_obj.role.name = "admin"  # Pas un 'management'
        mock_check_auth.return_value = None  # Ne fait rien, juste pour éviter l'authentification réelle
        
        # Exécuter la commande
        result = runner.invoke(
            contracts_app, 
            ["create", "-c", "1", "-st", "1000.0", "-sd", "500.0", "-si", "-u", "2"],
            obj=mock_obj  # Passer l'objet utilisateur simulé
        )
    
    # Vérifier que la commande a réussi
    assert result.exit_code == 0
    mock_customer.get_by_id.assert_called_once_with(1)
    mock_user.get_by_id.assert_called_once_with(2)
    fake_contract_instance.save.assert_called_once()
    # Vérifier qu'un message de succès a été affiché
    mock_print.assert_called()


@patch('epicevents.cli.contracts.Contract')
@patch('epicevents.cli.contracts.Confirm.ask')
@patch('epicevents.cli.contracts.console.print')
def test_delete_contract_confirmed(mock_print, mock_confirm, mock_contract, runner):
    """Test de la commande delete_contract avec confirmation"""
    from epicevents.cli.contracts import app as contracts_app
    
    # Configurer les mocks
    mock_contract_instance = MagicMock()
    mock_contract_instance.id = 1
    mock_contract.get_by_id.return_value = mock_contract_instance
    
    # Configurer le mock pour confirmer la suppression
    mock_confirm.return_value = True
    
    # Patcher check_auth pour éviter l'authentification réelle
    with patch('epicevents.permissions.auth.check_auth'):
        # Exécuter la commande
        result = runner.invoke(contracts_app, ["delete", "1"])
    
    # Vérifier que la commande a réussi
    assert result.exit_code == 0
    mock_contract.get_by_id.assert_called_once_with(1)
    mock_confirm.assert_called_once()
    mock_contract_instance.delete_instance.assert_called_once()
    # Vérifier qu'un message de succès a été affiché
    mock_print.assert_called()


@patch('epicevents.cli.contracts.Contract')
@patch('epicevents.cli.contracts.Confirm.ask')
@patch('epicevents.cli.contracts.console.print')
def test_delete_contract_canceled(mock_print, mock_confirm, mock_contract, runner):
    """Test de la commande delete_contract avec annulation"""
    from epicevents.cli.contracts import app as contracts_app
    
    # Configurer les mocks
    mock_contract_instance = MagicMock()
    mock_contract_instance.id = 1
    mock_contract.get_by_id.return_value = mock_contract_instance
    
    # Configurer le mock pour annuler la suppression
    mock_confirm.return_value = False
    
    # Patcher check_auth pour éviter l'authentification réelle
    with patch('epicevents.permissions.auth.check_auth'):
        # Exécuter la commande
        result = runner.invoke(contracts_app, ["delete", "1"])
    
    # La commande devrait réussir mais ne pas supprimer
    assert result.exit_code == 0  # Au lieu de != 0
    mock_contract.get_by_id.assert_called_once_with(1)
    mock_confirm.assert_called_once()
    mock_contract_instance.delete_instance.assert_not_called()
    # Vérifier qu'un message d'annulation a été affiché
    mock_print.assert_called()


@patch('epicevents.cli.customers.Customer')
@patch('epicevents.cli.customers.display_list')
def test_list_customers(mock_display, mock_customer, runner):
    """Test de la fonction list_customers"""
    from epicevents.cli.customers import app as customers_app
    
    # Créer des données de test pour les clients
    mock_customers = []
    for i in range(5):
        mock_customer_instance = MagicMock()
        mock_customer_instance.id = i
        mock_customer_instance.first_name = f"First{i}"
        mock_customer_instance.last_name = f"Last{i}"
        mock_customer_instance.email = f"customer{i}@example.com"
        mock_customer_instance.team_contact_id = MagicMock()  # Simuler un contact
        mock_customers.append(mock_customer_instance)
    
    # Configurer le mock pour Customer.select()
    mock_query = MagicMock()
    mock_query.__iter__.return_value = iter(mock_customers)
    mock_customer.select.return_value = mock_query
    
    # Patcher check_auth pour éviter l'authentification réelle
    with patch('epicevents.permissions.auth.check_auth'):
        # Exécuter la commande
        result = runner.invoke(customers_app, ["list"])
    
    # Vérifier que la commande a réussi
    assert result.exit_code == 0
    mock_customer.select.assert_called_once()
    mock_display.assert_called_once()


@patch('epicevents.cli.customers.Customer')
@patch('epicevents.cli.customers.Confirm.ask')
@patch('epicevents.cli.customers.console.print')
def test_delete_customer_confirmed(mock_print, mock_confirm, mock_customer, runner):
    """Test de la commande delete_customer avec confirmation"""
    from epicevents.cli.customers import app as customers_app
    
    # Configurer les mocks
    mock_customer_instance = MagicMock()
    mock_customer_instance.id = 1
    mock_customer.get_by_id.return_value = mock_customer_instance  # Utiliser get_by_id au lieu de get_or_none
    
    # Configurer le mock pour confirmer la suppression
    mock_confirm.return_value = True
    
    # Patcher check_auth pour éviter l'authentification réelle
    with patch('epicevents.permissions.auth.check_auth'):
        # Exécuter la commande
        result = runner.invoke(customers_app, ["delete", "1"])
    
    # Vérifier que la commande a réussi
    assert result.exit_code == 0
    mock_customer.get_by_id.assert_called_once_with(1)  # Vérifier get_by_id au lieu de get_or_none
    mock_confirm.assert_called_once()
    mock_customer_instance.delete_instance.assert_called_once()
    # Vérifier qu'un message de succès a été affiché
    mock_print.assert_called()


@patch('epicevents.cli.events.Event')
@patch('epicevents.cli.events.Confirm.ask')
@patch('epicevents.cli.events.console.print')
def test_delete_event_confirmed(mock_print, mock_confirm, mock_event, runner):
    """Test de la commande delete_event avec confirmation"""
    from epicevents.cli.events import app as events_app
    
    # Configurer les mocks
    mock_event_instance = MagicMock()
    mock_event_instance.id = 1
    mock_event.get_by_id.return_value = mock_event_instance  # Utiliser get_by_id au lieu de get_or_none
    
    # Configurer le mock pour confirmer la suppression
    mock_confirm.return_value = True
    
    # Patcher check_auth pour éviter l'authentification réelle
    with patch('epicevents.permissions.auth.check_auth'):
        # Exécuter la commande
        result = runner.invoke(events_app, ["delete", "1"])
    
    # Vérifier que la commande a réussi
    assert result.exit_code == 0
    mock_event.get_by_id.assert_called_once_with(1)  # Vérifier get_by_id au lieu de get_or_none
    mock_confirm.assert_called_once()
    mock_event_instance.delete_instance.assert_called_once()
    # Vérifier qu'un message de succès a été affiché
    mock_print.assert_called()


@patch('epicevents.cli.users.User')
@patch('epicevents.cli.users.Confirm.ask')
@patch('epicevents.cli.users.console.print')
def test_delete_user_confirmed(mock_print, mock_confirm, mock_user, runner):
    """Test de la commande delete_user avec confirmation"""
    from epicevents.cli.users import app as users_app
    
    # Configurer les mocks
    mock_user_instance = MagicMock()
    mock_user_instance.id = 1
    mock_user.get_by_id.return_value = mock_user_instance  # Utiliser get_by_id au lieu de get_or_none
    
    # Configurer le mock pour confirmer la suppression
    mock_confirm.return_value = True
    
    # Patcher check_auth pour éviter l'authentification réelle
    with patch('epicevents.permissions.auth.check_auth'):
        # Exécuter la commande
        result = runner.invoke(users_app, ["delete", "1"])
    
    # Vérifier que la commande a réussi
    assert result.exit_code == 0
    mock_user.get_by_id.assert_called_once_with(1)  # Vérifier get_by_id au lieu de get_or_none
    mock_confirm.assert_called_once()
    mock_user_instance.delete_instance.assert_called_once()
    # Vérifier qu'un message de succès a été affiché
    mock_print.assert_called()
