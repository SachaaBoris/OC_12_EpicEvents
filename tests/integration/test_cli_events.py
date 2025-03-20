import pytest
from datetime import datetime, timedelta
from typer.testing import CliRunner
from epicevents.cli.events import app
from epicevents.models.event import Event
from epicevents.models.contract import Contract
from epicevents.models.customer import Customer
from epicevents.models.user import User
from epicevents.models.company import Company
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
    
    # Créer des entreprises
    acme_company = Company.create(name="ACME")
    globex_company = Company.create(name="Globex")
    
    # Créer des clients
    john_customer = Customer.create(
        email="john@example.com",
        first_name="John",
        last_name="Doe",
        phone="0987654321",
        company=acme_company,
        team_contact_id=sales_user
    )
    
    jane_customer = Customer.create(
        email="jane@example.com",
        first_name="Jane",
        last_name="Smith",
        phone="0987654322",
        company=globex_company,
        team_contact_id=sales_user
    )
    
    # Créer des contrats
    contract1 = Contract.create(
        customer=john_customer,
        signed=True,
        amount_total=1000.0,
        amount_due=500.0,
        team_contact_id=manager_user
    )
    
    contract2 = Contract.create(
        customer=jane_customer,
        signed=True,
        amount_total=2000.0,
        amount_due=2000.0,
        team_contact_id=manager_user
    )
    
    # Créer des événements
    future_date1 = datetime.now() + timedelta(days=30)
    future_date2 = datetime.now() + timedelta(days=45)
    
    event1 = Event.create(
        contract=contract1,
        name="Conference",
        location="Paris",
        event_date=future_date1,
        attendees=100,
        notes="Notes for conference",
        team_contact_id=support_user
    )
    
    event2 = Event.create(
        contract=contract2,
        name="Workshop",
        location="Lyon",
        event_date=future_date2,
        attendees=50,
        notes="Notes for workshop",
        team_contact_id=support_user
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
        },
        "companies": {
            "acme": acme_company,
            "globex": globex_company
        },
        "customers": {
            "john": john_customer,
            "jane": jane_customer
        },
        "contracts": {
            "contract1": contract1,
            "contract2": contract2
        },
        "events": {
            "event1": event1,
            "event2": event2
        },
        "future_dates": {
            "date1": future_date1,
            "date2": future_date2
        }
    }


def test_cli_create_event(runner, create_test_data, monkeypatch):
    """Test la création d'un événement via la CLI."""
    # Données de test
    data = create_test_data
    support_user = data["users"]["support"]
    contract = data["contracts"]["contract1"]
    future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Exécuter la commande de création d'événement
    result = runner.invoke(
        app, 
        [
            "create",
            "-ct", str(contract.id),
            "-t", "New Event",
            "-d", future_date,
            "-l", "Paris",
            "-a", "100",
            "-n", "Test notes",
            "-u", str(support_user.id)
        ],
        obj=support_user
    )
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "événement créé :" in result.stdout.lower()
    
    # Vérifier que l'événement a bien été créé dans la base de données
    created_event = Event.select().where(Event.name == "New Event").first()
    assert created_event is not None
    assert created_event.contract.id == contract.id
    assert created_event.team_contact_id.id == support_user.id


def test_cli_list_events(runner, create_test_data, monkeypatch):
    """Test l'affichage de la liste des événements via la CLI."""
    # Données de test
    data = create_test_data
    support_user = data["users"]["support"]
    event1 = data["events"]["event1"]
    
    # Exécuter la commande de liste des événements
    result = runner.invoke(app, ["list"], obj=support_user)
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "Liste des événements" in result.stdout


def test_cli_read_event(runner, create_test_data, monkeypatch):
    """Test la lecture des détails d'un événement via la CLI."""
    # Données de test
    data = create_test_data
    support_user = data["users"]["support"]
    event = data["events"]["event1"]
    
    # Exécuter la commande de lecture d'un événement
    result = runner.invoke(app, ["read", str(event.id)], obj=support_user)
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert f"Événement {event.id}" in result.stdout or f"Event {event.id}" in result.stdout
    
    # Test de lecture d'un événement inexistant
    invalid_id = 9999
    result_invalid = runner.invoke(app, ["read", str(invalid_id)], obj=support_user)
    
    # Vérifier que l'erreur est correctement gérée
    assert "n'existe pas" in result_invalid.stdout or "introuvable" in result_invalid.stdout


