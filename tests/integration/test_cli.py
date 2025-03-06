import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from peewee import DoesNotExist
import datetime

# Fixture pour le runner CLI
@pytest.fixture
def runner():
    return CliRunner()

# Classes dummy pour simuler les modèles
class DummyRole:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __lt__(self, other):
        return self.name < other.name

class DummyUser:
    def __init__(self, id, username, email, first_name, last_name, phone, role):
        self.id = id
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.role = role
        self.password = "hashed_password"

    def __lt__(self, other):
        return self.username < other.username

class DummyCompany:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __lt__(self, other):
        return self.name < other.name

class DummyCustomer:
    def __init__(self, id, first_name, last_name, email, phone, company, team_contact_id, date_created=None, date_updated=None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.company = company
        self.team_contact_id = team_contact_id
        self.date_created = date_created or datetime.datetime.now()
        self.date_updated = date_updated or datetime.datetime.now()

    def __lt__(self, other):
        return self.last_name < other.last_name

class DummyContract:
    def __init__(self, id, customer, signed, amount_total, amount_due, team_contact_id, date_created=None, date_updated=None):
        self.id = id
        self.customer = customer
        self.signed = signed
        self.amount_total = amount_total
        self.amount_due = amount_due
        self.team_contact_id = team_contact_id
        self.date_created = date_created or datetime.datetime.now()
        self.date_updated = date_updated or datetime.datetime.now()

    def __lt__(self, other):
        return self.id < other.id

class DummyEvent:
    def __init__(self, id, contract, name, location, event_date, attendees, notes, team_contact_id, date_created=None, date_updated=None):
        self.id = id
        self.contract = contract
        self.name = name
        self.location = location
        self.event_date = event_date
        self.attendees = attendees
        self.notes = notes
        self.team_contact_id = team_contact_id
        self.date_created = date_created or datetime.datetime.now()
        self.date_updated = date_updated or datetime.datetime.now()

    def __lt__(self, other):
        return self.event_date < other.event_date

# Fixtures pour les objets dummy
@pytest.fixture
def dummy_roles():
    return {
        "admin": DummyRole(1, "admin"),
        "management": DummyRole(2, "management"),
        "sales": DummyRole(3, "sales"),
        "support": DummyRole(4, "support")
    }

@pytest.fixture
def dummy_users(dummy_roles):
    return {
        "admin": DummyUser(1, "admin", "admin@example.com", "Admin", "User", "0123456789", dummy_roles["admin"]),
        "manager": DummyUser(2, "manager", "manager@example.com", "Manager", "User", "0123456789", dummy_roles["management"]),
        "sales": DummyUser(3, "sales", "sales@example.com", "Sales", "User", "0123456789", dummy_roles["sales"]),
        "support": DummyUser(4, "support", "support@example.com", "Support", "User", "0123456789", dummy_roles["support"])
    }

@pytest.fixture
def dummy_companies():
    return {
        "acme": DummyCompany(1, "ACME"),
        "globex": DummyCompany(2, "Globex")
    }

@pytest.fixture
def dummy_customers(dummy_companies, dummy_users):
    return {
        "john": DummyCustomer(1, "John", "Doe", "john@example.com", "0123456789", dummy_companies["acme"], dummy_users["sales"]),
        "jane": DummyCustomer(2, "Jane", "Smith", "jane@example.com", "0123456789", dummy_companies["globex"], dummy_users["sales"])
    }

@pytest.fixture
def dummy_contracts(dummy_customers, dummy_users):
    return {
        "contract1": DummyContract(1, dummy_customers["john"], True, 1000.0, 500.0, dummy_users["manager"]),
        "contract2": DummyContract(2, dummy_customers["jane"], False, 2000.0, 2000.0, dummy_users["manager"])
    }

@pytest.fixture
def dummy_events(dummy_contracts, dummy_users):
    future_date = datetime.datetime.now() + datetime.timedelta(days=30)
    return {
        "event1": DummyEvent(1, dummy_contracts["contract1"], "Conference", "Paris", future_date, 100, "Notes", dummy_users["support"]),
        "event2": DummyEvent(2, dummy_contracts["contract2"], "Workshop", "Lyon", future_date + datetime.timedelta(days=15), 50, "Notes", dummy_users["support"])
    }

# Helper pour créer un mock de Peewee QuerySet
def create_query_mock(items):
    query_mock = MagicMock()
    query_mock.exists.return_value = bool(items)
    query_mock.__iter__.return_value = iter(items)
    query_mock.__len__.return_value = len(items)
    query_mock.limit.return_value = query_mock
    query_mock.offset.return_value = query_mock
    return query_mock

# Tests des commandes auth
@patch("epicevents.cli.users.authenticate_user")
def test_cli_login(mock_authenticate, runner, dummy_roles):
    """Test de la commande login"""
    from epicevents.cli.users import app as users_app
    
    # Configurer le mock
    mock_authenticate.return_value = {
        "token": "fake_token",
        "user_id": 1,
        "role": dummy_roles["admin"].name
    }
    
    # Exécuter la commande
    result = runner.invoke(users_app, ["login", "-u", "admin", "-p", "password"])
    
    # Vérifications
    assert result.exit_code == 0
    mock_authenticate.assert_called_once_with("admin", "password")

@patch("epicevents.cli.users.remove_token")
@patch("epicevents.cli.users.User.get_by_id", return_value=MagicMock(username="admin"))
@patch("epicevents.cli.users.verify_token", return_value={"user_id": 1})
def test_cli_logout(mock_verify_token, mock_get_by_id, mock_remove_token, runner):
    """Test de la commande logout quand un utilisateur est authentifié."""
    from epicevents.cli.users import app as users_app
    
    # Exécuter la commande logout
    result = runner.invoke(users_app, ["logout"])
    
    # Vérifications
    assert result.exit_code == 0
    # remove_token doit être appelée puisque verify_token retourne un payload valide
    mock_remove_token.assert_called_once()

# Tests des commandes utilisateurs
@patch('epicevents.cli.users.Role')
@patch('epicevents.cli.users.User')
def test_cli_create_user(mock_user, mock_role, runner, dummy_roles, dummy_users):
    """Test de création d'un utilisateur"""
    from epicevents.cli.users import app as users_app

    # Configurer le mock du Role : quand Role.get_by_id est appelé, renvoyer le dummy role admin
    mock_role.get_by_id.return_value = dummy_roles["admin"]

    # Lorsque User() est appelé, renvoyer une instance factice dont on peut vérifier la méthode save()
    fake_user_instance = MagicMock()
    mock_user.return_value = fake_user_instance

    # Simuler que la sauvegarde réussit
    fake_user_instance.save.return_value = None

    # Configurer le mock pour la vérification de l'existence de l'utilisateur
    mock_user.select().where().exists.return_value = False

    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["manager"]):
            # Exécuter la commande
            result = runner.invoke(users_app, [
                "create",
                "-u", "newadmin",
                "-p", "password",
                "-e", "admin@test.com",
                "-fn", "New",
                "-ln", "Admin",
                "-ph", "0123456789",
                "-r", 1
            ])

    # Vérifications
    assert result.exit_code == 0
    fake_user_instance.save.assert_called_once()

