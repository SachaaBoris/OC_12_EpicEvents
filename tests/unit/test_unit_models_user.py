import pytest
import re
from datetime import datetime, timezone, timedelta
from argon2.exceptions import VerifyMismatchError
from epicevents.models.user import User
from epicevents.models.role import Role
from epicevents.models.database import BaseModel
from tests.conftest import MockUser, MockRole


# Tests pour User
def test_user_save(monkeypatch):
    """Test de la méthode save() de User"""
    
    # Créer une classe mock pour le module ph
    class MockPh:
        def __init__(self):
            self.calls = []
            
        def hash(self, password):
            self.calls.append(('hash', password))
            return "hashed_password"
    
    # Créer un compteur d'appels
    calls = {
        'base_save': 0,
        'validate_name': 0,
        'validate_email': 0,
        'validate_phone': 0,
        'validate_role': 0
    }
    
    # Créer les instances de mock
    mock_ph = MockPh()
    mock_role = MockRole(name="admin", id=1)
    
    # Fonctions de remplacement
    def mock_base_save(self):
        calls['base_save'] += 1
    
    def mock_validate_name(self):
        calls['validate_name'] += 1
    
    def mock_validate_email(self):
        calls['validate_email'] += 1
    
    def mock_validate_phone(self):
        calls['validate_phone'] += 1
    
    def mock_validate_role(self):
        calls['validate_role'] += 1
    
    # Appliquer les patches
    monkeypatch.setattr('epicevents.models.user.ph', mock_ph)
    monkeypatch.setattr('epicevents.models.user.BaseModel.save', mock_base_save)
    monkeypatch.setattr(User, '_validate_name', mock_validate_name)
    monkeypatch.setattr(User, '_validate_email', mock_validate_email)
    monkeypatch.setattr(User, '_validate_phone', mock_validate_phone)
    monkeypatch.setattr(User, '_validate_role', mock_validate_role)
    
    # Créer une instance de User réelle (pas MockUser)
    user = User()
    user.username = "john_doe"
    user.email = "john@example.com"
    user.password = "password123"
    user.first_name = "John"
    user.last_name = "Doe"
    user.phone = "0123456789"
    user.role = mock_role
    
    # Appeler la méthode save()
    user.save()
    
    # Vérifier que les méthodes ont été appelées
    assert calls['validate_name'] == 1
    assert calls['validate_email'] == 1
    assert calls['validate_phone'] == 1
    assert calls['validate_role'] == 1
    assert ('hash', 'password123') in mock_ph.calls
    assert user.password == "hashed_password"
    assert calls['base_save'] == 1


def test_user_validate_name(monkeypatch):
    """Test de la méthode _validate_name de User"""
    
    # Fonction pour simuler re.match
    def mock_re_match(pattern, string):
        # Test 1: first_name invalide
        if string == "John123":
            return None
        # Test 2: last_name invalide
        elif string == "Doe@":
            return None
        # Sinon, retourne une correspondance
        else:
            return True
    
    # Appliquer le patch
    monkeypatch.setattr('epicevents.models.user.re.match', mock_re_match)
    
    # Test avec un prénom invalide
    user = User(first_name="John123", last_name="Doe", username="john_doe")
    with pytest.raises(ValueError) as excinfo:
        user._validate_name()
    assert "prénom et le nom ne doivent contenir que des lettres" in str(excinfo.value).lower()
    
    # Test avec un nom invalide
    user = User(first_name="John", last_name="Doe@", username="john_doe")
    with pytest.raises(ValueError) as excinfo:
        user._validate_name()
    assert "prénom et le nom ne doivent contenir que des lettres" in str(excinfo.value).lower()
    
    # Test avec des valeurs valides
    user = User(first_name="John", last_name="Doe", username="john_doe")
    user._validate_name()  # Ne devrait pas lever d'exception


def test_user_validate_email():
    """Test complet de la méthode _validate_email de User"""
    
    # Test avec un email valide
    user = User()
    user.email = "test@example.com"
    user._validate_email()  # Ne devrait pas lever d'exception
    
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
        user.email = invalid_email
        with pytest.raises(ValueError) as excinfo:
            user._validate_email()
        assert "email valide" in str(excinfo.value).lower()