def test_cli_update_event(runner, create_test_data, monkeypatch):
    """Test la mise à jour d'un événement via la CLI."""
    # Données de test
    data = create_test_data
    support_user = data["users"]["support"]
    event = data["events"]["event1"]
    
    # Date future pour éviter l'erreur de validation
    future_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    
    # Nouvelles valeurs pour la mise à jour
    new_title = "Updated Event"
    new_location = "Bordeaux"
    
    # Exécuter la commande de mise à jour d'événement
    result = runner.invoke(
        app, 
        [
            "update", 
            str(event.id), 
            "-t", new_title,
            "-l", new_location,
            "-d", future_date
        ],
        obj=support_user
    )
    
    # Vérifier que la commande s'est exécutée avec succès
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "mis à jour" in result.stdout.lower()
    
    # Vérifier que la mise à jour a été effectuée dans la base de données
    updated_event = Event.get_by_id(event.id)
    assert updated_event.name == new_title
    assert updated_event.location == new_location


def test_cli_delete_event_confirm(runner, create_test_data, monkeypatch):
    """Test la suppression d'un événement via la CLI avec confirmation."""
    # Données de test
    data = create_test_data
    admin_user = data["users"]["admin"]
    event = data["events"]["event1"]
    
    # Patch la fonction Confirm.ask pour simuler une réponse "oui"
    monkeypatch.setattr("epicevents.cli.events.Confirm.ask", lambda message: True)
    
    # Exécuter la commande de suppression
    result = runner.invoke(app, ["delete", str(event.id)], obj=admin_user)

    # Vérifier que la commande s'est exécutée avec succès et que l'événement a été supprimé
    assert result.exit_code == 0, f"Erreur: {result.stdout}"
    assert "supprimé" in result.stdout.lower()
    
    # Vérifier que l'événement n'existe plus
    event_exists = Event.select().where(Event.id == event.id).exists()
    assert event_exists is False


def test_delete_event_abort(runner, create_test_data, monkeypatch):
    """Test l'annulation de la suppression d'un événement via la CLI."""
    # Données de test
    data = create_test_data
    admin_user = data["users"]["admin"]
    event = data["events"]["event2"]
    
    # Patch la fonction Confirm.ask pour simuler une réponse "non"
    monkeypatch.setattr("epicevents.cli.events.Confirm.ask", lambda message: False)
    
    # Exécuter la commande de suppression
    result = runner.invoke(app, ["delete", str(event.id)], obj=admin_user)
    
    # Vérifier que la commande a été annulée
    assert "annulée" in result.stdout.lower()
    
    # Vérifier que l'événement existe toujours
    event_exists = Event.select().where(Event.id == event.id).exists()
    assert event_exists is True


def test_create_event_validation_error(runner, create_test_data, monkeypatch):
    """Test la gestion des erreurs de validation lors de la création d'un événement."""
    # Données de test
    data = create_test_data
    support_user = data["users"]["support"]
    contract = data["contracts"]["contract1"]

    # Date passée qui devrait échouer à la validation
    past_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Exécuter la commande de création d'événement avec date passée
    result = runner.invoke(
        app, 
        [
            "create",
            "-ct", str(contract.id),
            "-t", "Invalid Event",
            "-d", past_date,  # Date dans le passé qui devrait être rejetée
            "-l", "Paris",
            "-a", "100",
            "-n", "Test notes",
            "-u", str(support_user.id)
        ],
        obj=support_user
    )
    
    # Vérifier que la commande a échoué avec un message d'erreur
    assert "erreur" in result.stdout.lower() or "error" in result.stdout.lower()
    
    # Vérifier que l'événement n'a pas été créé
    event_exists = Event.select().where(Event.name == "Invalid Event").exists()
    assert event_exists is False


def test_list_events_empty(runner, create_test_data, monkeypatch):
    """Test l'affichage d'un message approprié quand aucun événement n'existe."""
    # Données de test
    data = create_test_data
    support_user = data["users"]["support"]
    
    # Supprimer tous les événements pour tester le cas vide
    Event.delete().execute()
    
    # Exécuter la commande de liste des événements
    result = runner.invoke(app, ["list"], obj=support_user)
    
    # Vérifier qu'un message approprié est affiché
    assert "aucun événement" in result.stdout.lower() or "aucun event" in result.stdout.lower()
