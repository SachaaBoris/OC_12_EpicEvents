import jwt
import sys
import typer
import sentry_sdk
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from rich.console import Console
from epicevents.cli.utils import format_text
from epicevents.cli.utils import welcome_user
from epicevents.models.user import User
from epicevents.permissions.perm import has_permission
from epicevents.config import SECRET_KEY, TOKEN_EXP
from epicevents.config import SENTRY_ENV


console = Console()
ph = PasswordHasher()

# AUTH & TOKEN Configuration
JWT_SECRET = SECRET_KEY
JWT_EXPIRE = TOKEN_EXP
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
        'exp': (datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE)).timestamp()
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
        if datetime.now(timezone.utc).timestamp() > exp_timestamp:
            remove_token()
            return None

        return payload

    except jwt.InvalidTokenError as e:
        remove_token()
        console.print(
            format_text('bold', 'red', f"Token Invalide : {e}")
        )
        return None


# Password remove from sys.argv
def sanitize_argv():
    if len(sys.argv) >= 3 and sys.argv[1] == "user" and sys.argv[2] == "login":
        sanitized_args = []
        skip_next = False

        for arg in sys.argv:
            if skip_next:
                sanitized_args.append("****")  # Masque l'argument sensible
                skip_next = False
            elif arg.lower() in ["-p", "-password", "-pass", "--p", "--password", "--pass"]:
                sanitized_args.append(arg)
                skip_next = True
            else:
                sanitized_args.append(arg)

        sys.argv = sanitized_args


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticates a user and generates a token."""
    try:
        user = User.get(User.username == username)
    except User.DoesNotExist:
        console.print(
            format_text('bold', 'red', "❌ Utilisateur non trouvé.")
        )

        if SENTRY_ENV == "production":
            # Sends to Sentry if we're in production
            sanitize_argv()
            error_log = f"Utilisateur inexistant : '{username}'."
            sentry_sdk.set_extra("event_details", {
                "event": "unexisting user",
                "source": username,
            })
            sentry_sdk.capture_message(error_log, level="warning")

        return None

    try:
        ph.verify(user.password, password)
    except VerifyMismatchError:
        console.print(
            format_text('bold', 'red', "❌ Mot de passe incorrect.")
        )

        if SENTRY_ENV == "production":
            # Sends to Sentry if we're in production
            sanitize_argv()
            error_log = f"Mot de passe erroné : '{username}'."
            sentry_sdk.set_extra("event_details", {
                "event": "wrong pw",
                "source": username,
            })
            sentry_sdk.capture_message(error_log, level="warning")

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

    has_perm, error_message = has_permission(user, resource, action, target_id)

    if has_perm:
        return

    # Display & log both the standard error message and the detailed reason if available
    error_log = f"Permission denied for user {user.id} on {resource} {action}"
    if error_message:
        error_log += f": {error_message}"
        console.print(format_text('bold', 'red', f"❌ Vous n'avez pas l'autorisation d'exécuter '{resource} {action}'."))
        console.print(format_text('italic', 'red', f"   Raison: {error_message}"))
    else:
        console.print(format_text('bold', 'red', f"❌ Vous n'avez pas l'autorisation d'exécuter '{resource} {action}'."))

    if SENTRY_ENV == "production":
        # Sends to Sentry if we're in production
        sentry_sdk.set_extra("event_details", {
            "event": "unauthorized",
            "source_id": user.id,
            "resource": resource,
            "action": action,
            "target_id": target_id
        })
        sentry_sdk.capture_message(error_log, level="warning")

    raise typer.Exit(1)


def get_target_id_from_args(args) -> Optional[int]:
    """Extract target ID from command arguments."""
    if not args:
        return None

    # Find the subcommand position (create, read, update, delete)
    for i, arg in enumerate(args):
        if arg in ["create", "read", "update", "delete"]:
            # If we found a subcommand and there's another argument after it
            if i + 1 < len(args):
                try:
                    # Try to convert the next argument to an integer (the ID)
                    if not args[i + 1].startswith("-"):  # option flag
                        return int(args[i + 1])
                except ValueError:
                    pass

    return None