@patch('epicevents.cli.users.User')
@patch('epicevents.cli.users.display_list')
def test_cli_list_users(mock_display, mock_user, runner, dummy_users):
    """Test de liste des utilisateurs"""
    from epicevents.cli.users import app as users_app
    
    # Créer un mock de QuerySet
    user_list = list(dummy_users.values())
    query_mock = create_query_mock(user_list)
    mock_user.select.return_value = query_mock
    
    # Définir un side_effect pour display_list
    def fake_display_list(*args, **kwargs):
        print("Liste des utilisateurs")
        for user in user_list:
            print(f"{user.id}: {user.username}")
        print("Appuyez sur 'Backspace' pour continuer, 'Echap' pour quitter.")
    
    mock_display.side_effect = fake_display_list
    
    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["support"]):
            # Exécuter la commande
            result = runner.invoke(users_app, ["list"])
    
    # Vérifications
    assert result.exit_code == 0
    assert "Liste des utilisateurs" in result.output
    mock_display.assert_called_once()

@patch('epicevents.cli.users.User')
def test_cli_read_user(mock_user, runner, dummy_users):
    """Test de lecture d'un utilisateur"""
    from epicevents.cli.users import app as users_app

    # Configurer le mock pour User.get_by_id
    mock_user.get_by_id.return_value = dummy_users["manager"]

    # Exécuter la commande
    result = runner.invoke(users_app, ["read", "1"])

    # Vérifications
    assert result.exit_code == 0, f"Command failed with output: {result.output}"
    mock_user.get_by_id.assert_called_once_with(1)

