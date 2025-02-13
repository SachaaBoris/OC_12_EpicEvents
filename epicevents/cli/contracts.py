import typer
import os
from datetime import datetime
from rich.console import Console
from rich.prompt import Confirm
from peewee import DoesNotExist
from peewee import IntegrityError
from models.contract import Contract
from models.customer import Customer
from models.company import Company
from models.user import User
from cli.utils import display_list, format_text
from dotenv import get_key


app = typer.Typer(help="Gestion des contrats")
CURRENCY = get_key(".env", "CURRENCY")
console = Console()

@app.command("create")
def create_contract(
    customer_id: int = typer.Option(..., "-c", help="ID du client"),
    sum_total: float = typer.Option(..., "-st", help="Montant total"),
    sum_due: float = typer.Option(None, "-sd", help="Montant restant dû"),
    signed: bool = typer.Option(False, "-si", help="Statut de la signature (True: Signé, False: Non signé)"),
    contact_id: int = typer.Option(0, "-u", help="ID du commercial en charge"),
):
    """Creates a new contract."""

    try:
        customer = Customer.get_by_id(customer_id)
    except DoesNotExist:
        console.print(format_text('bold', 'red', f"❌ Erreur : Le client ID {customer_id} n'existe pas."))
        raise typer.Exit()

    if contact_id:
        try:
            user = User.get_by_id(contact_id)
        except DoesNotExist:
            console.print(format_text('bold', 'red', f"❌ Erreur : L'utilisateur ID {contact_id} n'existe pas."))
            raise typer.Exit()
    else:
        user = None

    contract = Contract(
        customer=customer,
        amount_total=sum_total,
        amount_due=sum_due if sum_due is not None else sum_total,
        signed=signed,
        team_contact=user,
    )
    
    try:
        contract.save()
        console.print(format_text('bold', 'green', f"✅ Contrat {contract.id} créé pour {customer.first_name} {customer.last_name}."))
    except (ValueError, IntegrityError) as e:
        console.print(format_text('bold', 'red', f"❌ {str(e)}"))
        raise typer.Exit(1)

@app.command("read")
def read_contract(
    contract_id: int = typer.Argument(None, help="ID du contrat à afficher")
):
    """Shows contract details given contract uid."""

    if contract_id is not None:
        try:
            contract = Contract.get_by_id(contract_id)
            contract_data = [
                {"Champ": "ID", "Valeur": contract.id},
                {"Champ": "Client", "Valeur": f"{contract.customer.first_name} {contract.customer.last_name.upper()}"},
                {"Champ": "Montant total", "Valeur": f"{contract.amount_total:.2f} {CURRENCY}"},
                {"Champ": "Montant dû", "Valeur": f"{contract.amount_due:.2f} {CURRENCY}"},
                {"Champ": "Signé", "Valeur": "✅ Oui" if contract.signed else "❌ Non"},
                {"Champ": "Epic Contact", "Valeur": f"{contract.team_contact.first_name} {contract.team_contact.last_name.upper()} ({contract.team_contact.user_id})" if contract.team_contact else "Aucun"},
            ]
            display_list(f"Contrat {contract.id}", contract_data)

        except DoesNotExist:
            console.print(format_text('bold', 'red', f"❌ Erreur : Le contrat ID {contract_id} n'existe pas."))
            raise typer.Exit()
    else:
        console.print(format_text('bold', 'red', "❌ Erreur : Vous n'avez pas fourni d'ID de contrat."))


