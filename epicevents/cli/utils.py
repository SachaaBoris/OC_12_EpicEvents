import jwt
import typer
import sys
import os
import time
import keyboard
from argon2 import PasswordHasher
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Optional
from models.user import User
from models.role import Role
from models.rolepermission import RolePermission
from models.permission import Permission
from dotenv import load_dotenv, get_key
from rich.color import ANSI_COLOR_NAMES
from rich import print
from rich.console import Console
from rich.style import Style
from rich.table import Table
from enum import Enum


VALID_RICH_COLORS = list(ANSI_COLOR_NAMES.keys())

console = Console()
app = typer.Typer()
ph = PasswordHasher()

# AUTH & TOKEN Configuration
load_dotenv()
JWT_SECRET = os.getenv('SECRET_KEY')
JWT_EXPIRE = int(get_key(".env", "TOKEN_EXP"))
if not JWT_SECRET:
    raise ValueError("La clé secrète JWT n'est pas définie dans les variables d'environnement")
JWT_ALGORITHM = 'HS256'
TOKEN_FILE = Path('.jwt')
ITEMS_PP = int(get_key(".env", "ITEMS_PER_PAGE"))

def remove_token():
    """Logs out user by removing token"""
    TOKEN_FILE.unlink(missing_ok=True)

def generate_token(user: User) -> str:
    """Generates a JWT token for a user"""
    payload = {
        'user_id': user.id,
        'role': user.role.name,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRE)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Saving token as .jwt file
    TOKEN_FILE.write_text(token)
    return token

