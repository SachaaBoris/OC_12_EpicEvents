import jwt
import typer
import sys
import os
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv, get_key
from rich.color import ANSI_COLOR_NAMES
from rich import print
from rich.console import Console
from epicevents.cli.utils import display_list
from epicevents.cli.utils import format_text
from epicevents.cli.utils import welcome_user
from epicevents.models.user import User
from epicevents.permissions.checker import has_permission
from epicevents.permissions.utils import get_all_permissions


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

class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass

def remove_token():
    """Logs out user by removing token."""
    TOKEN_FILE.unlink(missing_ok=True)

def generate_token(user: User) -> str:
    """Generates a JWT token for a user."""
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
    """Verifying stored token validity."""
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
    """Authenticates a user and generates a token."""
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

def is_logged() -> User | None:
    """Returns user matching the token or None."""
    payload = verify_token()
    if not payload:
        return None

    return User.get_or_none(User.id == payload.get("user_id"))

@app.command("debug_token")
def debug_token():
    """Displays token validity."""
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

@app.command("debug_permissions")
def debug_permissions():
    """Displays all permissions."""
    all_permissions = get_all_permissions()
    display_list(title="Permissions disponibles", items=all_permissions)

@app.command("debug_commands")
def list_commands():
    """Lists all available CLI commands and subcommands in the Epicevents CLI."""
    import importlib
    from epicevents.__main__ import app
    for command in app.registered_commands:
        console.print(format_text('bold', 'blue', f"- {command.name}"))

    for sub_typer in app.registered_groups:
        sub_name = sub_typer.name
        console.print(format_text('bold', 'blue', f"- {sub_name}"))

        for sub_command in sub_typer.typer_instance.registered_commands:
            console.print(format_text('bold', 'blue', f"  - {sub_command.name}"))

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
    resource = ctx.info_name
    action = command 
    target_id = get_target_id_from_args(sys.argv)

    if has_permission(user, resource, action, target_id):
        return

    console.print(
        format_text('bold', 'red', f"❌ Vous n'avez pas l'autorisation d'exécuter '{resource} {action}'.")
    )
    raise typer.Exit(1)

def get_target_id_from_args(args) -> Optional[int]:
    """Extract target ID from command arguments."""
    if args and len(args) > 0:
        try:
            return int(args[-1])  # last arg
        except ValueError:
            return None
    return None