@patch('epicevents.cli.users.User')
def test_cli_read_user_not_found(mock_user, runner):
    """Test de lecture d'un utilisateur inexistant"""
    from epicevents.cli.users import app as users_app

    # Configurer le mock pour User.get_by_id pour lever une exception DoesNotExist
    mock_user.get_by_id.side_effect = DoesNotExist

    # Exécuter la commande
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=MagicMock()):
            result = runner.invoke(users_app, ["read", "999"])

    # Vérification
    assert "l'utilisateur id 999 n'existe pas" in result.output.lower()

@patch('epicevents.cli.users.User')
def test_cli_update_user(mock_user, runner, dummy_users):
    """Test de mise à jour d'un utilisateur"""
    from epicevents.cli.users import app as users_app
    
    # Configurer le mock
    user = dummy_users["admin"]
    mock_user.get_or_none.return_value = user
    
    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["sales"]):
            # Exécuter la commande
            result = runner.invoke(users_app, ["update", "1", "-e", "new@example.com"])
    
    # Vérifications
    assert result.exit_code == 0
    assert "mis à jour" in result.output.lower()

@patch('epicevents.cli.users.User')
@patch('epicevents.cli.users.typer')
def test_cli_delete_user_confirm(mock_typer, mock_user, runner, dummy_users):
    """Test de suppression d'un utilisateur avec confirmation"""
    from epicevents.cli.users import app as users_app

    # Configurer les mocks
    mock_user.get_or_none.return_value = dummy_users["admin"]
    mock_typer.confirm.return_value = True  # Simulate user confirming the deletion

    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["admin"]):
            # Exécuter la commande
            result = runner.invoke(users_app, ["delete", "1"])

    # Vérification
    assert "êtes-vous sûr de vouloir supprimer" in result.output.lower()

# Tests des commandes clients
@patch('epicevents.cli.customers.Customer')
@patch('epicevents.cli.customers.Company')
@patch('epicevents.cli.customers.User')
def test_cli_create_customer(mock_user, mock_company, mock_customer, runner, dummy_users, dummy_companies, dummy_customers):
    """Test de création d'un client"""
    from epicevents.cli.customers import app as customers_app

    # Configurer les mocks
    mock_company.get_or_create.return_value = (dummy_companies["acme"], False)
    mock_user.get_or_none.return_value = dummy_users["sales"]

    # Lorsque Customer() est appelé, renvoyer une instance factice dont on peut vérifier la méthode save()
    fake_customer_instance = MagicMock()
    mock_customer.return_value = fake_customer_instance

    # Simuler que la sauvegarde réussit
    fake_customer_instance.save.return_value = None

    # Configurer le mock pour la vérification de l'existence du client
    mock_customer.select().where().exists.return_value = False

    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["sales"]):
            # Exécuter la commande
            result = runner.invoke(customers_app, [
                "create",
                "-fn", "John",
                "-ln", "Doe",
                "-e", "john@example.com",
                "-p", "0123456789",
                "-c", "ACME",
                "-u", "3"
            ])

    # Vérifications
    assert result.exit_code == 0
    fake_customer_instance.save.assert_called_once()

