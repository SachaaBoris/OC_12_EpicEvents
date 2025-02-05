import typer
from cli import auth, customers, users, contracts, events


app = typer.Typer(add_completion=False)

# Auth
app.command(name="login")(auth.login)
app.command(name="logout")(auth.logout)
app.command(name="debug_token")(auth.debug_token)

# Sub Commands
#app.add_typer(auth.app, name="auth", help="Authentification")
app.add_typer(users.app, name="users", help="Gestion des utilisateurs")
app.add_typer(customers.app, name="customers", help="Gestion des clients")
app.add_typer(contracts.app, name="contracts", help="Gestion des contrats")
app.add_typer(events.app, name="events", help="Gestion des événements")

if __name__ == "__main__":
    app()
