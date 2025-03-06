import pytest
import json
import datetime
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open


# Tests pour les fonctions de permissions
def test_always_true():
    """Test de la fonction always_true"""
    from epicevents.permissions.perm import always_true
    
    # Appeler la fonction avec n'importe quels arguments
    result = always_true(1, 2, 3)
    
    # Vérifier que le résultat est toujours True
    assert result is True


def test_is_self():
    """Test de la fonction is_self"""
    from epicevents.permissions.perm import is_self
    
    # Créer un utilisateur mock
    mock_user = MagicMock()
    mock_user.id = 1
    
    # Appeler is_self avec l'ID de l'utilisateur courant
    result = is_self(mock_user, mock_user)
    assert result is True
    
    # Appeler is_self avec un utilisateur différent (id 2)
    mock_user_2 = MagicMock()
    mock_user_2.id = 2
    result = is_self(mock_user, mock_user_2)
    assert result is False


@patch('epicevents.permissions.perm.get_all_permissions')
def test_has_permission_admin(mock_get_all_permissions):
    """Test de has_permission pour un admin (toujours autorisé)"""
    from epicevents.permissions.perm import has_permission
    
    # Créer un utilisateur mock avec un rôle 'admin'
    mock_user = MagicMock()
    mock_user.role.name = "admin"
    
    # Configurer le mock pour get_all_permissions
    permissions = {
        "admin": {
            "*": {
                "*": lambda *args: True
            }
        }
    }
    mock_get_all_permissions.return_value = permissions
    
    # Appeler has_permission avec l'utilisateur mocké
    result = has_permission(mock_user, "any_resource", "any_action")
    
    # Le résultat devrait être True (admin a toutes les permissions)
    assert result[0] is True


@patch('epicevents.permissions.perm.get_all_permissions')
def test_has_permission_specific_role(mock_get_all_permissions):
    """Test de has_permission pour un rôle spécifique avec une permission existante"""
    from epicevents.permissions.perm import has_permission
    
    # Créer un utilisateur mock avec un rôle 'sales'
    mock_user = MagicMock()
    mock_user.role.name = "sales"
    
    # Configurer le mock pour get_all_permissions
    permissions = {
        "sales": {
            "customer": {
                "read": lambda *args: True
            }
        }
    }
    mock_get_all_permissions.return_value = permissions
    
    # Appeler has_permission pour une permission que sales a
    result = has_permission(mock_user, "customer", "read")
    
    # Le résultat devrait être True
    assert result[0] is True
    
    # Appeler has_permission pour une permission que sales n'a pas
    result = has_permission(mock_user, "customer", "delete")
    
    # Le résultat devrait être False
    assert result[0] is False


def test_is_my_customer():
    """Test de la fonction is_my_customer"""
    from epicevents.permissions.perm import is_my_customer
    
    # Créer des mocks pour User, Customer et Contract
    mock_user = MagicMock()
    mock_user.id = 3
    
    mock_customer = MagicMock()
    mock_customer.team_contact_id_id = 3  # Même ID que l'utilisateur
    
    # Patcher les requêtes de base de données
    with patch('epicevents.models.customer.Customer.get_by_id', return_value=mock_customer):
        # Appeler is_my_customer
        result = is_my_customer(mock_user, 1)  # 1 est l'ID du client
    
    # Le résultat devrait être True car le client est attribué à l'utilisateur
    assert result[0] is True


def test_is_my_customer_wrong_user():
    """Test de is_my_customer quand le client est attribué à un autre utilisateur"""
    from epicevents.permissions.perm import is_my_customer
    
    # Créer des mocks pour User, Customer et Contract
    mock_user = MagicMock()
    mock_user.id = 3
    
    mock_customer = MagicMock()
    mock_customer.team_contact_id = 4  # ID différent de l'utilisateur
    
    mock_contract = MagicMock()
    mock_contract.customer_id = 1  # ID du client associé au contrat
    mock_contract.signed = True  # Le contrat est signé
    
    mock_event = MagicMock()
    mock_event.contract = mock_contract  # Associer le contrat à l'événement
    
    # Patch la méthode `exists` de `Customer.select().where()` pour retourner False
    with patch('epicevents.models.customer.Customer.select') as mock_select:
        # Configurer les mocks en chaîne pour select().where().exists()
        mock_select_query = MagicMock()
        mock_where_query = MagicMock()
        mock_where_query.exists.return_value = False  # exists() retourne False
        
        mock_select_query.where.return_value = mock_where_query
        mock_select.return_value = mock_select_query
        
        # Patcher la fonction `get_by_id` pour les autres appels de base de données
        with patch('epicevents.models.event.Event.get_by_id', return_value=mock_event):
            # Appeler is_my_customer
            result = is_my_customer(mock_user, 1)  # 1 est l'ID du client
            
    # Le résultat devrait être False car l'utilisateur n'est pas le commercial associé
    assert result[0] is False
    assert result[1] == "Vous n'êtes pas le commercial associé à ce client."