@patch('epicevents.cli.customers.Customer')
@patch('epicevents.cli.customers.display_list')
def test_cli_list_customers(mock_display, mock_customer, runner, dummy_users, dummy_customers):
    """Test de liste des clients"""
    from epicevents.cli.customers import app as customers_app
    
    # Créer un mock de QuerySet
    customer_list = list(dummy_customers.values())
    query_mock = create_query_mock(customer_list)
    mock_customer.select.return_value = query_mock
    
    # Définir un side_effect pour display_list
    def fake_display_list(*args, **kwargs):
        print("Liste des clients")
        for customer in customer_list:
            print(f"{customer.id}: {customer.first_name} {customer.last_name}")
        print("Appuyez sur 'Backspace' pour continuer, 'Echap' pour quitter.")
    
    mock_display.side_effect = fake_display_list
    
    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["support"]):
            # Exécuter la commande
            result = runner.invoke(customers_app, ["list"])
    
    # Vérifications
    assert result.exit_code == 0
    assert "Liste des clients" in result.output
    mock_display.assert_called_once()

@patch('epicevents.cli.customers.Customer')
def test_cli_read_customer(mock_customer, runner, dummy_users, dummy_customers):
    """Test de lecture d'un client"""
    from epicevents.cli.customers import app as customers_app

    # Configurer le mock pour Customer.get_by_id
    mock_customer.get_by_id.return_value = dummy_customers["john"]

    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["support"]):
            # Exécuter la commande
            result = runner.invoke(customers_app, ["read", "1"])

    # Vérifications
    assert result.exit_code == 0, f"Command failed with output: {result.output}"
    mock_customer.get_by_id.assert_called_once_with(1)

@patch('epicevents.cli.customers.Customer')
def test_cli_update_customer(mock_customer, runner, dummy_users, dummy_customers):
    """Test de mise à jour d'un client"""
    from epicevents.cli.customers import app as customers_app
    
    # Configurer le mock
    customer = dummy_customers["john"]
    mock_customer.get_or_none.return_value = customer
    
    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["sales"]):
            # Exécuter la commande
            result = runner.invoke(customers_app, ["update", "1", "-e", "newemail@example.com"])
    
    # Vérifications
    assert result.exit_code == 0
    assert "mis à jour" in result.output.lower()

@patch('epicevents.cli.customers.Customer')
@patch('epicevents.cli.customers.typer')
def test_cli_delete_customer_confirm(mock_typer, mock_customer, runner, dummy_users, dummy_customers):
    """Test de suppression d'un client avec confirmation"""
    from epicevents.cli.customers import app as customers_app
    
    # Configurer les mocks
    mock_customer.get_or_none.return_value = dummy_customers["john"]
    mock_typer.confirm.return_value = True
    
    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["admin"]):
            # Exécuter la commande
            result = runner.invoke(customers_app, ["delete", "1"])
    
    # Vérification
    assert "êtes-vous sûr de vouloir supprimer" in result.output.lower()

# Tests des commandes contrats
@patch('epicevents.cli.contracts.Contract')
@patch('epicevents.cli.contracts.Customer')
@patch('epicevents.cli.contracts.User')
def test_cli_create_contract(mock_user, mock_customer, mock_contract, runner, dummy_users, dummy_customers, dummy_contracts):
    """Test de création d'un contrat"""
    from epicevents.cli.contracts import app as contracts_app

    # Configurer les mocks
    mock_customer.get_or_none.return_value = dummy_customers["john"]
    mock_user.get_or_none.return_value = dummy_users["manager"]

    # Lorsque Contract() est appelé, renvoyer une instance factice dont on peut vérifier la méthode save()
    fake_contract_instance = MagicMock()
    mock_contract.return_value = fake_contract_instance

    # Simuler que la sauvegarde réussit
    fake_contract_instance.save.return_value = None

    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["manager"]):
            # Exécuter la commande
            result = runner.invoke(contracts_app, [
                "create",
                "-c", "1",
                "-st", "1000.0",
                "-sd", "500.0",
                "-si",
                "-u", "2"
            ])

    # Vérifications
    assert result.exit_code == 0
    fake_contract_instance.save.assert_called_once()

