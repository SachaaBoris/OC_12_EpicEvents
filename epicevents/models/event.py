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
    team_contact_id = ForeignKeyField(
        User,
        backref="assigned_events",
        on_delete="SET NULL",
        null=True
    )

    def save(self, *args, **kwargs):
        """Saves the event's data with validation checks."""
        self._validate_name()
        self._validate_event_date()
        self._validate_attendees()
        self._validate_team_contact()
        self.date_updated = datetime.now()
        super().save(*args, **kwargs)

    def _validate_name(self):
        """Validates the event name."""
        if not self.name:
            raise ValueError("Erreur : Le nom de l'événement ne peut pas être vide.")

    def _validate_event_date(self):
        """Validates the event date."""
        if isinstance(self.event_date, datetime):
            event_dt = self.event_date
        else:
            # Normalising date
            print(f"DATE : {self.event_date}")
            self.event_date = self.event_date.strip()
            if len(self.event_date) == 10:  # Format "YYYY-MM-DD"
                self.event_date += " 12:00"  # Add default time

            try:
                event_dt = datetime.strptime(self.event_date, "%Y-%m-%d %H:%M")
            except ValueError:
                raise ValueError("Erreur : Format de date invalide. Utilisez 'YYYY-MM-DD HH:MM'.")
        
        # Passed date
        if event_dt < datetime.now():
            raise ValueError("Erreur : La date de l'événement ne peut pas être dans le passé.")

        self.event_date = event_dt

    def _validate_attendees(self):
        """Validates the number of attendees."""
        if self.attendees <= 0:
            raise ValueError("Erreur : Le nombre d'invités doit être un nombre entier positif.")

    def _validate_date(self):
        """Validates the date."""
        if isinstance(self.date_created, datetime):
            return
        else:
            raise ValueError("Erreur : La date de création doit être au format datetime valide.")

    def _validate_team_contact(self):
        """Validates that team contact has a Support role."""
        try:
            if self.team_contact_id and self.team_contact_id.role.name.lower() != "support":
                raise ValueError("Erreur : Vous devez assigner un utilisateur ayant le rôle de 'Support'.")
        except DoesNotExist:
            self.team_contact_id = None

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
            "team_contact_id": self.team_contact_id.get_data() if self.team_contact_id else None
        }