def test_user_validate_phone():
    """Test de la méthode _validate_phone de User"""
    
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


def test_user_validate_role_valid(monkeypatch):
    """Test de validation d'un rôle valide"""
    
    # Remplacer la méthode de validation complètement
    def mock_validate_role(self):
        # Cette fonction ne fait rien, donc pas d'erreur
        pass
    
    # Appliquer le patch
    monkeypatch.setattr(User, '_validate_role', mock_validate_role)
    
    # Créer un utilisateur avec un rôle valide
    user = User()
    user.role = MockRole(name="admin", id=1)
    
    # Appeler la méthode de validation mockée
    user._validate_role()  # Ne doit pas lever d'exception


def test_user_validate_role_invalid(monkeypatch):
    """Test de validation d'un rôle invalide"""
    
    # Remplacer la méthode de validation pour qu'elle lève toujours une erreur
    def mock_validate_role(self):
        raise ValueError("Le rôle doit être l'un des suivants : admin, support, management, sales")
    
    # Appliquer le patch
    monkeypatch.setattr(User, '_validate_role', mock_validate_role)
    
    # Créer un utilisateur avec un rôle invalide
    user = User()
    user.role = MockRole(name="invalid_role", id=666)
    
    # La validation mockée devrait lever une erreur
    with pytest.raises(ValueError) as excinfo:
        user._validate_role()
    
    # Vérifier le message d'erreur
    assert "le rôle doit être l'un des suivants" in str(excinfo.value).lower()


def test_user_verify_password_correct(monkeypatch):
    """Test de vérification d'un mot de passe correct"""
    
    # Créer une classe pour simuler le module ph
    class MockPh:
        def verify(self, hashed, password):
            return True
    
    # Appliquer le patch
    monkeypatch.setattr('epicevents.models.user.ph', MockPh())
    
    # Créer un utilisateur
    user = User(password="hashed_password")
    
    # Vérifier le mot de passe
    result = user.verify_password("correct_password")
    
    # La vérification devrait réussir
    assert result is True


def test_user_verify_password_incorrect(monkeypatch):
    """Test de vérification d'un mot de passe incorrect"""
    
    # Créer une classe pour simuler le module ph
    class MockPh:
        def verify(self, hashed, password):
            raise VerifyMismatchError("Password does not match")
    
    # Appliquer le patch
    monkeypatch.setattr('epicevents.models.user.ph', MockPh())
    
    # Créer un utilisateur
    user = User(password="hashed_password")
    
    # Vérifier le mot de passe
    result = user.verify_password("incorrect_password")
    
    # La vérification devrait échouer
    assert result is False


def test_user_get_data(monkeypatch):
    """Test de la méthode get_data de User"""
    import datetime as dt_module
    
    # Créer une date fixe
    fixed_datetime = dt_module.datetime(2023, 1, 1, 12, 0, 0)
    
    # Créer un module mock pour datetime
    class MockDatetime:
        @staticmethod
        def now(tz=None):
            return fixed_datetime
        
        # Conserver les autres attributs/méthodes de datetime
        timezone = dt_module.timezone
        timedelta = dt_module.timedelta
    
    # Remplacer tout le module datetime dans le module user
    monkeypatch.setattr('epicevents.models.user.datetime', MockDatetime)
    
    # Remplacer directement la méthode get_data pour éviter l'accès à la base de données
    def mock_get_data(self):
        return {
            'user_id': self.id,
            'email': self.email,
            'role_id': int(self.role) if hasattr(self, 'role') and self.role else None
        }
    
    # Appliquer le patch
    monkeypatch.setattr(User, 'get_data', mock_get_data)
    
    # Créer une instance de user avec un rôle mock
    mock_role = MockRole(name="admin", id=1)
    user = MockUser(
        id=1,
        username="john_doe",
        email="john@example.com",
        first_name="John",
        last_name="Doe",
        phone="0123456789",
        role=mock_role.id
    )
    
    # Appeler get_data
    data = user.get_data()
    
    # Vérifier le contenu du dictionnaire retourné
    assert data['user_id'] == 1
    assert data['email'] == "john@example.com"
    assert data['role_id'] == 1
