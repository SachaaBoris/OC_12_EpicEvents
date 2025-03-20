import os
import pytest
from datetime import datetime
from typer.testing import CliRunner
from epicevents.cli.customers import app
from epicevents.models.customer import Customer
from epicevents.models.company import Company
from epicevents.models.user import User
from epicevents.models.role import Role
from epicevents.models.database import BaseModel
from peewee import DoesNotExist


@pytest.fixture
def create_test_data(setup_db_tables, monkeypatch):
    """Crée des données de test dans la base de données en mémoire."""
   
    # Créer des rôles
    admin_role = Role.create(name="admin")
    management_role = Role.create(name="management")
    sales_role = Role.create(name="sales")
    support_role = Role.create(name="support")
    
    # Créer un commercial
    sales_user = User.create(
        username="sales",
        email="sales@epicevents.com",
        first_name="Sales",
        last_name="User",
        phone="0123456789",
        password="password123",
        role=sales_role
    )
    
    # Créer un second commercial pour les tests
    sales_user2 = User.create(
        username="sales2",
        email="sales2@epicevents.com",
        first_name="Sales",
        last_name="User",
        phone="0123456788",
        password="password123",
        role=sales_role
    )
    
    # Créer une entreprise
    company = Company.create(name="Test Company")
    
    # Créer un client
    customer = Customer.create(
        email="client@test.com",
        first_name="John",
        last_name="Doe",
        phone="0987654321",
        company=company,
        team_contact_id=sales_user
    )
    
    return {
        "admin_role": admin_role,
        "management_role": management_role,
        "sales_role": sales_role,
        "support_role": support_role,
        "sales_user": sales_user,
        "sales_user2": sales_user2,
        "company": company,
        "customer": customer
    }


def test_cli_create_customer(runner, create_test_data, monkeypatch):
    """Test la création d'un client via la CLI."""
    # Données de test
    data = create_test_data
    sales_user = data["sales_user"]
    company = data["company"]
    
    # Exécuter la commande de création de client
    result = runner.invoke(
        app, 
        [
            "create", 
            "-fn", "Alice", 
            "-ln", "Smith", 
            "-e", "alice@example.com", 
            "-p", "0712345678", 
            "-c", company.name
        ],
        obj=sales_user
    )
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "Alice SMITH créé avec succès" in result.stdout
    
    # Vérifier que le client a bien été créé dans la base de données
    created_customer = Customer.select().where(Customer.email == "alice@example.com").first()
    assert created_customer is not None


def test_cli_list_customers(runner, create_test_data, monkeypatch):
    """Test l'affichage de la liste des clients via la CLI."""
    # Données de test
    data = create_test_data
    sales_user = data["sales_user"]
    
    # Exécuter la commande de liste des clients
    result = runner.invoke(app, ["list"], obj=sales_user)
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "Liste des clients" in result.stdout


def test_cli_read_customer(runner, create_test_data, monkeypatch):
    """Test la lecture des détails d'un client via la CLI."""
    # Données de test
    data = create_test_data
    sales_user = data["sales_user"]
    customer = data["customer"]
    
    # Exécuter la commande de lecture d'un client
    result = runner.invoke(app, ["read", str(customer.id)], obj=sales_user)

    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert f"Client" in result.stdout
    
    # Test de lecture d'un client inexistant
    invalid_id = 9999
    result_invalid = runner.invoke(app, ["read", str(invalid_id)], obj=sales_user)
    
    # Vérifier que l'erreur est correctement gérée
    assert f"Client ID {invalid_id} introuvable" in result_invalid.stdout


def test_cli_update_customer(runner, create_test_data, monkeypatch):
    """Test la mise à jour d'un client via la CLI."""
    # Données de test
    data = create_test_data
    sales_user = data["sales_user"]
    sales_user2 = data["sales_user2"]
    customer = data["customer"]
    
    # Nouvelles valeurs pour la mise à jour
    new_email = "john.updated@test.com"
    new_phone = "0711223344"
    
    # Exécuter la commande de mise à jour de client
    result = runner.invoke(
        app, 
        [
            "update", 
            str(customer.id), 
            "-e", new_email, 
            "-p", new_phone,
            "-u", str(sales_user2.id)
        ],
        obj=sales_user
    )
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert f"Client {customer.id}" in result.stdout
    assert "mis à jour avec succès" in result.stdout
    
    # Vérifier que la mise à jour a été effectuée dans la base de données
    updated_customer = Customer.get_by_id(customer.id)
    assert updated_customer.email == new_email
    assert updated_customer.phone == new_phone


def test_cli_delete_customer_confirm(runner, create_test_data, monkeypatch):
    """Test la suppression d'un client via la CLI avec confirmation."""
    # Données de test
    data = create_test_data
    sales_user = data["sales_user"]
    customer = data["customer"]
    
    # Patch la fonction Confirm.ask pour simuler une réponse "oui"
    monkeypatch.setattr("epicevents.cli.customers.Confirm.ask", lambda message: True)
    
    # Exécuter la commande de suppression
    result = runner.invoke(app, ["delete", str(customer.id)], obj=sales_user)
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "supprimé" in result.stdout
    
    # Vérifier que le client n'existe plus
    customer_exists = Customer.select().where(Customer.id == customer.id).exists()
    assert customer_exists is False


def test_delete_customer_abort(runner, create_test_data, monkeypatch):
    """Test l'annulation de la suppression d'un client via la CLI."""
    # Données de test
    data = create_test_data
    sales_user = data["sales_user"]
    company = data["company"]
    
    # Créer un nouveau client pour le test
    new_customer = Customer.create(
        email="temp@test.com",
        first_name="Temp",
        last_name="User",
        phone="0987654322",
        company=company,
        team_contact_id=sales_user
    )
 
    # Patch la fonction Confirm.ask pour simuler une réponse "non"
    monkeypatch.setattr("epicevents.cli.customers.Confirm.ask", lambda message: False)
    
    # Exécuter la commande de suppression
    result = runner.invoke(app, ["delete", str(new_customer.id)], obj=sales_user)
    
    # Vérifier que la commande a été annulée
    assert "Opération annulée" in result.stdout
    
    # Vérifier que le client existe toujours
    customer_exists = Customer.select().where(Customer.id == new_customer.id).exists()
    assert customer_exists is True


def test_list_customers_filtered_no_result(runner, create_test_data, monkeypatch):
    """Test l'affichage de la liste des clients avec filtre ne donnant aucun résultat."""
    # Données de test
    data = create_test_data
    
    # Créer un utilisateur admin qui n'a pas de clients assignés
    admin_user = User.create(
        username="admin",
        email="admin@epicevents.com",
        first_name="Admin",
        last_name="User",
        phone="0123456787",
        password="password123",
        role=data["admin_role"]
    )
    
    # S'assurer que tous les clients ont un commercial assigné
    # pour que le filtre admin ne retourne aucun résultat
    for customer in Customer.select():
        if not customer.team_contact_id:
            customer.team_contact_id = data["sales_user"]
            customer.save()
    
    # Exécuter la commande de liste des clients avec filtre
    result = runner.invoke(app, ["list", "--fi"], obj=admin_user)
    
    # Vérifier qu'un message d'absence de clients est affiché
    assert "Aucun client" in result.stdout or "aucun client" in result.stdout.lower()
