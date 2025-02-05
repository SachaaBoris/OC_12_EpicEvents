import typer
import os
from dotenv import load_dotenv, set_key, get_key
from models.user import User


app = typer.Typer(help="Gestion des utilisateurs")

@app.command("create")
def create_user(
    fn: str = typer.Option(..., "--fn", help="Prénom du commercial"),
    un: str = typer.Option(..., "--un", help="Nom du commercial"),
    pw: str = typer.Option(..., "--pw", help="Mot de passe du commercial"),
    e: str = typer.Option(..., "--e", help="Adresse mail du commercial"),
    r: int = typer.Option(..., "--r", help="Numéro de rôle (1: Admin, 2: Sales, 3: Support)")
):
    """Creates a new user."""
    typer.echo(f"Utilisateur créé: {fn} {un}, Rôle: {r}")

@app.command("list")
def list_users():
    """Lists all users."""
    users = User.select()

    if users.count() == 0:
        typer.echo("❌ Aucun utilisateur trouvé.")
        return

    typer.echo("Liste des utilisateurs :\n")
    typer.echo("ID  USERNAME            (EMAIL)             ROLE")
    for user in users:
        typer.echo(f"-{user.id} {user.username} ({user.email}) - Rôle: {user.role.name}")

@app.command("update")
def update_user(
    uid: int = typer.Argument(..., help="Id de l'user à modifier"),
    new_value: str = typer.Argument(..., help="Nouvelle valeur à appliquer"),
    fn: bool = typer.Option(False, "-fn", help="Modifier le prénom"),
    ln: bool = typer.Option(False, "-ln", help="Modifier le nom"),
    e: bool = typer.Option(False, "-e", help="Modifier l'email"),
    p: bool = typer.Option(False, "-p", help="Modifier le mot de passe"),
    d: bool = typer.Option(False, "-d", help="Modifier le département")
):
    """Updates an existing user"""
    typer.echo(f"Modification de l'utilisateur {uid}: {new_value}")

@app.command("delete")
def delete_user(uid: int = typer.Option(..., "--uid", help="Id de l'user à supprimer")):
    """Deletes an existing user."""
    typer.echo(f"Utilisateur {uid} supprimé.")
