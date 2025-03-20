import pytest
import jwt
from datetime import datetime, timezone
from epicevents.models.user import User
from epicevents.permissions.auth import generate_token
from epicevents.permissions.auth import verify_token
from epicevents.permissions.auth import remove_token
from epicevents.permissions.auth import is_logged
from epicevents.permissions.auth import get_target_id_from_args
from epicevents.permissions.auth import check_auth
from tests.conftest import mock_admin_user


# Tests des fonctions d'authentification
def test_remove_token(monkeypatch):
    """Test pour vérifier la fonction remove_token"""
    
    # Créer un mock approprié pour TOKEN_FILE
    class MockPath:
        def __init__(self):
            self.unlink_called = False
            self.missing_ok_value = None
            
        def unlink(self, missing_ok=False):
            self.unlink_called = True
            self.missing_ok_value = missing_ok
    
    # Instancier le mock
    mock_token_file = MockPath()
    
    # Patcher TOKEN_FILE avec notre mock
    monkeypatch.setattr("epicevents.permissions.auth.TOKEN_FILE", mock_token_file)
    
    # Appeler la fonction
    remove_token()
    
    # Vérifier que la méthode unlink a été appelée avec missing_ok=True
    assert mock_token_file.unlink_called
    assert mock_token_file.missing_ok_value is True


def test_token_file_not_exists(monkeypatch):
    """Test pour vérifier le comportement quand le fichier token n'existe pas"""
    
    # Créer un mock approprié pour TOKEN_FILE
    class MockPath:
        def exists(self):
            return False
    
    # Instancier le mock
    mock_token_file = MockPath()
    
    # Patcher TOKEN_FILE avec notre mock
    monkeypatch.setattr("epicevents.permissions.auth.TOKEN_FILE", mock_token_file)
    
    # Appeler la fonction
    result = verify_token()
    
    # Vérifier que le résultat est None
    assert result is None


def test_generate_token(monkeypatch, mock_admin_user):
    """Test de génération d'un token JWT"""
    # Mock JWT_SECRET et JWT_EXPIRE
    monkeypatch.setattr("epicevents.permissions.auth.JWT_SECRET", "test_secret_key")
    monkeypatch.setattr("epicevents.permissions.auth.JWT_EXPIRE", 24)
    
    # Créer un mock approprié pour TOKEN_FILE
    class MockPath:
        def __init__(self):
            self.content = None
            
        def write_text(self, content):
            self.content = content
    
    # Instancier le mock
    mock_token_file = MockPath()
    
    # Patcher TOKEN_FILE avec notre mock
    monkeypatch.setattr("epicevents.permissions.auth.TOKEN_FILE", mock_token_file)

    # Mock User
    user = mock_admin_user

    # Appeler la fonction
    token = generate_token(user)

    # Vérifier que le token est généré correctement
    decoded = jwt.decode(token, 'test_secret_key', algorithms=['HS256'])
    assert decoded['user_id'] == user.id
    assert decoded['role'] == user.role.name
    assert 'exp' in decoded

    # Vérifier que le fichier token a été écrit
    assert mock_token_file.content == token


def test_verify_token_valid(monkeypatch):
    """Test de vérification d'un token JWT valide"""
    # Mock JWT_SECRET
    monkeypatch.setattr("epicevents.permissions.auth.JWT_SECRET", "test_secret_key")
    
    # Créer un token valide
    user_id = 1
    role = "admin"
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.now(timezone.utc).timestamp() + 3600  # Expire dans 1h
    }
    token = jwt.encode(payload, 'test_secret_key', algorithm='HS256')

    # Créer un mock approprié pour TOKEN_FILE
    class MockPath:
        def exists(self):
            return True
            
        def read_text(self):
            return token
    
    # Instancier le mock
    mock_token_file = MockPath()
    
    # Patcher TOKEN_FILE avec notre mock
    monkeypatch.setattr("epicevents.permissions.auth.TOKEN_FILE", mock_token_file)

    # Vérifier le token
    result = verify_token()

    # Vérifications
    assert result is not None
    assert result['user_id'] == user_id
    assert result['role'] == role