def test_is_owner():
    """Test de la fonction is_owner"""
    from epicevents.permissions.perm import is_owner
    
    # Créer un mock pour User
    mock_user = MagicMock()
    mock_user.id = 1
    
    # Créer un mock pour Customer avec un attribut team_contact_id
    mock_customer = MagicMock()
    mock_customer.team_contact_id = 1  # Même ID que l'utilisateur
    
    # Appeler is_owner avec le customer mocké
    result = is_owner(mock_user, mock_customer)
    
    # Vérifier que le résultat est True
    assert result is True
    
    # Tester avec un ID différent
    mock_customer.team_contact_id = 2  # ID différent de l'utilisateur
    result = is_owner(mock_user, mock_customer)
    
    # Vérifier que le résultat est False
    assert result is False


def test_get_all_permissions():
    """Test de la fonction get_all_permissions"""
    from epicevents.permissions.perm import get_all_permissions
    
    # Appeler la fonction
    permissions = get_all_permissions()
    
    # Vérifier que c'est une liste de dictionnaires
    assert isinstance(permissions, list)
    assert len(permissions) > 0
    
    # Vérifier la structure d'un élément de la liste
    assert "Rôle" in permissions[0]
    assert "Ressource" in permissions[0]
    assert "Action" in permissions[0]
    
    # Vérifier que l'admin a des permissions globales
    admin_perm = next((p for p in permissions if p["Rôle"] == "admin"), None)
    assert admin_perm is not None
    assert admin_perm["Ressource"] == "*"
    assert admin_perm["Action"] == "*"


@patch('epicevents.permissions.auth.verify_token')
@patch('epicevents.permissions.auth.console.print')
def test_debug_token(mock_console_print, mock_verify_token):
    """Test de la fonction debug_token"""
    from epicevents.permissions.auth import debug_token
    import datetime
    
    # Créer un payload valide
    payload = {
        'user_id': 1,
        'role': 'admin',
        'exp': int(datetime.datetime.now().timestamp()) + 3600
    }
    
    # Configurer le mock pour verify_token
    mock_verify_token.return_value = payload
    
    # Appeler debug_token
    debug_token()
    
    # Vérifier que les méthodes ont été appelées
    mock_verify_token.assert_called_once()
    # Vérifier que console.print a été appelé
    assert mock_console_print.call_count > 0


@patch('epicevents.permissions.auth.verify_token')
@patch('epicevents.permissions.auth.console.print')
def test_debug_token_no_token(mock_console_print, mock_verify_token):
    """Test de debug_token quand aucun token n'existe"""
    from epicevents.permissions.auth import debug_token
    
    # Configurer le mock pour verify_token
    mock_verify_token.return_value = None
    
    # Appeler debug_token
    debug_token()
    
    # Vérifier que verify_token a été appelé
    mock_verify_token.assert_called_once()
    
    # Comme il n'y a pas de token valide, console.print ne devrait pas être appelé
    # Ou il devrait y avoir un message différent
    # Cette assertion peut être différente selon votre implémentation
    mock_console_print.assert_not_called()


@patch('epicevents.permissions.auth.get_all_permissions')
@patch('epicevents.permissions.auth.display_list')
def test_debug_permissions(mock_display_list, mock_get_all_permissions):
    """Test de la fonction debug_permissions"""
    from epicevents.permissions.auth import debug_permissions
    
    # Préparer des données de test pour get_all_permissions
    mock_permissions = [
        {"Rôle": "admin", "Ressource": "*", "Action": "*"},
        {"Rôle": "sales", "Ressource": "customer", "Action": "read, update"}
    ]
    mock_get_all_permissions.return_value = mock_permissions
    
    # Appeler debug_permissions
    debug_permissions()
    
    # Vérifier que get_all_permissions a été appelé
    mock_get_all_permissions.assert_called_once()
    
    # Vérifier que display_list a été appelé avec les bons arguments
    mock_display_list.assert_called_once()
    args, kwargs = mock_display_list.call_args
    assert kwargs.get('title') == "Permissions disponibles"
    assert kwargs.get('items') == mock_permissions

