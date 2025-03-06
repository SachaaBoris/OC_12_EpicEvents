import os
import typer
from epicevents.cli import users, customers, contracts, events, utils
from epicevents.permissions import auth
from epicevents.permissions.auth import check_auth

app = typer.Typer(
    add_completion=False,
    help="Application de gestion d'événements Epic Events",
    context_settings={"help_option_names": ["-h", "--help", "--h", "-help"]}
)

# Sub Commands
app.add_typer(users.app, name="user", help="Gestion des utilisateurs", callback=check_auth)
app.add_typer(customers.app, name="customer", help="Gestion des clients", callback=check_auth)
app.add_typer(contracts.app, name="contract", help="Gestion des contrats", callback=check_auth)
app.add_typer(events.app, name="event", help="Gestion des événements", callback=check_auth)
app.add_typer(auth.app, name="util", help="Fonctions utilitaires", callback=check_auth)

def main():
    """Point d'entrée principal de l'application"""
    app(obj={})

if __name__ == "__main__":
    main()
