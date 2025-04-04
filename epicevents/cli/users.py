import typer
from rich.console import Console
from rich.prompt import Confirm
from peewee import DoesNotExist
from argon2 import PasswordHasher
from epicevents.models.user import User
from epicevents.models.role import Role
from epicevents.permissions.auth import AuthenticationError
from epicevents.permissions.auth import authenticate_user
from epicevents.permissions.auth import verify_token
from epicevents.permissions.auth import remove_token
from epicevents.cli.utils import display_list
from epicevents.cli.utils import format_text


app = typer.Typer(help="Gestion des utilisateurs")
console = Console()
ph = PasswordHasher()


# AUTH operations
@app.command("login")
def login(
    username: str = typer.Option(..., "-u", help="Nom d'utilisateur"),
    password: str = typer.Option(..., "-p", help="Mot de passe")
):
    """Authenticates user through CLI"""
    try:
        user_obj = authenticate_user(username, password)
        if user_obj:
            console.print(
                format_text('bold', 'green', f"✅ Connecté en tant que {username} (rôle: {user_obj['role']})")
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
    role_id: int = typer.Option(..., "-r", help="Numéro de rôle (1: Admin, 2: Management, 3: Sales, 4: Support)")
):
    """Creates a new user."""

    # Check if user already exists
    if User.select().where((User.username == username) | (User.email == email)).exists():
        console.print(
            format_text('bold', 'red', "❌ Erreur : User déjà enregistré.")
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

    try:
        user.save()
        console.print(
            format_text('bold', 'green', f"✅ Utilisateur {user.username} créé avec succès !")
        )
    except ValueError as e:
        # Intercepte les erreurs de validation de la classe User
        console.print(
            format_text('bold', 'red', f"❌ {str(e)}")
        )
        raise typer.Exit(1)


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
            format_text('bold', 'red', "❌ Erreur : Vous n'avez pas fourni d'ID utilisateur.")
        )


@app.command("list")
def list_users(
    ctx: typer.Context,
    filter_on: bool = typer.Option(False, "--fi", help="Filtre automatique des utilisateurs selon votre rôle.")
):
    """Lists all users."""

    nobody_message = "❌ Aucun utilisateur n'est enregistré dans la bdd."
    title_str = "Liste des utilisateurs"

    if filter_on:
        user = ctx.obj
        users = User.select().join(Role).where(Role.name == user.role.name)
        title_str = title_str + f" ({user.role.name})"
    else:
        users = User.select()

    if not users.exists():
        console.print(format_text('bold', 'red', f"{nobody_message}"))
        return

    users_list = []
    for user in users:
        context_color = "red" if not user.role else "white"

        users_list.append(
            {
                "ID": user.id,
                "USERNAME": user.username,
                "EMAIL": user.email,
                "ROLE": user.role.name if user.role else "Aucun",
                "Contexte": context_color,
            }
        )

    users_list = sorted(users_list, key=lambda x: x["ID"], reverse=False)
    display_list(title_str, users_list, use_context=True)


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
    if role_id is not None:
        updates["role"] = role_id

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
                format_text('bold', 'yellow', "⚠  Aucun champ à mettre à jour.")
            )
            raise typer.Exit()
    except ValueError as e:
        console.print(format_text('bold', 'red', f"{str(e)}"))
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