@patch('epicevents.cli.contracts.Contract')
@patch('epicevents.cli.contracts.display_list')
def test_cli_list_contracts(mock_display, mock_contract, runner, dummy_users, dummy_contracts):
    """Test de liste des contrats"""
    from epicevents.cli.contracts import app as contracts_app
    
    # Créer un mock de QuerySet
    contract_list = list(dummy_contracts.values())
    query_mock = create_query_mock(contract_list)
    mock_contract.select.return_value = query_mock
    
    # Définir un side_effect pour display_list
    def fake_display_list(*args, **kwargs):
        print("Liste des contrats")
        for contract in contract_list:
            print(f"{contract.id}: {contract.amount_total}€")
        print("Appuyez sur 'Backspace' pour continuer, 'Echap' pour quitter.")
    
    mock_display.side_effect = fake_display_list
    
    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["support"]):
            # Exécuter la commande
            result = runner.invoke(contracts_app, ["list"])
    
    # Vérifications
    assert result.exit_code == 0
    assert "Liste des contrats" in result.output
    mock_display.assert_called_once()

@patch('epicevents.cli.contracts.Contract')
@patch('epicevents.cli.contracts.User.get_or_none')  # Patcher les requêtes User.get_or_none
def test_cli_read_contract(mock_get_user, mock_contract, runner, dummy_contracts, dummy_users, dummy_customers):
    """Test de la commande read contract pour un contrat existant."""
    from epicevents.cli.contracts import app as contracts_app

    # 🔹 Assurer que les IDs sont bien des entiers
    dummy_contract = dummy_contracts["contract1"]
    dummy_contract.id = 1
    dummy_contract.signed = True
    dummy_contract.amount_total = 5000.0
    dummy_contract.amount_due = 2000.0

    dummy_contract.team_contact_id = dummy_users["sales"].id  # Doit être un entier !
    dummy_contract.customer = dummy_customers["john"]
    dummy_contract.customer.team_contact_id = dummy_users["support"].id  # Doit être un entier !

    # 🔹 Configurer les mocks
    mock_contract.get_by_id.return_value = dummy_contract

    # Simuler User.get_or_none() pour retourner le bon utilisateur quand on lui donne un ID
    def mock_get_user_by_id(query):
        if query == dummy_users["sales"].id:
            return dummy_users["sales"]
        if query == dummy_users["support"].id:
            return dummy_users["support"]
        return None

    mock_get_user.side_effect = mock_get_user_by_id

    # 🔹 Exécuter la commande CLI
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["support"]):
            result = runner.invoke(contracts_app, ["read", "1"])

    # 🔹 Afficher le résultat du test pour débogage
    print(f"CLI Output:\n{result.output}")

    # 🔹 Vérifications
    assert result.exit_code == 0
    assert f"Contrat {dummy_contract.id}" in result.output
    assert dummy_contract.customer.first_name in result.output
    assert "Montant" in result.output

@patch('epicevents.cli.contracts.Contract')
def test_cli_update_contract(mock_contract, runner, dummy_users, dummy_contracts):
    """Test de mise à jour d'un contrat"""
    from epicevents.cli.contracts import app as contracts_app
    
    # Configurer le mock
    contract = dummy_contracts["contract1"]
    mock_contract.get_or_none.return_value = contract
    
    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["manager"]):
            # Exécuter la commande
            result = runner.invoke(contracts_app, ["update", "1", "-sd", "200.0"])
    
    # Vérifications
    assert result.exit_code == 0
    assert "mis à jour" in result.output.lower()

@patch('epicevents.cli.contracts.Contract')
@patch('epicevents.cli.contracts.typer')
def test_cli_delete_contract_confirm(mock_typer, mock_contract, runner, dummy_users, dummy_contracts):
    """Test de suppression d'un contrat avec confirmation"""
    from epicevents.cli.contracts import app as contracts_app
    
    # Configurer les mocks
    mock_contract.get_or_none.return_value = dummy_contracts["contract1"]
    mock_typer.confirm.return_value = True
    
    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["admin"]):
            # Exécuter la commande
            result = runner.invoke(contracts_app, ["delete", "1"])
    
    # Vérification
    assert "êtes-vous sûr de vouloir supprimer" in result.output.lower()

