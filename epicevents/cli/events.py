import typer
import os
from datetime import datetime
from rich.console import Console
from rich.prompt import Confirm
from peewee import DoesNotExist
from typing import Optional
from epicevents.models.event import Event
from epicevents.models.contract import Contract
from epicevents.models.customer import Customer
from epicevents.models.user import User
from epicevents.cli.utils import display_list
from epicevents.cli.utils import format_text


app = typer.Typer(help="Gestion des événements")
console = Console()

@app.command("create")
def create_event(
    contract_id: int = typer.Option(..., "-ct", help="Numéro du contrat associé"),
    event_name: str = typer.Option(..., "-t", help="Nom de l'événement"),
    event_date: str = typer.Option(..., "-d", help="Date de l'événement (YYYY-MM-DD HH:MM)"),
    place: str = typer.Option(..., "-l", help="Localisation"),
    attendees: int = typer.Option(..., "-a", help="Nombre de participants"),
    notes: str = typer.Option(None, "-n", help="Notes"),
    contact_id: Optional[int] = typer.Option(None, "-u", help="Numéro du support associé")
):
    """Creates a new event."""

    event = Event(
        contract_id=contract_id,
        name = event_name,
        event_date=event_date,
        location=place,
        attendees=attendees,
        notes=notes,
        team_contact_id=contact_id
    )

    try:
        event.save()
        console.print(format_text('bold', 'green', f"✅ Événement créé : {event.name} pour le {event_date}"))
    except ValueError as e:
        console.print(format_text('bold', 'red', f"❌ {str(e)}"))
        raise typer.Exit(1)

@app.command("read")
def read_event(event_id: int = typer.Argument(..., help="ID de l'événement à afficher")):
    """Shows a specific event."""

    try:
        event = Event.get_by_id(event_id)
        event_data = [
            {"Champ": "ID", "Valeur": event.id},
            {"Champ": "Date", "Valeur": event.event_date},
            {"Champ": "Nom", "Valeur": event.name},
            {"Champ": "Localisation", "Valeur": event.location},
            {"Champ": "Participants", "Valeur": event.attendees},
            {"Champ": "Notes", "Valeur": event.notes},
            {"Champ": "Contact Epic", "Valeur": f"{event.team_contact_id.first_name} {event.team_contact_id.last_name.upper()} ({event.team_contact_id.id})" if isinstance(event.team_contact_id, User) else f"ID: {event.team_contact_id}" if event.team_contact_id else "Aucun"},
        ]
        display_list(f"Événement {event.id} : {event.name}", event_data)
    except DoesNotExist:
        console.print(format_text('bold', 'red', f"❌ L'événement {event_id} n'existe pas."))
        raise typer.Exit()

@app.command("list")
def list_events(
    ctx: typer.Context,
    filter_on: bool = typer.Option(False, "--fi", help="Filtre automatiquement les événement selon votre rôle")
):
    """List all events."""
    events = Event.select()
    current_date = datetime.now()
    nothing_message = "❌ Aucun événement n'est enregistré dans la bdd."

    if filter_on:
        user = ctx.obj
        if user.role.name == "sales":
            events = events.where(Event.event_date > current_date)
            nothing_message = "❌ Aucun événement futur n'est enregistré dans la bdd."
        elif user.role.name in ["admin", "management"]:
            events = events.where(Event.team_contact_id.is_null(True))
            nothing_message = "❌ Aucun événement sans agent n'est enregistré dans la bdd."
        else:  # support
            events = events.where(Event.team_contact_id == user.id)
            nothing_message = "❌ Aucun événement avec agent n'est enregistré dans la bdd."

    if not events.count():
        console.print(format_text('bold', 'red', f"{nothing_message}"))
        return

    # Ordering events for display
    future_events = []
    past_events = []
    for event in events:
        if event.event_date > current_date:
            future_events.append(event)
        else:
            past_events.append(event)
    future_events.sort(key=lambda x: x.event_date)
    past_events.sort(key=lambda x: x.event_date, reverse=True)

    event_list = []
    # Future Events
    for event in future_events:
        context_color = "red" if event.team_contact_id is None else "blue"
        event_list.append(
            {
                "ID": event.id,
                "Date": event.event_date,
                "Nom": event.name,
                "Participants": event.attendees,
                "Contexte": context_color,
            }
        )

    # Past Events
    for event in past_events:
        context_color = "red" if event.team_contact_id is None else "wheat4"
        event_list.append(
            {
                "ID": event.id,
                "Date": event.event_date,
                "Nom": event.name,
                "Participants": event.attendees,
                "Contexte": context_color,
            }
        )

    event_list = sorted(event_list, key=lambda x: x["ID"], reverse=False)
    display_list("Liste des événements", event_list, use_context=True)

@app.command("update")
def update_event(
    event_id: int = typer.Argument(..., help="ID de l'évennement à modifier"),
    contract_id: int = typer.Option(None, "-ct", help="Numéro du contrat associé"),
    event_name: str = typer.Option(None, "-t", help="Nom de l'événement"),
    event_date: str = typer.Option(None, "-d", help="Date de l'événement (YYYY-MM-DD)"),
    place: str = typer.Option(None, "-l", help="Localisation"),
    attendees: int = typer.Option(None, "-a", help="Nombre de participants"),
    notes: str = typer.Option(None, "-n", help="Notes"),
    contact_id: int = typer.Option(None, "-u", help="Numéro du commercial associé")
):
    """Updates an existing event."""

    try:
        event = Event.get_by_id(event_id)
    except DoesNotExist:
        console.print(format_text('bold', 'red', f"❌ Événement {event_id} non trouvé."))
        raise typer.Exit()

    updates = {}
    
    if contract_id:
        updates["contract_id"] = contract_id
    if event_name:
        updates["name"] = event_name
    if event_date:
        updates["event_date"] = datetime.strptime(event_date, "%Y-%m-%d")
    if place:
        updates["location"] = place
    if attendees:
        updates["attendees"] = attendees
    if notes:
        updates["notes"] = notes
    if contact_id:
        updates["team_contact_id"] = contact_id

    try:
        if updates:
            for field, value in updates.items():
                setattr(event, field, value)
            event.save()
            console.print(format_text('bold', 'green', f"✅ Événement {event_id} mis à jour avec succès !"))
        else:
            console.print(format_text('bold', 'yellow', "⚠ Aucun champ à mettre à jour."))
            raise typer.Exit()

    except ValueError as e:
        console.print(format_text('bold', 'red', f"❌ {str(e)}"))
        raise typer.Exit(1)

@app.command("delete")
def delete_event(
    event_id: int = typer.Argument(..., help="N° de l'événement à supprimer")
):
    """Deletes an existing event."""

    try:
        event = Event.get_by_id(event_id)
    except DoesNotExist:
        console.print(format_text('bold', 'red', f"❌ Événement {event_id} non trouvé."))
        raise typer.Exit()

    confirm = Confirm.ask(
        format_text('bold', 'yellow', f"⚠ Êtes-vous sûr de vouloir supprimer {event.name} ({event_id}) ?")
    )

    if confirm:
        event.delete_instance()
        console.print(format_text('bold', 'green', f"✅ Événement {event.name} ({event_id}) supprimé avec succès."))
    else:
        console.print(format_text('bold', 'red', "❌ Opération annulée."))
        raise typer.Exit()
    