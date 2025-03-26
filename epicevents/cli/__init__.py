import typer


# Creates typer instance
app = typer.Typer(
    add_completion=False,
    help="Application de gestion d'événements Epic Events",
    context_settings={"help_option_names": ["-h", "--help", "--h", "-help"]}
)


def init_cli():
    from epicevents.permissions.auth import check_auth
    from epicevents.cli import users, customers, contracts, events, debug

    # Adding sub-commands
    app.add_typer(users.app, name="user", help="Gestion des utilisateurs", callback=check_auth)
    app.add_typer(customers.app, name="customer", help="Gestion des clients", callback=check_auth)
    app.add_typer(contracts.app, name="contract", help="Gestion des contrats", callback=check_auth)
    app.add_typer(events.app, name="event", help="Gestion des événements", callback=check_auth)
    app.add_typer(debug.app, name="debug", help="Fonctions de debug", callback=check_auth)

    return app
