import jwt
import typer
import sys
import os
from argon2 import PasswordHasher
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Optional
from models.user import User
from models.rolepermission import RolePermission
from models.permission import Permission
from dotenv import load_dotenv, get_key
from rich import print
from rich.console import Console
from rich.style import Style
from rich.table import Table
from enum import Enum


console = Console()

# AUTH & TOKEN Configuration
load_dotenv()
JWT_SECRET = os.getenv('SECRET_KEY')
JWT_EXPIRE = int(get_key(".env", "TOKEN_EXP"))
if not JWT_SECRET:
    raise ValueError("La clé secrète JWT n'est pas définie dans les variables d'environnement")
JWT_ALGORITHM = 'HS256'
TOKEN_FILE = Path('.jwt')
app = typer.Typer()
ph = PasswordHasher()


class Entity(Enum):
    USER = "users"
    CUSTOMER = "customers"
    CONTRACT = "contracts"
    EVENT = "events"


class Operation(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"


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
            console.print(
                format_text('bold', 'red', "❌ Token manquant. Veuillez vous connecter.")
            )
            return None

        token = TOKEN_FILE.read_text().strip()
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Expiration check
        exp_timestamp = payload['exp']
        if datetime.utcnow().timestamp() > exp_timestamp:
            remove_token()
            console.print(
                format_text('bold', 'red', "❌ Token expiré. Veuillez vous reconnecter.")
            )
            return None

        return payload

    except jwt.InvalidTokenError:
        remove_token()
        console.print(
            format_text('bold', 'red', "❌ Token invalide. Veuillez vous reconnecter.")
        )
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
    return {
        'token': token,
        'user_id': user.id,
        'role': user.role.name
    }

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
    Checks if user can operate on entity.
    
    Args:
        user: actual User
        entity: target entity
        operation: CRUDL
        target_id: self object ID
    """
    # Admin can do it all
    if user.role.name.lower() == "admin":
        return True

    # Sales rules
    if user.role.name.lower() == "sales":
        if entity == Entity.USER.value:
            # Only on himself
            return (operation in ["read", "update", "delete"] and 
                   target_id is not None and 
                   target_id == user.id)
        # Full Access to customers, contracts & events
        return entity in [Entity.CUSTOMER.value, Entity.CONTRACT.value, Entity.EVENT.value]

    # Support rules
    if user.role.name.lower() == "support":
        if entity == Entity.USER.value:
            # Only on himself
            return (operation in ["read", "update", "delete"] and 
                   target_id is not None and 
                   target_id == user.id)
        if entity in [Entity.CUSTOMER.value, Entity.CONTRACT.value]:
            # ReadOnly customers & contracts
            return operation in ["read", "list"]
        if entity == Entity.EVENT.value:
            return operation != "create"

    return False

def get_target_id_from_args(args) -> Optional[int]:
    """Extract target ID from command arguments."""
    if args and len(args) > 0:
        try:
            return int(args[-1])  # Prendre le dernier argument
        except ValueError:
            return None
    return None

def check_auth(ctx: typer.Context) -> None:
    """Checks that user is authentified and allowed before each command."""
    command: str | None = ctx.invoked_subcommand
    
    if command in ["users create", "login", "logout"]:
        return
    
    user: User | None = is_logged()
    if not user:
        console.print(format_text('bold', 'red', "❌ Vous devez être connecté pour exécuter cette commande."))
        raise typer.Exit(1)

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

def display_list(title: str, items: list, use_context: bool = False):
    """Displays a list of records."""

    # See https://rich.readthedocs.io/en/stable/protocol.html?highlight=__rich__#console-customization

    table = Table(
        title=title,
        padding=(0, 1),
        header_style="blue bold",
        title_style="purple bold",
        title_justify="center",
    )

    if not items:
        console.print(format_text('bold', 'red', "❌ Aucun élément à afficher."))
        return

    headers = list(items[0].keys())

    if "Contexte" in headers:
        headers.remove("Contexte")

    for title in headers:
        table.add_column(title, style="cyan", justify="center")

    for item in items:
        values = [str(item[key]) for key in headers]
        style = item.get("Contexte", "white") if use_context else "white"
        table.add_row(*values, style=style)

    console = Console()
    print("")
    console.print(table)

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
    valid_colors = ['red', 'yellow', 'green', 'blue', 'purple', 'orange', 'brown']
    style_map = {
        'bold': 'bold',
        'italic': 'italic',
        'underline': 'underline',
        'strike': 'strike'
    }

    if style == 'normal' and color in valid_colors:
        return f"[{color}]{text}[/{color}]"

    valid_style = style in style_map
    valid_color = color in valid_colors

    if not valid_style and not valid_color:
        return text

    if not valid_style and valid_color:
        return f"[{color}]{text}[/{color}]"

    if valid_style and not valid_color:
        style_tag = style_map[style]
        return f"[{style_tag}]{text}[/{style_tag}]"

    style_tag = style_map[style]
    return f"[{style_tag} {color}]{text}[/{style_tag} {color}]"