def verify_token() -> Optional[dict]:
    """Verifying stored token validity"""
    try:
        if not TOKEN_FILE.exists():
            return None

        token = TOKEN_FILE.read_text().strip()
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Expiration check
        exp_timestamp = payload['exp']
        if datetime.utcnow().timestamp() > exp_timestamp:
            remove_token()
            return None

        return payload

    except jwt.InvalidTokenError:
        remove_token()
        return None

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticates a user and generates a token"""
    try:
        user = User.get(User.username == username)
    except User.DoesNotExist:
        console.print(
            format_text('bold', 'red', "❌ Utilisateur non trouvé.")
        )
        return None

    try:
        ph.verify(user.password, password)
    except VerifyMismatchError:
        console.print(
            format_text('bold', 'red', "❌ Mot de passe incorrect.")
        )
        return None
        
    token = generate_token(user)
    welcome_user()
    return {
        'token': token,
        'user_id': user.id,
        'role': user.role.name
    }

@app.command("debug_rolperm")
def debug_rolperm():
    # Displays users permissions
    users = User.select()

    permissions_list = []

    for user in users:
        if not user.role:
            continue

        role = user.role.name
        permissions = []
        role_permissions = RolePermission.select().where(RolePermission.role == user.role)
        for role_permission in role_permissions:
            permission = role_permission.permission.name
            permissions.append(permission)

        permissions_list.append({
            "user": user.username,
            "role": role,
            "permissions": ", ".join(permissions)
        })

    display_list("Liste des permissions", permissions_list)

@app.command("debug_token")
def debug_token():
    """Displays token validity"""
    payload = verify_token()
    if payload is not None:
        exp_timestamp = payload['exp']
        exp_datetime = datetime.fromtimestamp(exp_timestamp).strftime('%d/%m/%y %H:%M')
        remaining_time = exp_timestamp - datetime.now().timestamp()
        if remaining_time > 0:
            hours, remainder = divmod(remaining_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            remaining_time_str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        else:
            remaining_time_str = "Le token vient d'expirer."

        console.print(
            format_text('bold', 'blue', f"⏳ Token expire le : {exp_datetime} - Temps restant : {remaining_time_str}")
        )

def check_permission(user: User, entity: str, operation: str, target_id: Optional[int] = None) -> bool:
    """
    Checks if the user has permission to perform a specific operation on a given entity.

    Args:
        user (User): The user whose permissions are being checked.
        entity (str): The entity on which the operation is being performed (e.g., "user", "util").
        operation (str): The operation being performed (e.g., "read", "update", "delete").
        target_id (Optional[int]): The ID of the target entity. Used for self-access checks.

    Returns:
        bool: True if the user has the required permission, False otherwise.
    """

    # Special case for the "util" entity: only admins have access
    if entity == "util":
        return user.role.name == "admin"

    # Check if this is a self-access case (e.g., user updating their own profile)
    is_self_access = entity == "user" and operation in ["read", "update", "delete"] and target_id == user.id

    # Construct permission name based on the entity, operation, and self-access status
    permission_name = f"{entity}_{operation}_self" if is_self_access else f"{entity}_{operation}"

    # Fetch permission from database
    permission = Permission.get_or_none(Permission.name == permission_name)

    # Check if user's role has the required permission
    role_permission = RolePermission.get_or_none(
        (RolePermission.role == user.role) &
        (RolePermission.permission == permission.id)
    )

    return role_permission is not None

def get_target_id_from_args(args) -> Optional[int]:
    """Extract target ID from command arguments."""
    if args and len(args) > 0:
        try:
            return int(args[-1])  # last arg
        except ValueError:
            return None
    return None

def check_auth(ctx: typer.Context) -> None:
    """Checks that user is authentified and allowed before each command."""
    command: str | None = ctx.invoked_subcommand
    
    if command in ["login", "logout"]:
        return
    
    user: User | None = is_logged()
    if not user:
        console.print(format_text('bold', 'red', "❌ Vous devez être connecté pour exécuter cette commande."))
        raise typer.Exit(1)

    ctx.obj = user
    entity = ctx.info_name
    operation = command 
    target_id = get_target_id_from_args(sys.argv)

    if check_permission(user, entity, operation, target_id):
        return

    console.print(
        format_text('bold', 'red', f"❌ Vous n'avez pas l'autorisation d'exécuter '{entity} {operation}'.")
    )
    raise typer.Exit(1)

def is_logged() -> User | None:
    """Returns user matching the token or None."""
    payload = verify_token()
    if not payload:
        return None

    return User.get_or_none(User.id == payload.get("user_id"))

def validate_rich_color(color=None):
    """Returns a rich valid color anyways"""
    valid_colors = VALID_RICH_COLORS if isinstance(VALID_RICH_COLORS, list) else ["white"]
    if not isinstance(color, str) or color not in valid_colors:
        return "white"
    return color

def display_list(title: str, items: list, use_context: bool = False):
    """Displays a list of records with pagination."""

    # See https://rich.readthedocs.io/en/stable/protocol.html?highlight=__rich__#console-customization

    items_per_page = ITEMS_PP
    total_items = len(items)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    current_page = 1 

    while current_page <= total_pages:
        start_index = (current_page - 1) * items_per_page
        end_index = min(start_index + items_per_page, total_items)
        page_items = items[start_index:end_index]
        title_str = title if total_pages <= 1 else f"{title} (Page {current_page}/{total_pages})"
        
        table = Table(
            title=title_str,
            padding=(0, 1),
            header_style="blue bold",
            title_style="purple bold",
            title_justify="center",
        )

        if not page_items:
            console.print(format_text('bold', 'red', "❌ Aucun élément à afficher."))
            return

        headers = list(page_items[0].keys())

        if "Contexte" in headers:
            headers.remove("Contexte")

        for header in headers:
            table.add_column(header, style="cyan", justify="center")

        for item in page_items:
            values = [str(item[key]) for key in headers]
            color = validate_rich_color(item.get("Contexte", "white"))
            style = color if use_context else "white"
            table.add_row(*values, style=style)

        console.print(table)

        if current_page < total_pages:
            console.print(format_text('bold', 'yellow', "Appuyez sur 'Backspace' pour continuer, 'Echap' pour quitter."))
            time.sleep(0.2)

            # Wait for user input
            while True:
                if keyboard.is_pressed('backspace'):
                    current_page += 1
                    time.sleep(0.2)
                    break
                elif keyboard.is_pressed('escape'):
                    time.sleep(0.2)
                    return
                time.sleep(0.1)
        else:
            current_page += 1

def format_text(style: str, color: str, text: str) -> None:
    """
    Formats text with a Rich style and color.

    Args:
        style (str): Text style ('bold', 'italic', 'underline', 'strike', or 'normal')
        color (str): Desired color
        text (str): Text to format

    Returns:
        str: Text formatted with Rich tags

    Examples:
        error_text = format_text('bold', 'red', '❌ Error: Invalid role.')
        confirm = Confirm.ask(format_text('bold', 'yellow', '⚠ Confirmation required'))
        italic_warning = format_text('italic', 'red', 'Warning')
        underlined_text = format_text('underline', 'green', 'Important')
        striked_text = format_text('strike', 'red', 'Deleted')
        normal_text = format_text('normal', 'blue', 'Normal text')
    """

    color = validate_rich_color(color)

    style_map = {
        'bold': 'bold',
        'italic': 'italic',
        'underline': 'underline',
        'strike': 'strike'
    }

    valid_style = style in style_map
    if style == 'normal' or not valid_style:
        return f"[{color}]{text}[/{color}]"

    style_tag = style_map[style]
    return f"[{style_tag} {color}]{text}[/{style_tag} {color}]"

def welcome_user():
    print("")
    print("                        ###    ")
    print("                      ###      ")
    print("       ################    ####")
    print("       #          ###         #")
    print("       #        ###           #")
    print("       #      ###             #")
    print("       #    ###      ###      #")
    print("       #  ###      ###        #")
    print("       #         ###     ###  #")
    print("       #       ###     ###    #")
    print("       #     ###     ###      #")
    print("       #           ###        #")
    print("       #         ###          #")
    print("       #####   ################")
    print("             ###               ")
    print("           ###                 ")
    print("")
    print("        WELCOME TO EPICEVENTS")
    print("  Customer Relationship Management")
    print("")



