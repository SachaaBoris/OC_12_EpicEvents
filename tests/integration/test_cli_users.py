import pytest
from typer.testing import CliRunner
from epicevents.cli.users import app
from epicevents.models.user import User
from epicevents.models.role import Role
from epicevents.models.database import BaseModel
from epicevents.permissions.auth import AuthenticationError
from peewee import DoesNotExist


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


def test_cli_login_logout(runner, create_test_data, monkeypatch):
    """Test des commandes login & logout."""
    
    # Exécuter la commande login
    result = runner.invoke(app, ["login", "-u", "admin", "-p", "password123"])
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "connecté" in result.stdout.lower() or "logged in" in result.stdout.lower()
    
    # Exécuter la commande logout
    result = runner.invoke(app, ["logout"])
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "déconnecté" in result.stdout.lower() or "logged out" in result.stdout.lower()


def test_cli_login_failure(runner, create_test_data, monkeypatch):
    """Test de la commande login avec des identifiants incorrects."""

    # Exécuter la commande login avec des identifiants incorrects
    result = runner.invoke(app, ["login", "-u", "bad", "-p", "bad"])

    # Vérifier que la commande a échoué avec un message d'erreur
    assert "utilisateur non trouvé" in result.stdout.lower() or "invalid" in result.stdout.lower()


def test_cli_create_user(runner, create_test_data, monkeypatch):
    """Test de création d'un utilisateur via la CLI."""
    # Données de test
    data = create_test_data
    admin_user = data["users"]["admin"]
    admin_role = data["roles"]["admin"]
    
    # Exécuter la commande de création d'utilisateur
    result = runner.invoke(
        app, 
        [
            "create",
            "-u", "newuser",
            "-p", "newpassword",
            "-e", "new@example.com",
            "-fn", "New",
            "-ln", "User",
            "-ph", "0123456780",
            "-r", str(admin_role.id)
        ],
        obj=admin_user
    )
       
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "créé avec succès" in result.stdout.lower()
    
    # Vérifier que l'utilisateur a bien été créé dans la base de données
    created_user = User.select().where(User.username == "newuser").first()
    assert created_user is not None
    assert created_user.email == "new@example.com"
    assert created_user.first_name == "New"
    assert created_user.last_name == "User"
    assert created_user.phone == "0123456780"
    assert created_user.role.id == admin_role.id


def test_cli_create_user_duplicate(runner, create_test_data, monkeypatch):
    """Test la création d'un utilisateur avec un nom d'utilisateur ou email existant."""
    # Données de test
    data = create_test_data
    admin_user = data["users"]["admin"]
    admin_role = data["roles"]["admin"]
    
    # Exécuter la commande de création d'utilisateur avec un username existant
    result = runner.invoke(
        app, 
        [
            "create",
            "-u", "admin",  # Username déjà existant
            "-p", "newpassword",
            "-e", "new@example.com",
            "-fn", "New",
            "-ln", "User",
            "-ph", "0123456780",
            "-r", str(admin_role.id)
        ],
        obj=admin_user
    )
    
    # Vérifier que la commande a échoué avec un message d'erreur
    assert "déjà enregistré" in result.stdout.lower()


def test_cli_list_users(runner, create_test_data, monkeypatch):
    """Test l'affichage de la liste des utilisateurs via la CLI."""
    # Données de test
    data = create_test_data
    admin_user = data["users"]["admin"]
    
    # Exécuter la commande de liste des utilisateurs
    result = runner.invoke(app, ["list"], obj=admin_user)
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "liste des utilisateurs" in result.stdout.lower() or "user list" in result.stdout.lower()
    
    # Vérifier que les utilisateurs sont affichés
    for user_key in ["admin", "manager", "sales", "support"]:
        user = data["users"][user_key]
        assert user.username in result.stdout.lower()