@app.command("list")
def list_contracts(
    unsigned: bool = typer.Option(False, "-ns", help="Filtrer les contrats non signés"),
    unpaid: bool = typer.Option(False, "-up", help="Filtrer les contrats non payés"),
):
    """List contracts with filtering options."""
    query = Contract.select()
    if unsigned:
        query = query.where(Contract.signed == False)
    if unpaid:
        query = query.where(Contract.amount_due > 0)
    contracts = list(query)
    if not contracts:
        console.print(
            format_text('bold', 'red', "❌ Aucun contrat trouvé.")
        )
        return
    contracts_list = []
    for contract in contracts:
        if not contract.signed:
            context = "orange"
        elif contract.amount_due > 0:
            context = "yellow"
        else:
            context = "blue"
        contracts_list.append(
            {
                "ID": contract.id,
                "CLIENT": f"{contract.customer.first_name} {contract.customer.last_name.upper()} ({contract.customer.id})",
                "MONTANT TOTAL": f"{contract.amount_total:.2f} {CURRENCY}",
                "MONTANT DÛ": f"{contract.amount_due:.2f} {CURRENCY}",
                "EPIC CONTACT": f"{contract.team_contact_id.first_name} {contract.team_contact_id.last_name.upper()} ({contract.team_contact_id.id})" if contract.team_contact_id else "Aucun",
                "Contexte": context,
            }
        )
    display_list("Liste des contrats", contracts_list, use_context=True)

@app.command("update")
def update_contract(
    contract_id: int = typer.Argument(..., help="ID du contrat à modifier"),
    customer_id: int = typer.Option(None, "-c", help="Modifier l'ID du client"),
    user_id: int = typer.Option(None, "-u", help="Modifier l'ID du commercial"),
    sum_total: float = typer.Option(None, "-st", help="Modifier le montant total"),
    sum_due: float = typer.Option(None, "-sd", help="Modifier le montant dû"),
    signed: bool = typer.Option(None, "-s", help="Modifier le statut de la signature"),
):
    """Updates existing contract."""

    try:
        contract = Contract.get_by_id(contract_id)
    except DoesNotExist:
        console.print(format_text('bold', 'red', f"❌ Erreur : Le contrat ID {contract_id} n'existe pas."))
        raise typer.Exit()

    updates = {}

    if customer_id:
        try:
            updates["customer"] = Customer.get_by_id(customer_id)
        except DoesNotExist:
            console.print(format_text('bold', 'red', f"❌ Erreur : Le client ID {customer_id} n'existe pas."))
            raise typer.Exit()

    if user_id:
        try:
            updates["team_contact_id"] = User.get_by_id(user_id)
        except DoesNotExist:
            console.print(format_text('bold', 'red', f"❌ Erreur : L'utilisateur ID {user_id} n'existe pas."))
            raise typer.Exit()

    if sum_total is not None:
        updates["amount_total"] = sum_total

    if sum_due is not None:
        updates["amount_due"] = sum_due

    if signed is not None:
        updates["signed"] = signed

    try:
        if updates:
            for key, value in updates.items():
                setattr(contract, key, value)
            contract.save()
            console.print(format_text('bold', 'green', f"✅ Contrat {contract_id} mis à jour avec succès !"))
        else:
            console.print(format_text('bold', 'yellow', "⚠ Aucun champ à mettre à jour."))
            raise typer.Exit()
    except (ValueError, IntegrityError) as e:
        console.print(format_text('bold', 'red', f"❌ {str(e)}"))
        raise typer.Exit(1)

@app.command("delete")
def delete_contract(
    contract_id: int = typer.Argument(..., help="ID du contrat à supprimer")
):
    """Deletes existing contract."""

    try:
        contract = Contract.get_by_id(contract_id)
    except DoesNotExist:
        console.print(format_text('bold', 'red', f"❌ Erreur : Le contrat ID {contract_id} n'existe pas."))
        raise typer.Exit()

    confirm = Confirm.ask(format_text('bold', 'yellow', f"⚠ Êtes-vous sûr de vouloir supprimer le contrat {contract_id} ?"))

    if confirm:
        contract.delete_instance()
        console.print(format_text('bold', 'green', f"✅ Contrat {contract_id} supprimé avec succès !"))
    else:
        console.print(format_text('bold', 'red', "❌ Opération annulée."))
        raise typer.Exit()
