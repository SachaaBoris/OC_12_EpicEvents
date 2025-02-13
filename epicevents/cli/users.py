import typer
import os
from datetime import datetime
from rich.console import Console
from rich.prompt import Confirm
from peewee import DoesNotExist
from dotenv import load_dotenv, set_key, get_key
from models.user import User
from cli.utils import authenticate_user
from cli.utils import generate_token, verify_token, remove_token
from cli.utils import display_list, format_text


app = typer.Typer(help="Gestion des utilisateurs")
console = Console()

# AUTH operations
@app.command("login")
def login(
    username: str = typer.Option(..., "-u", help="Nom d'utilisateur"),
    password: str = typer.Option(..., "-p", help="Mot de passe")
):
    """Authenticates user through CLI"""
    try:
        result = authenticate_user(username, password)
        console.print(
            format_text('bold', 'green', f"✅ Connecté en tant que {username} (rôle: {result['role']})")
        )
    except AuthenticationError as e:
        console.print(
            format_text('bold', 'red', f"❌ Erreur d'authentification : {str(e)}")
        )
        raise typer.Exit(1)

@app.command("logout")
def logout():
    """Logs out current user through CLI"""
    payload = verify_token()
    if payload:
        user_id = payload.get("user_id")
        user = User.get_by_id(user_id)
        remove_token()
        console.print(
            format_text('bold', 'green', f"✅ {user.username} déconnecté(e).")
        )
    else:
        console.print(
            format_text('bold', 'red', "❌ Vous n'étiez pas connecté.")
        )

# CRUD operations
@app.command("create")
def create_user(
    username: str = typer.Option(..., "-u", help="Nom d'utilisateur"),
    password: str = typer.Option(..., "-p", help="Mot de passe"),
    email: str = typer.Option(..., "-e", help="Email"),
    first_name: str = typer.Option(..., "-fn", help="Prénom"),
    last_name: str = typer.Option(..., "-ln", help="Nom"),
    phone: str = typer.Option(..., "-ph", help="Téléphone"),
    role_id: int = typer.Option(..., "-r", help="Numéro de rôle (1: Admin, 2: Sales, 3: Support)")
):
    """Creates a new user."""

    # Check if user already exists
    if User.select().where((User.username == username) | (User.email == email)).exists():
        console.print(
            format_text('bold', 'red', "❌ Erreur : email déjà utilisé.")
        )
        raise typer.Exit()

    # Validate rôle
    try:
        role = Role.get_by_id(role_id)
    except DoesNotExist:
        console.print(
            format_text('bold', 'red', "❌ Erreur : Rôle invalide.")
        )
        raise typer.Exit()

    user = User(
        username=username,
        password=ph.hash(password),
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        role=role,
    )

    user.save()
    console.print(
        format_text('bold', 'green', f"✅ Utilisateur {user.username} créé avec succès !")
    )

@app.command("read")
def read_user(ctx: typer.Context, uid: int = typer.Argument(None, help="ID de l'utilisateur à afficher")):
    """Shows user details given user uid."""
    if uid is not None:
        ctx.obj = {"target_id": uid}
        try:
            user = User.get_by_id(uid)
            user_data = [
                {"Champ": "ID", "Valeur": user.id},
                {"Champ": "Nom d'utilisateur", "Valeur": user.username},
                {"Champ": "Email", "Valeur": user.email},
                {"Champ": "Prénom", "Valeur": user.first_name.capitalize()},
                {"Champ": "Nom", "Valeur": user.last_name.upper()},
                {"Champ": "Téléphone", "Valeur": user.phone},
                {"Champ": "Rôle", "Valeur": user.role.name if user.role else "Aucun"},
            ]
            display_list(f"Utilisateur {user.username}", user_data)

        except DoesNotExist:
            console.print(
                format_text('bold', 'red', f"❌ Erreur : L'utilisateur ID {uid} n'existe pas.")
            )
            raise typer.Exit()
    else:
        console.print(
            format_text('bold', 'red', f"❌ Erreur : Vous n'avez pas fourni d'ID utilisateur.")
        )

@app.command("list")
def list_users(ctx: typer.Context):
    """Lists all users."""
    users = User.select()

    if not users.exists():
        console.print(
            format_text('bold', 'red', f"❌ Aucun utilisateur trouvé.")
        )
        return

    user_list = [
        {
            "ID": user.id,
            "USERNAME": user.username,
            "EMAIL": user.email,
            "ROLE": user.role.name,
        }
        for user in users
    ]

    display_list("Liste des utilisateurs", user_list)

@app.command("update")
def update_user(
    ctx: typer.Context,
    uid: int = typer.Argument(..., help="ID de l'utilisateur à modifier"),
    username: str = typer.Option(None, "-u", help="Nouveau nom d'utilisateur"),
    email: str = typer.Option(None, "-e", help="Nouvel email"),
    password: str = typer.Option(None, "-p", help="Nouveau mot de passe"),
    first_name: str = typer.Option(None, "-fn", help="Nouveau prénom"),
    last_name: str = typer.Option(None, "-ln", help="Nouveau nom"),
    phone: str = typer.Option(None, "-ph", help="Nouveau téléphone"),
    role_id: int = typer.Option(None, "-r", help="Nouveau rôle"),
):
    """Updates an existing user."""

    try:
        user = User.get_by_id(uid)
    except DoesNotExist:
        console.print(
            format_text('bold', 'red', f"❌ Erreur : L'utilisateur ID {uid} n'existe pas.")
        )
        raise typer.Exit()

    updates = {}

    if username:
        updates["username"] = username
    if email:
        updates["email"] = email
    if password:
        updates["password"] = ph.hash(password)
    if first_name:
        updates["first_name"] = first_name
    if last_name:
        updates["last_name"] = last_name
    if phone:
        updates["phone"] = phone
    if role_id:
        try:
            updates["role"] = Role.get_by_id(role_id)
        except DoesNotExist:
            console.print(
                format_text('bold', 'red', "❌ Erreur : Rôle invalide.")
            )
            raise typer.Exit()
    
    try:
        if updates:
            for key, value in updates.items():
                setattr(user, key, value)
            user.save()
            console.print(
                format_text('bold', 'green', f"✅ Utilisateur {uid} mis à jour avec succès !")
            )
        else:
            console.print(
                format_text('bold', 'yellow', "⚠ Aucun champ à mettre à jour.")
            )
            raise typer.Exit()
    except ValueError as e:
        console.print(format_text('bold', 'red', f"❌ {str(e)}"))
        raise typer.Exit(1)

@app.command("delete")
def delete_user(
    ctx: typer.Context,
    user_id: int = typer.Argument(..., help="ID de l'user à supprimer")
):
    """Deletes an existing user."""

    try:
        user = User.get_by_id(user_id)
    except DoesNotExist:
        console.print(
            format_text('bold', 'red', f"❌ Erreur : L'utilisateur ID {user_id} n'existe pas.")
        )
        raise typer.Exit()

    confirm = Confirm.ask(
        format_text('bold', 'yellow', f"⚠ Êtes-vous sûr de vouloir supprimer {user.username} ?")
    )

    if confirm:
        user.delete_instance()
        console.print(
            format_text('bold', 'green', f"✅ Utilisateur {user.username} supprimé avec succès !")
        )
    else:
        console.print(
            format_text('bold', 'red', "❌ Opération annulée.")
        )
        raise typer.Exit()
