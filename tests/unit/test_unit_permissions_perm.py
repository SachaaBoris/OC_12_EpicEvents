import pytest
from peewee import DoesNotExist
from epicevents.models.contract import Contract
from epicevents.models.customer import Customer
from epicevents.models.event import Event
from epicevents.permissions.perm import has_permission
from epicevents.permissions.perm import always_true
from epicevents.permissions.perm import is_owner
from epicevents.permissions.perm import is_self
from epicevents.permissions.perm import is_my_customer


# Tests pour les fonctions de permissions
def test_always_true():
    """Test de la fonction always_true"""
    
    # Appeler la fonction avec n'importe quels arguments
    result = always_true(1, 2, 3)
    
    # Vérifier que le résultat est toujours True
    assert result is True


def test_is_self():
    """Test de la fonction is_self"""
    
    # Créer un utilisateur avec un ID
    class User:
        def __init__(self, id):
            self.id = id
    
    # Créer deux utilisateurs
    user1 = User(1)
    user2 = User(2)
    
    # Appeler is_self avec l'ID de l'utilisateur courant
    result = is_self(user1, user1, "user")
    assert result is True
    
    # Appeler is_self avec un utilisateur différent
    result = is_self(user1, user2, "user")
    assert result is False


def test_has_permission_admin(monkeypatch):
    """Test de has_permission pour un admin (toujours autorisé)"""
    
    # Créer un utilisateur avec un rôle
    class Role:
        def __init__(self, name):
            self.name = name
    
    class User:
        def __init__(self, role):
            self.role = role
    
    # Créer un utilisateur admin
    user = User(Role("admin"))
    
    # Dictionnaire de permissions simulé
    def mock_get_all_permissions():
        return {
            "admin": {
                "*": {
                    "*": lambda *args: True
                }
            }
        }
    
    # Patcher get_all_permissions
    monkeypatch.setattr("epicevents.permissions.perm.get_all_permissions", mock_get_all_permissions)
    
    # Appeler has_permission
    result = has_permission(user, "any_resource", "any_action")
    
    # Le résultat devrait être True (admin a toutes les permissions)
    assert result[0] is True


def test_has_permission_specific_role(monkeypatch):
    """Test de has_permission pour un rôle spécifique avec une permission existante"""
    
    # Créer un utilisateur avec un rôle
    class Role:
        def __init__(self, name):
            self.name = name
    
    class User:
        def __init__(self, role):
            self.role = role
    
    # Créer un utilisateur commercial
    user = User(Role("sales"))
    
    # Dictionnaire de permissions simulé
    def mock_get_all_permissions():
        return {
            "sales": {
                "customer": {
                    "read": lambda *args: True
                }
            }
        }
    
    # Patcher get_all_permissions
    monkeypatch.setattr("epicevents.permissions.perm.get_all_permissions", mock_get_all_permissions)
    
    # Appeler has_permission pour une permission que sales a
    result = has_permission(user, "customer", "read")
    
    # Le résultat devrait être True
    assert result[0] is True
    
    # Appeler has_permission pour une permission que sales n'a pas
    result = has_permission(user, "customer", "delete")
    
    # Le résultat devrait être False
    assert result[0] is False


def test_is_owner():
    """Test de la fonction is_owner"""
    
    # Créer des classes pour les objets simulés
    class User:
        def __init__(self, id):
            self.id = id
    
    class TeamContact:
        def __init__(self, id):
            self.id = id
            
    class Customer:
        def __init__(self, team_contact_id):
            # Créer un objet TeamContact avec l'ID fourni
            self.team_contact_id = TeamContact(team_contact_id)
    
    # Créer un utilisateur
    user = User(1)
    
    # Créer un client avec le même ID de contact
    customer = Customer(1)
    
    # Appeler is_owner
    result = is_owner(user, customer, "customer")
    
    # Vérifier que le résultat est True
    assert result is True
    
    # Tester avec un ID différent
    customer.team_contact_id = TeamContact(2)  # Remplacer par un nouvel objet, pas juste un ID
    result = is_owner(user, customer, "customer")
    
    # Vérifier que le résultat est False
    assert result is False


def test_is_owner_edge_cases():
    """Test complet de is_owner avec différents cas limites"""
    
    # Créer un utilisateur
    class User:
        def __init__(self, id):
            self.id = id
            
        def __int__(self):
            return self.id
    
    # Créer une classe pour team_contact_id
    class TeamContact:
        def __init__(self, id):
            self.id = id
    
    # Créer différents types d'objets
    class ObjectWithTeamContactId:
        def __init__(self, id):
            # Créer un objet TeamContact avec l'ID fourni
            self.team_contact_id = TeamContact(id)
    
    class ObjectWithoutTeamContactId:
        def __init__(self):
            pass  # Pas d'attribut team_contact_id
    
    # Créer l'utilisateur
    user = User(1)
    
    # Test avec un objet où user.id == object.team_contact_id.id
    obj1 = ObjectWithTeamContactId(1)
    assert is_owner(user, obj1, "customer") is True
    
    # Test avec un objet où user.id != object.team_contact_id.id
    obj2 = ObjectWithTeamContactId(2)
    assert is_owner(user, obj2, "contract") is False
    
    # Test avec un objet sans attribut team_contact_id
    obj3 = ObjectWithoutTeamContactId()
    assert is_owner(user, obj3, "event") is False


def test_is_my_customer(monkeypatch):
    """Test de is_my_customer"""
    
    # Classe User simple
    class User:
        def __init__(self, id):
            self.id = id
    
    # Mock pour Event
    class MockEvent:
        @staticmethod
        def get_by_id(id):
            if id == 123:
                event = type('Event', (), {})()
                event.contract = type('Contract', (), {})()
                event.contract.id = 456
                return event
            raise DoesNotExist()
    
    # Mock pour Contract
    class MockContract:
        @staticmethod
        def get_by_id(id):
            if id == 456:
                contract = type('Contract', (), {})()
                contract.signed = True
                contract.customer_id = 789
                return contract
            raise DoesNotExist()
    
    # Mock pour la sélection Customer
    class MockCustomerSelect:
        def where(self, condition):
            return self
        
        def exists(self):
            return True
    
    class MockCustomer:
        @staticmethod
        def select():
            return MockCustomerSelect()
    
    # Définir des attributs statiques sur MockCustomer pour les expressions ORM
    MockCustomer.id = object()
    MockCustomer.team_contact_id = object()
    
    # Patcher les modules importés
    import epicevents.models.event
       
    monkeypatch.setattr(epicevents.permissions.perm, "Event", MockEvent)
    monkeypatch.setattr(epicevents.permissions.perm, "Contract", MockContract)
    monkeypatch.setattr(epicevents.permissions.perm, "Customer", MockCustomer)
    monkeypatch.setattr(epicevents.permissions.perm, "DoesNotExist", DoesNotExist)
    
    # Créer un utilisateur
    user = User(1)
    
    # Test avec ID valide
    result, error = is_my_customer(user, 123, 'event')
    assert result is True, f"Expected True, got {result}"
    assert error is None, f"Expected None, got {error}"
    
    # Test avec ID invalide
    result, error = is_my_customer(user, 999, 'event')
    assert result is False, f"Expected False, got {result}"
    assert error is not None, f"Expected non-None error message"
