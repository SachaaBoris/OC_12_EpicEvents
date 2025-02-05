import typer

app = typer.Typer(help="Gestion des événements")

@app.command("create")
def create_event(
    ct: int = typer.Option(..., "--ct", help="Numéro du contrat associé"),
    d: str = typer.Option(..., "--d", help="Date de l'événement (YYYY-MM-DD)"),
    l: str = typer.Option(..., "--l", help="Localisation"),
    a: int = typer.Option(..., "--a", help="Nombre de participants"),
    n: str = typer.Option(None, "--n", help="Notes"),
    u: int = typer.Option(0, "--u", help="Numéro du commercial associé")
):
    """Creates a new event."""
    typer.echo(f"Événement créé pour le contrat {ct} à {l} le {d}, {a} participants.")

@app.command("filter")
def filter_events(s: bool = typer.Option(False, "-s", help="Filtrer les événements passés")):
    """Filters passed avents."""
    typer.echo(f"Filtrage des événements passés : {s}")

@app.command("list")
def list_events():
    """List all events."""
    events = Event.select()
    if not events.count():
        typer.echo("❌ Aucun événements n'est enregistré dans la bdd.")
        return

    # Ordering events for display
    current_date = datetime.now()
    future_events = []
    past_events = []
    
    for event in events:
        if event.event_date > current_date:
            future_events.append(event)
        else:
            past_events.append(event)
    
    future_events.sort(key=lambda x: x.event_date)
    past_events.sort(key=lambda x: x.event_date, reverse=True)

    if future_events:
        typer.echo("\n📅 Événements à venir :")
        for event in future_events:
            typer.echo(f"{event.id}: {event.event_date}, {event.name}, {event.attendees} personnes")
    
    if past_events:
        typer.echo("\n📅 Événements passés :")
        for event in past_events:
            typer.echo(f"{event.id}: {event.event_date}, {event.name}, {event.attendees} personnes")

@app.command("update")
def update_event(
    event_id: int = typer.Argument(..., help="N° de l'événement à modifier"),
    new_value: str = typer.Argument(..., help="Nouvelle valeur à appliquer"),
    ct: bool = typer.Option(False, "-ct", help="Modifier le numéro du contrat"),
    d: bool = typer.Option(False, "-d", help="Modifier la date de l'événement"),
    l: bool = typer.Option(False, "-l", help="Modifier la localisation"),
    a: bool = typer.Option(False, "-a", help="Modifier le nombre de participants"),
    n: bool = typer.Option(False, "-n", help="Modifier les notes"),
    u: bool = typer.Option(False, "-u", help="Modifier le numéro du support associé")
):
    """Updates existing event."""
    typer.echo(f"Modification de l'événement {event_id}: {new_value}")

if __name__ == "__main__":
    app()
