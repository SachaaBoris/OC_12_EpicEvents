import re
from datetime import datetime, timedelta, timezone
from peewee import *
from .database import BaseModel
from .contract import Contract
from .user import User


class Event(BaseModel):
    """Represents an event in the CRM system."""

    contract = ForeignKeyField(Contract, backref="events")
    name = CharField(max_length=150)
    location = CharField(max_length=150)
    event_date = DateTimeField()
    attendees = IntegerField()
    date_created = DateTimeField(default=datetime.now)
    date_updated = DateTimeField(default=datetime.now)
    notes = TextField(null=True)
    team_contact = ForeignKeyField(
        User,
        backref="assigned_events",
        on_delete="SET NULL",
        null=True
    )

    def save(self, *args, **kwargs):
        """Saves the event's information with validation checks."""
        self._validate_name()
        self._validate_event_date()
        self._validate_attendees()
        self.date_updated = datetime.now()  # Mise à jour automatique de la date
        super().save(*args, **kwargs)

    def _validate_name(self):
        """Validates the event name."""
        if not self.name:
            raise ValueError("Erreur : Le nom de l'événement ne peut pas être vide.")

    def _validate_event_date(self):
        """Validates the event date."""
        if self.event_date < datetime.now():
            raise ValueError("Erreur : La date de l'événement ne peut pas être dans le passé.")

    def _validate_attendees(self):
        """Validates the number of attendees."""
        if self.attendees <= 0:
            raise ValueError("Erreur : Le nombre d'invités doit être un nombre entier positif.")

    def _validate_date(self):
        """Validates the date."""
        if isinstance(self.date_created, datetime):
            return  # Si la date est déjà un objet datetime valide, on passe
        else:
            raise ValueError("Erreur : La date de création doit être au format datetime valide.")

    def get_data(self):
        """Returns a dictionary with the event's information."""
        return {
            "event_id": self.id,
            "contract": self.contract.get_data() if self.contract else None,
            "name": self.name,
            "location": self.location,
            "event_date": self.event_date,
            "attendees": self.attendees,
            "notes": self.notes,
            "date_created": self.date_created,
            "date_updated": self.date_updated,
            "team_contact": self.team_contact.get_data() if self.team_contact else None
        }