# Tests des commandes événements
@patch('epicevents.cli.events.Event')
@patch('epicevents.cli.events.Contract')
@patch('epicevents.cli.events.User')
def test_cli_create_event(mock_user, mock_contract, mock_event, runner, dummy_users, dummy_contracts, dummy_events):
    """Test de création d'un événement"""
    from epicevents.cli.events import app as events_app

    # Date future pour éviter l'erreur de validation
    future_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")

    # Configurer les mocks
    mock_contract.get_or_none.return_value = dummy_contracts["contract1"]
    mock_user.get_or_none.return_value = dummy_users["support"]

    # Lorsque Event() est appelé, renvoyer une instance factice dont on peut vérifier la méthode save()
    fake_event_instance = MagicMock()
    mock_event.return_value = fake_event_instance

    # Simuler que la sauvegarde réussit
    fake_event_instance.save.return_value = None

    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["manager"]):
            # Exécuter la commande
            result = runner.invoke(events_app, [
                "create",
                "-ct", "1",
                "-t", "Conference",
                "-d", future_date,
                "-l", "Paris",
                "-a", "100",
                "-n", "Notes",
                "-u", "4"
            ])

    # Vérifications
    assert result.exit_code == 0
    fake_event_instance.save.assert_called_once()

@patch('epicevents.cli.events.Event')
@patch('epicevents.cli.events.display_list')
def test_cli_list_events(mock_display, mock_event, runner, dummy_users, dummy_events):
    """Test de liste des événements"""
    from epicevents.cli.events import app as events_app
    
    # Créer un mock de QuerySet
    event_list = list(dummy_events.values())
    query_mock = create_query_mock(event_list)
    mock_event.select.return_value = query_mock
    
    # Définir un side_effect pour display_list
    def fake_display_list(*args, **kwargs):
        print("Liste des événements")
        for event in event_list:
            print(f"{event.id}: {event.name}")
        print("Appuyez sur 'Backspace' pour continuer, 'Echap' pour quitter.")
    
    mock_display.side_effect = fake_display_list
    
    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["sales"]):
            # Exécuter la commande
            result = runner.invoke(events_app, ["list"])
    
    # Vérifications
    assert result.exit_code == 0
    assert "Liste des événements" in result.output
    mock_display.assert_called_once()

@patch('epicevents.cli.events.Event')
def test_cli_read_event(mock_event, runner, dummy_users, dummy_events):
    """Test de lecture d'un événement"""
    from epicevents.cli.events import app as events_app
        
    # Configurer le mock
    mock_event.get_by_id.return_value = dummy_events["event1"]
    
    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["support"]):
            # Exécuter la commande
            result = runner.invoke(events_app, ["read", "1"])
    
    # Vérifications
    assert result.exit_code == 0
    mock_event.get_by_id.assert_called_once()

@patch('epicevents.cli.events.Event')
def test_cli_update_event(mock_event, runner, dummy_users, dummy_events):
    """Test de mise à jour d'un événement"""
    from epicevents.cli.events import app as events_app
    
    # Date future pour éviter l'erreur de validation
    future_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Configurer le mock
    event = dummy_events["event1"]
    mock_event.get_or_none.return_value = event
    
    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["admin"]):
            # Exécuter la commande
            result = runner.invoke(events_app, ["update", "1", "-t", "New Conference", "-d", future_date])
    
    # Vérifications
    assert result.exit_code == 0
    assert "mis à jour" in result.output.lower()

@patch('epicevents.cli.events.Event')
@patch('epicevents.cli.events.typer')
def test_cli_delete_event_confirm(mock_typer, mock_event, runner, dummy_users, dummy_events):
    """Test de suppression d'un événement avec confirmation"""
    from epicevents.cli.events import app as events_app
    
    # Configurer les mocks
    mock_event.get_or_none.return_value = dummy_events["event1"]
    mock_typer.confirm.return_value = True
    
    # Patcher check_auth pour simuler un utilisateur authentifié
    with patch('epicevents.permissions.auth.check_auth', return_value=True):
        with patch('epicevents.permissions.auth.is_logged', return_value=dummy_users["admin"]):
            # Exécuter la commande
            result = runner.invoke(events_app, ["delete", "1"])
    
    # Vérification
    assert "êtes-vous sûr de vouloir supprimer" in result.output.lower()
