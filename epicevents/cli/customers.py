import typer
from datetime import datetime
from models.customer import Customer

app = typer.Typer()

@app.command()
def create(
    fn: str = typer.Option(..., "--fn", help="Prénom du client"),
    ln: str = typer.Option(..., "--ln", help="Nom du client"),
    e: str = typer.Option(..., "--e", help="Adresse mail du client"),
    p: str = typer.Option(..., "--p", help="Numéro de téléphone"),
    c: int = typer.Option(..., "--c", help="Numéro d'entreprise du client"),
    u: int = typer.Option(0, "--u", help="Numéro du commercial en charge"),
):
    """Créer un nouveau client"""
    customer = Customer.create(
        first_name=fn,
        last_name=ln,
        email=e,
        phone=p,
        company_id=c,
        created_date=datetime.now(),
        updated_date=datetime.now(),
        assigned_user_id=u,
    )
    typer.echo(f"Client {customer.id} créé avec succès.")

@app.command()
def list():
    """Lister tous les clients"""
    customers = Customer.select()
    if not customers.count():
        typer.echo("❌ Aucun client n'est enregistré dans la bdd.")
        return

    for customer in customers:
        typer.echo(f"{customer.id}: {customer.first_name} {customer.last_name} - {customer.email}")

@app.command()
def update(
    customer_id: int,
    field: str = typer.Argument(..., help="Champ à modifier"),
    new_value: str = typer.Argument(..., help="Nouvelle valeur"),
):
    """Mettre à jour un client"""
    allowed_fields = {"fn": "first_name", "ln": "last_name", "e": "email", "p": "phone", "c": "company_id"}
    
    if field not in allowed_fields:
        typer.echo("Champ non modifiable.")
        raise typer.Exit()
    
    query = Customer.update({allowed_fields[field]: new_value, "updated_date": datetime.now()}).where(Customer.id == customer_id)
    query.execute()
    typer.echo(f"Client {customer_id} mis à jour avec succès.")
