import typer
import os
from datetime import datetime
from rich.console import Console
from rich.prompt import Confirm
from peewee import DoesNotExist
from epicevents.models.customer import Customer
from epicevents.models.company import Company
from epicevents.models.user import User
from epicevents.cli.auth import is_logged
from epicevents.cli.utils import display_list
from epicevents.cli.utils import format_text


app = typer.Typer(help="Gestion des clients")
console = Console()

def create_company(company_name: str) -> int:
    """Checks if company already exists."""
    company, created = Company.get_or_create(name=company_name)
    return company.id

@app.command("create")
def create_customer(
    ctx: typer.Context,
    first_name: str = typer.Option(..., "-fn", help="Prénom du client"),
    last_name: str = typer.Option(..., "-ln", help="Nom du client"),
    email: str = typer.Option(..., "-e", help="Adresse mail du client"),
    phone: str = typer.Option(..., "-p", help="Numéro de téléphone"),
    company: str = typer.Option(..., "-c", help="Nom d'entreprise du client"),
    contact_id: int = typer.Option(0, "-u", help="Numéro du commercial en charge"),
):
    """Creates a new customer."""

    user = ctx.obj

    # If "sales" & no contact_id given, auto-assign to user.id
    if user.role.name == "sales" and contact_id == 0:
        contact_id = user.id

    # Checks if customer already exists
    if Customer.select().where(Customer.email == email).exists():
        console.print(
            format_text('bold', 'red', "❌ Erreur : Client déjà enregistré.")
        )
        raise typer.Exit()

    # Validate company
    if not company:
        console.print(
            format_text('bold', 'red', "❌ Erreur : Vous devez fournir l'entreprise du client.")
        )
        raise typer.Exit()

    try:
        company_id = create_company(company)
    except ValueError as e:
        console.print(format_text('bold', 'red', f"❌ {str(e)}"))
        raise typer.Exit(1)

    customer = Customer(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        company_id=company_id,
        assigned_user_id=contact_id
    )

    try:
        customer.save()
        console.print(
            format_text('bold', 'green', f"✅ Client {customer.id} : {customer.first_name} {customer.last_name.upper()} créé avec succès.")
        )
    except ValueError as e:
        console.print(format_text('bold', 'red', f"❌ {str(e)}"))
        raise typer.Exit(1)

@app.command("read")
def read_customer(customer_id: int = typer.Argument(None, help="ID du client à afficher")):
    """Shows customer details given customer uid."""
    try:
        customer = Customer.get_by_id(customer_id)
        customer_data = [
            {"Champ": "ID", "Valeur": customer.id},
            {"Champ": "Email", "Valeur": customer.email},
            {"Champ": "Téléphone", "Valeur": customer.phone},
            {"Champ": "Entreprise", "Valeur": customer.company.name},
            {"Champ": "Epic Contact", "Valeur": f"{customer.team_contact_id.first_name} {customer.team_contact_id.last_name.upper()} ({customer.team_contact_id.id})" if isinstance(customer.team_contact_id, User) else f"ID: {customer.team_contact_id}" if customer.team_contact_id else "Aucun"},
        ]
        display_list(f"Client {customer.first_name} {customer.last_name.upper()}", customer_data)
    except DoesNotExist:
        console.print(format_text('bold', 'red', f"❌ Client ID {customer_id} introuvable."))
        raise typer.Exit()

