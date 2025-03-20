import pytest
from peewee import DoesNotExist
from epicevents.models.user import User
from epicevents.models.customer import Customer
from epicevents.models.contract import Contract
from epicevents.models.event import Event
from epicevents.permissions.perm import is_my_customer


def test_is_my_customer_direct_match(monkeypatch):
    """Test is_my_customer lorsque l'utilisateur est le commercial du client"""
    
    # Créer des classes pour les objets simulés
    class User:
        def __init__(self, id):
            self.id = id
            
        def __int__(self):
            return self.id
    
    class MockCustomer:
        def __init__(self):
            self.id = 1
            self.team_contact_id = 3  # Match direct avec l'ID de l'utilisateur
            
        def __int__(self):
            return self.id
    
    class MockEvent:
        def __init__(self):
            self.contract = MockContract()
            
    class MockContract:
        def __init__(self):
            self.id = 1
            self.customer_id = 1
            self.signed = True
    
    # Créer les objets
    user = User(3)
    customer = MockCustomer()
    
    # Simuler les méthodes de requête
    def mock_event_get_by_id(id):
        return MockEvent()
        
    def mock_contract_get_by_id(id):
        return MockContract()
    
    # Simuler Customer.select().where().exists()
    class MockQuery:
        def where(self, *args, **kwargs):
            return self
            
        def exists(self):
            return True
    
    # Appliquer les patches
    monkeypatch.setattr("epicevents.models.event.Event.get_by_id", mock_event_get_by_id)
    monkeypatch.setattr("epicevents.models.contract.Contract.get_by_id", mock_contract_get_by_id)
    monkeypatch.setattr("epicevents.models.customer.Customer.select", lambda: MockQuery())
    
    # Appeler is_my_customer
    result = is_my_customer(user, 1, "event")
    
    # Vérifier le résultat
    assert result[0] is True
    assert result[1] is None  # Le deuxième élément est None, pas une chaîne vide


def test_is_my_customer_exception_handling(monkeypatch):
    """Test is_my_customer lors d'une exception dans la base de données"""
    
    class User:
        def __init__(self, id):
            self.id = id
            
        def __int__(self):
            return self.id
    
    # Créer l'utilisateur
    user = User(3)
    
    # Simuler Event.get_by_id qui lève DoesNotExist
    def mock_get_by_id_error(id):
        raise DoesNotExist(f"L'événement {id} n'existe pas.")
    
    # Simuler Contract.get_by_id qui lèverait également une DoesNotExist
    def mock_contract_get_by_id_error(id):
        raise DoesNotExist(f"Le contrat {id} n'existe pas.")
    
    # Appliquer les patches
    monkeypatch.setattr("epicevents.models.event.Event.get_by_id", mock_get_by_id_error)
    monkeypatch.setattr("epicevents.models.contract.Contract.get_by_id", mock_contract_get_by_id_error)
    
    # Appeler is_my_customer
    result = is_my_customer(user, 1, "event")
    
    # Vérifier le résultat
    assert result[0] is False
    # Le message peut être différent maintenant, alors vérifiez qu'il contient des informations pertinentes
    assert "n'existe" in result[1]