def test_cli_read_user(runner, create_test_data, monkeypatch):
    """Test la lecture des détails d'un utilisateur via la CLI."""
    # Données de test
    data = create_test_data
    admin_user = data["users"]["admin"]
    user_to_read = data["users"]["manager"]
    monkeypatch.setattr("epicevents.permissions.auth.is_logged", lambda: admin_user)
    
    # Exécuter la commande de lecture d'un utilisateur
    result = runner.invoke(app, ["read", str(user_to_read.id)], obj=admin_user)
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert user_to_read.username in result.stdout
    assert user_to_read.email in result.stdout
    
    # Test de lecture d'un utilisateur inexistant
    invalid_id = 9999
    result_invalid = runner.invoke(app, ["read", str(invalid_id)], obj=admin_user)
    
    # Vérifier que l'erreur est correctement gérée
    assert f"l'utilisateur id {invalid_id} n'existe pas" in result_invalid.stdout.lower()


def test_cli_update_user(runner, create_test_data, monkeypatch):
    """Test la mise à jour d'un utilisateur via la CLI."""
    # Données de test
    data = create_test_data
    admin_user = data["users"]["admin"]
    user_to_update = data["users"]["sales"]
    
    # Nouvelles valeurs pour la mise à jour
    new_email = "updated@example.com"
    new_phone = "0987654321"
    
    # Exécuter la commande de mise à jour d'utilisateur
    result = runner.invoke(
        app, 
        [
            "update", 
            str(user_to_update.id), 
            "-e", new_email,
            "-ph", new_phone
        ],
        obj=admin_user
    )
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "mis à jour" in result.stdout.lower() or "updated" in result.stdout.lower()
    
    # Vérifier que la mise à jour a été effectuée dans la base de données
    updated_user = User.get_by_id(user_to_update.id)
    assert updated_user.email == new_email
    assert updated_user.phone == new_phone


def test_cli_delete_user_confirm(runner, create_test_data, monkeypatch):
    """Test la suppression d'un utilisateur via la CLI avec confirmation."""
    # Données de test
    data = create_test_data
    admin_user = data["users"]["admin"]
    
    # Créer un utilisateur temporaire à supprimer
    temp_user = User.create(
        username="temp",
        email="temp@example.com",
        first_name="Temp",
        last_name="User",
        phone="0123456789",
        password="password123",
        role=data["roles"]["support"]
    )
    
    # Patch la fonction Confirm.ask pour simuler une réponse "oui"
    monkeypatch.setattr("epicevents.cli.users.Confirm.ask", lambda message: True)
    
    # Exécuter la commande de suppression
    result = runner.invoke(app, ["delete", str(temp_user.id)], obj=admin_user)
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "supprimé" in result.stdout.lower() or "deleted" in result.stdout.lower()
    
    # Vérifier que l'utilisateur n'existe plus
    user_exists = User.select().where(User.id == temp_user.id).exists()
    assert user_exists is False


def test_cli_delete_user_abort(runner, create_test_data, monkeypatch):
    """Test l'annulation de la suppression d'un utilisateur via la CLI."""
    # Données de test
    data = create_test_data
    admin_user = data["users"]["admin"]
    user_to_delete = data["users"]["support"]
    
    # Patch la fonction Confirm.ask pour simuler une réponse "non"
    monkeypatch.setattr("epicevents.cli.users.Confirm.ask", lambda message: False)
    
    # Exécuter la commande de suppression
    result = runner.invoke(app, ["delete", str(user_to_delete.id)], obj=admin_user)
    
    # Vérifier que la commande a été annulée
    assert "annulée" in result.stdout.lower() or "cancelled" in result.stdout.lower()
    
    # Vérifier que l'utilisateur existe toujours
    user_exists = User.select().where(User.id == user_to_delete.id).exists()
    assert user_exists is True


def test_cli_delete_user_not_found(runner, create_test_data, monkeypatch):
    """Test la suppression d'un utilisateur inexistant via la CLI."""
    # Données de test
    data = create_test_data
    admin_user = data["users"]["admin"]
    
    # ID d'utilisateur inexistant
    invalid_id = 9999
    
    # Exécuter la commande de suppression
    result = runner.invoke(app, ["delete", str(invalid_id)], obj=admin_user)
    
    # Vérifier que l'erreur est correctement gérée
    assert f"l'utilisateur id {invalid_id} n'existe pas" in result.stdout.lower()