def test_verify_token_expired(monkeypatch):
    """Test de vérification d'un token JWT expiré"""
    # Mock JWT_SECRET
    monkeypatch.setattr("epicevents.permissions.auth.JWT_SECRET", "test_secret_key")
    
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
    mock_token_file = lambda: None
    mock_token_file.exists = lambda: True
    mock_token_file.read_text = lambda: token
    monkeypatch.setattr("epicevents.permissions.auth.TOKEN_FILE", mock_token_file)

    # Mock remove_token
    def mock_remove_token():
        mock_remove_token.called = True

    mock_remove_token.called = False
    monkeypatch.setattr("epicevents.permissions.auth.remove_token", mock_remove_token)
    
    # Appeler la fonction
    result = verify_token()

    # Vérifications
    assert result is None
    assert mock_remove_token.called


def test_is_logged_not_authenticated(monkeypatch):
    """Test de is_logged quand aucun utilisateur n'est authentifié"""
    
    # Configurer le mock pour verify_token
    monkeypatch.setattr("epicevents.permissions.auth.verify_token", lambda: None)
    
    # Appeler is_logged
    result = is_logged()
    
    # Vérifier le résultat
    assert result is None


def test_get_target_id_from_args():
    """Test de get_target_id_from_args avec différents types d'arguments"""
    
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


def test_check_auth(monkeypatch):
    """Test de la fonction check_auth"""
    import typer
    import sys
    import sentry_sdk
    
    # Créer un mock pour User
    class MockUser:
        def __init__(self):
            self.id = 1
            self.username = "johndoe"
    
    user_mock = MockUser()
    
    # Créer un mock pour is_logged
    def mock_is_logged():
        return user_mock
    
    # Mock pour get_target_id_from_args
    def mock_get_target_id_from_args(args):
        return 123
    
    # Mock pour has_permission qui autorise
    def mock_has_permission(user, resource, action, target_id):
        return True, None
    
    # Mock pour console.print
    messages = []
    def mock_print(message):
        messages.append(message)
    
    # Mock pour format_text
    def mock_format_text(style, color, text):
        return text
    
    # Mock pour typer.Exit
    class MockExit(Exception):
        def __init__(self, code=0):
            self.code = code
    
    # Mock pour sentry_sdk
    captured_messages = []
    class MockScope:
        def set_context(self, name, data):
            return self
    
    def mock_capture_message(message, level=None, scope=None):
        captured_messages.append(message)
    
    # Appliquer les mocks
    monkeypatch.setattr("typer.Exit", MockExit)
    monkeypatch.setattr("epicevents.permissions.auth.is_logged", mock_is_logged)
    monkeypatch.setattr("epicevents.permissions.auth.get_target_id_from_args", mock_get_target_id_from_args)
    monkeypatch.setattr("epicevents.permissions.auth.has_permission", mock_has_permission)
    monkeypatch.setattr("epicevents.permissions.auth.console.print", mock_print)
    monkeypatch.setattr("epicevents.permissions.auth.format_text", mock_format_text)
    monkeypatch.setattr(sys, "argv", ["program", "command", "arg1", "arg2"])
    monkeypatch.setattr(sentry_sdk, "capture_message", mock_capture_message)
    monkeypatch.setattr(sentry_sdk, "Scope", lambda: MockScope())
    monkeypatch.setattr("epicevents.permissions.auth.SENTRY_ENV", "production")
    
    # Créer un mock pour typer.Context
    class MockContext:
        def __init__(self):
            self.invoked_subcommand = "create"
            self.info_name = "resource"
            self.obj = None
    
    ctx = MockContext()
    
    # Test avec permission accordée
    check_auth(ctx)
    assert ctx.obj == user_mock
    
    # Test avec permission refusée
    def mock_has_permission_denied(user, resource, action, target_id):
        return False, "Accès refusé"
    
    monkeypatch.setattr("epicevents.permissions.auth.has_permission", mock_has_permission_denied)
    
    try:
        check_auth(ctx)
        pytest.fail("L'exception typer.Exit aurait dû être levée")
    except MockExit as e:
        assert e.code == 1
        assert any("Vous n'avez pas l'autorisation" in str(m) for m in messages)
        assert len(captured_messages) > 0
        assert "Permission denied" in captured_messages[0]
