import os
import pytest
from typer.testing import CliRunner
from epicevents.cli.contracts import app
from epicevents.models.contract import Contract
from epicevents.models.customer import Customer
from epicevents.models.user import User
from epicevents.models.company import Company
from epicevents.models.role import Role
from epicevents.models.database import BaseModel
from peewee import DoesNotExist


@pytest.fixture
def create_test_data(setup_db_tables):
    """Crée des données de test dans la base de données en mémoire."""
    # Créer des rôles
    admin_role = Role.create(name="admin")
    management_role = Role.create(name="management")
    sales_role = Role.create(name="sales")
    support_role = Role.create(name="support")
    
    # Créer un utilisateur de gestion
    manager = User.create(
        username="manager",
        email="manager@epicevents.com",
        first_name="Manager",
        last_name="Test",
        phone="0123456789",
        password="password123",
        role=management_role
    )
    
    # Créer un commercial
    sales_user = User.create(
        username="sales",
        email="sales@epicevents.com",
        first_name="Sales",
        last_name="Test",
        phone="0123456789",
        password="password123",
        role=sales_role
    )
    
    # Créer une entreprise
    company = Company.create(name="Test Company")
    
    # Créer un client
    customer = Customer.create(
        email="client@test.com",
        first_name="Client",
        last_name="Test",
        phone="0987654321",
        company=company,
        team_contact_id=sales_user
    )
    
    # Créer un contrat de test
    contract = Contract.create(
        customer=customer,
        signed=True,
        amount_total=1000.0,
        amount_due=500.0,
        team_contact_id=manager
    )
    
    return {
        "admin_role": admin_role,
        "management_role": management_role,
        "sales_role": sales_role,
        "support_role": support_role,
        "manager": manager,
        "sales_user": sales_user,
        "company": company,
        "customer": customer,
        "contract": contract
    }


def test_cli_create_contract(runner, create_test_data, monkeypatch):
    """Test la création d'un contrat via la CLI."""
    # Données de test
    data = create_test_data
    manager = data["manager"]
    customer = data["customer"]
    
    # Exécuter la commande de création de contrat
    result = runner.invoke(
        app, 
        ["create", "-c", str(customer.id), "-st", "2000", "-sd", "1000", "-si"],
        obj=manager  # Fournir l'objet utilisateur directement
    )
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert f"créé pour {customer.first_name} {customer.last_name}" in result.stdout
    
    # Vérifier que le contrat a bien été créé dans la base de données
    created_contract = Contract.select().where(
        (Contract.customer_id == customer.id) & 
        (Contract.amount_total == 2000)
    ).first()
    
    assert created_contract is not None
    assert created_contract.amount_due == 1000


def test_cli_list_contracts(runner, create_test_data, monkeypatch):
    """Test l'affichage de la liste des contrats via la CLI."""
    # Données de test
    data = create_test_data
    manager = data["manager"]
    
    # Exécuter la commande de liste des contrats
    result = runner.invoke(app, ["list"], obj=manager)
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "Liste des contrats" in result.stdout


def test_cli_read_contract(runner, create_test_data, monkeypatch):
    """Test la lecture des détails d'un contrat via la CLI."""
    # Données de test
    data = create_test_data
    manager = data["manager"]
    contract = data["contract"]
    
    # Exécuter la commande de lecture d'un contrat
    result = runner.invoke(app, ["read", str(contract.id)], obj=manager)
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert f"Contrat {contract.id}" in result.stdout
    
    # Test de lecture d'un contrat inexistant
    invalid_id = 9999
    result_invalid = runner.invoke(app, ["read", str(invalid_id)], obj=manager)
    
    # Vérifier que l'erreur est correctement gérée
    assert f"Le contrat ID {invalid_id} n'existe pas" in result_invalid.stdout


def test_cli_update_contract(runner, create_test_data, monkeypatch):
    """Test la mise à jour d'un contrat via la CLI."""
    # Données de test
    data = create_test_data
    manager = data["manager"]
    contract = data["contract"]
    
    # Valeurs initiales
    initial_amount_due = contract.amount_due
    new_amount_due = 300.0
    
    # Exécuter la commande de mise à jour de contrat
    result = runner.invoke(
        app, 
        ["update", str(contract.id), "-sd", str(new_amount_due)],
        obj=manager
    )
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert f"Contrat {contract.id} mis à jour avec succès" in result.stdout
    
    # Vérifier que la mise à jour a été effectuée dans la base de données
    updated_contract = Contract.get_by_id(contract.id)
    assert updated_contract.amount_due == new_amount_due
    assert updated_contract.amount_due != initial_amount_due


def test_cli_delete_contract_confirm(runner, create_test_data, monkeypatch):
    """Test la confirmation de suppression d'un contrat via la CLI."""
    # Données de test
    data = create_test_data
    manager = data["manager"]
    contract = data["contract"]
    
    # Patch la fonction Confirm.ask pour simuler une réponse "non"
    monkeypatch.setattr("epicevents.cli.contracts.Confirm.ask", lambda message: False)
    
    # Exécuter la commande de suppression
    result = runner.invoke(app, ["delete", str(contract.id)], obj=manager)
 
    # Vérifier que la commande a été annulée
    assert "Opération annulée" in result.stdout
    
    # Vérifier que le contrat existe toujours
    contract_exists = Contract.select().where(Contract.id == contract.id).exists()
    assert contract_exists is True


def test_delete_contract_success(runner, create_test_data, monkeypatch):
    """Test la suppression réussie d'un contrat via la CLI."""
    # Données de test
    data = create_test_data
    manager = data["manager"]
    contract = data["contract"]
    
    # Patch la fonction Confirm.ask pour simuler une réponse "oui"
    monkeypatch.setattr("epicevents.cli.contracts.Confirm.ask", lambda message: True)
    
    # Exécuter la commande de suppression
    result = runner.invoke(app, ["delete", str(contract.id)], obj=manager)
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert f"Contrat {contract.id} supprimé avec succès" in result.stdout
    
    # Vérifier que le contrat n'existe plus
    contract_exists = Contract.select().where(Contract.id == contract.id).exists()
    assert contract_exists is False


def test_create_contract_invalid_customer(runner, create_test_data, monkeypatch):
    """Test la création d'un contrat avec un client invalide."""
    # Données de test
    data = create_test_data
    manager = data["manager"]
    
    # Désactiver la validation de signature
    monkeypatch.setattr(Contract, "_validate_signed", lambda self: None)
    
    # ID de client inexistant
    invalid_customer_id = 9999
    
    # Exécuter la commande de création avec un client invalide
    result = runner.invoke(
        app, 
        ["create", "-c", str(invalid_customer_id), "-st", "1000", "-sd", "500", "-si"],
        obj=manager
    )
    
    # Vérifier que la commande affiche une erreur appropriée
    assert f"Le client ID {invalid_customer_id} n'existe pas" in result.stdout