@app.command("list")
def list_customers(
    ctx: typer.Context,
    filter_on: bool = typer.Option(False, "--fi", help="Filtre automatiquement les clients selon votre rôle")
):
    """Lists all customers."""
    customers = Customer.select().join(Company, on=(Customer.company_id == Company.id))
    nobody_message = "❌ Aucun client n'est enregistré dans la bdd."

    if filter_on:
        user = ctx.obj
        if user.role.name == "sales":
            customers = customers.where(Customer.team_contact_id == user.id)
            nobody_message = "❌ Aucun client ne vous est attribué."
        elif user.role.name in ["admin", "management"]:
            customers = customers.where(Customer.team_contact_id.is_null(True))
            nobody_message = "❌ Aucun client sans agent n'est enregistré dans la bdd."
        else:  # support
            customers = customers.where(Customer.team_contact_id.is_null(False)) 
            nobody_message = "❌ Aucun client avec agent n'est enregistré dans la bdd."         

    if not customers.exists():
        console.print(format_text('bold', 'red', f"{nobody_message}"))
        return

    customers_list = []
    for customer in customers:
        contact_info = "Aucun"
        context_color = "red"

        if isinstance(customer.team_contact_id, User):
            contact_info = f"{customer.team_contact_id.first_name} {customer.team_contact_id.last_name.upper()} ({customer.team_contact_id.id})"
            context_color = "white"
        elif customer.team_contact_id:
             contact_info = f"ID: {customer.team_contact_id}"
             context_color = "orange"

        customers_list.append(
            {
                "ID": customer.id,
                "FIRST NAME": customer.first_name,
                "LAST NAME": customer.last_name.upper(),
                "EMAIL": customer.email,
                "COMPANY": customer.company.name,
                "EPIC CONTACT": contact_info,
                "Contexte": context_color,
            }
        )

    customers_list = sorted(customers_list, key=lambda x: x["ID"], reverse=False)
    display_list("Liste des utilisateurs", customers_list, use_context=True)

@app.command("update")
def update_customer(
    customer_id: int = typer.Argument(..., help="ID du client à modifier"),
    first_name: str = typer.Option(None, "-fn", help="Nouveau prénom"),
    last_name: str = typer.Option(None, "-ln", help="Nouveau nom"),
    email: str = typer.Option(None, "-e", help="Nouvel email"),
    phone: str = typer.Option(None, "-p", help="Nouveau téléphone"),
    company: str = typer.Option(None, "-c", help="Nouvelle entreprise"),
    user_id: int = typer.Option(None, "-u", help="Nouveau commercial en charge"),
):
    """Updates an existing customer."""

    try:
        customer = Customer.get_by_id(customer_id)
    except DoesNotExist:
        console.print(format_text('bold', 'red', f"❌ Client ID {customer_id} introuvable."))
        raise typer.Exit()

    updates = {}
    if first_name:
        updates["first_name"] = first_name
    if last_name:
        updates["last_name"] = last_name
    if email:
        updates["email"] = email
    if phone:
        updates["phone"] = phone
    if company:
        updates["company_id"] = create_company(company)
    if user_id is not None:
        updates["team_contact_id"] = user_id
    
    try:
        if updates:
            for key, value in updates.items():
                setattr(customer, key, value)
            customer.save()
            console.print(format_text('bold', 'green', f"✅ Client {customer_id} : {customer.first_name} {customer.last_name.upper()} mis à jour avec succès !"))
        else:
            console.print(format_text('bold', 'yellow', "⚠ Aucun champ à mettre à jour."))
            raise typer.Exit()
    except ValueError as e:
        console.print(format_text('bold', 'red', f"❌ {str(e)}"))
        raise typer.Exit(1)

@app.command("delete")
def delete_customer(
    customer_id: int = typer.Argument(..., help="ID du client à supprimer")
):
    """Deletes an existing customer."""
    try:
        customer = Customer.get_by_id(customer_id)
    except DoesNotExist:
        console.print(format_text('bold', 'red', f"❌ Client ID {customer_id} introuvable."))
        raise typer.Exit()

    confirm = Confirm.ask(
        format_text('bold', 'yellow', f"⚠ Êtes-vous sûr de vouloir supprimer {customer.first_name} {customer.last_name.upper()} ({customer_id}) ?")
    )

    if confirm:
        customer.delete_instance()
        console.print(format_text('bold', 'green', f"✅ Client {customer.first_name} {customer.last_name.upper()} ({customer_id}) supprimé !"))
    else:
        console.print(
            format_text('bold', 'red', "❌ Opération annulée.")
        )
        raise typer.Exit()
