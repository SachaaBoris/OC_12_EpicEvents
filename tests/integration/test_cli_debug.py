import pytest
import os
import json
from datetime import datetime, timedelta, timezone
from typer.testing import CliRunner
from epicevents.models.user import User
from epicevents.models.role import Role
from epicevents.models.database import BaseModel
from epicevents.permissions.auth import generate_token
from epicevents.permissions.auth import remove_token
from epicevents.permissions.auth import get_all_permissions
from epicevents.cli.debug import app
from epicevents.cli.debug import list_commands
from epicevents.cli.debug import debug_token
from epicevents.cli.debug import debug_permissions


@pytest.fixture
def create_test_data(setup_db_tables):
    """Crée des données de test dans la base de données en mémoire."""
    # Créer des rôles
    admin_role = Role.create(name="admin")
    management_role = Role.create(name="management")
    sales_role = Role.create(name="sales")
    support_role = Role.create(name="support")
    
    # Créer des utilisateurs
    admin_user = User.create(
        username="admin",
        email="admin@epicevents.com",
        first_name="Admin",
        last_name="User",
        phone="0123456789",
        password="password123",
        role=admin_role
    )
    
    manager_user = User.create(
        username="manager",
        email="manager@epicevents.com",
        first_name="Manager",
        last_name="User",
        phone="0123456788",
        password="password123",
        role=management_role
    )
    
    sales_user = User.create(
        username="sales",
        email="sales@epicevents.com",
        first_name="Sales",
        last_name="User",
        phone="0123456787",
        password="password123",
        role=sales_role
    )
    
    support_user = User.create(
        username="support",
        email="support@epicevents.com",
        first_name="Support",
        last_name="User",
        phone="0123456786",
        password="password123",
        role=support_role
    )
    
    return {
        "roles": {
            "admin": admin_role,
            "management": management_role,
            "sales": sales_role,
            "support": support_role
        },
        "users": {
            "admin": admin_user,
            "manager": manager_user,
            "sales": sales_user,
            "support": support_user
        }
    }

# Tests pour les commandes debug
def test_debug_commands_ok(runner, create_test_data, monkeypatch):
    """Test de la fonction list_commands avec un utilisateur admin."""
    data = create_test_data
    support_user = data["users"]["support"]
    
    # Authentifier l'utilisateur en générant un token
    token = generate_token(support_user)
    
    # Exécuter la commande
    result = runner.invoke(app, ["commands"], obj=support_user)
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "liste des commandes" in result.stdout.lower()


def test_debug_token_ok(runner, create_test_data):
    """Test de la fonction debug_token avec un utilisateur admin."""
    data = create_test_data
    admin_user = data["users"]["admin"]

    # Authentifier l'utilisateur en générant un token
    token = generate_token(admin_user)

    # Exécuter la commande debug token
    result = runner.invoke(app, ["token"], obj=admin_user)

    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "token expire le" in result.stdout.lower()


def test_debug_token_ko(runner, create_test_data, monkeypatch):
    """Test de debug_token quand aucun token n'existe."""
    data = create_test_data
    manager_user = data["users"]["manager"]
        
    # Authentifier l'utilisateur en générant un token
    token = generate_token(manager_user)

    # Exécuter la commande debug token
    result = runner.invoke(app, ["token"], obj=manager_user)

    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "token expire le" in result.stdout.lower()


def test_debug_permissions_ok(runner, create_test_data, monkeypatch):
    """Test de la fonction debug_permissions avec un utilisateur admin."""
    data = create_test_data
    admin_user = data["users"]["admin"]

    # Authentifier l'utilisateur en générant un token
    token = generate_token(admin_user)
    
    # Exécuter la commande
    result = runner.invoke(app, ["permissions"], obj=admin_user)
        
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "permissions disponibles" in result.stdout.lower()

