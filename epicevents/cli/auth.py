import jwt
import typer
import os
from argon2 import PasswordHasher
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Optional
from models.user import User
from dotenv import load_dotenv, get_key


# Configuration
load_dotenv()
JWT_SECRET = os.getenv('SECRET_KEY')
JWT_EXPIRE = int(get_key(".env", "TOKEN_EXP"))
if not JWT_SECRET:
    raise ValueError("La clé secrète JWT n'est pas définie dans les variables d'environnement")
JWT_ALGORITHM = 'HS256'
TOKEN_FILE = Path('.jwt')
app = typer.Typer()
ph = PasswordHasher()

class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass

def remove_token():
    """Log out user by removing token"""
    TOKEN_FILE.unlink(missing_ok=True)

def generate_token(user: User) -> str:
    """Generate a JWT token for a user"""
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
    """Verify the stored token validity"""
    try:
        if not TOKEN_FILE.exists():
            return None

        token = TOKEN_FILE.read_text().strip()
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Expiration check
        exp_timestamp = payload['exp']
        if datetime.utcnow().timestamp() > exp_timestamp:
            remove_token()
            typer.echo("❌ Token expiré. Veuillez vous reconnecter.")
            return None

        return payload

    except jwt.InvalidTokenError:
        remove_token()
        typer.echo("❌ Token invalide. Veuillez vous reconnecter.")
        return None

def authenticate_user(username: str, password: str) -> dict:
    """Authenticates a user and generates a token"""
    try:
        user = User.get(User.username == username)
        try:
            ph.verify(user.password, password)
        except VerifyMismatchError:
            raise AuthenticationError("Mot de passe incorrect")
            
        token = generate_token(user)
        return {
            'token': token,
            'user_id': user.id,
            'role': user.role.name
        }
    except User.DoesNotExist:
        raise AuthenticationError("Utilisateur non trouvé")


@app.command()
def login(
    username: str = typer.Option(..., "--username", "-u", help="Nom d'utilisateur"),
    password: str = typer.Option(..., "--password", "-p", help="Mot de passe")
):
    """Authenticate user through CLI"""
    try:
        result = authenticate_user(username, password)
        typer.echo(f"✅ Connecté en tant que {username} (rôle: {result['role']})")
    except AuthenticationError as e:
        typer.echo(f"❌ Erreur d'authentification : {str(e)}")
        raise typer.Exit(1)

@app.command()
def logout():
    """Log out current user through CLI"""
    payload = verify_token()
    if payload:
        user_id = payload.get("user_id")
        user = User.get_by_id(user_id)
        remove_token()
        typer.echo(f"✅ {user.username} déconnecté(e).")
    else:
        typer.echo("❌ Vous n'étiez pas connecté.")

@app.command()
def debug_token():
    """Checking token validity"""
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
        
        typer.echo(f"⏳ Token expire le : {exp_datetime} - Temps restant : {remaining_time_str}")
    else:
        typer.echo("❌ Token inexistant.")

#def require_auth(func):
#    """Decorator to verify authentication before executing command"""
#    @wraps(func)
#    def wrapper(*args, **kwargs):
#        payload = verify_token()
#        if not payload:
#            raise typer.Exit("❌ Erreur : Utilisateur non authentifié ou session expirée")
#        kwargs['user_id'] = payload['user_id']
#        return func(*args, **kwargs)
#    return wrapper