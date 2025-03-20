from datetime import datetime
from peewee import (
    CharField,
    TextField,
    IntegerField,
    DateTimeField,
    ForeignKeyField,
    DoesNotExist
)
from epicevents.models.database import BaseModel
from epicevents.models.contract import Contract
from epicevents.models.user import User


class Event(BaseModel):
    """Represents an event in the CRM system."""

    contract = ForeignKeyField(Contract, backref="events")
    name = CharField(max_length=150)
    location = CharField(max_length=150)
    event_date = DateTimeField()
    attendees = IntegerField()
    notes = TextField(null=True)
    team_contact_id = ForeignKeyField(
        User,
        backref="assigned_events",
        on_delete="SET NULL",
        null=True
    )
    date_created = DateTimeField(null=True)  # Allow null for new objects
    date_updated = DateTimeField(null=True)  # Allow null for new objects

    def save(self, *args, **kwargs):
        """Saves the event's data with validation checks."""
        self._validate_contract()
        self._validate_name()
        self._validate_event_date()
        self._validate_attendees()
        self._validate_team_contact()
        if not self.id:
            self.date_created = datetime.now()  # Auto date_created
        self.date_updated = datetime.now()  # Auto date_updated
        super().save(*args, **kwargs)

    def _validate_contract(self):
        """Validates contract."""
        if not self.contract or not Contract.get_or_none(Contract.id == self.contract.id):
            raise ValueError("❌ Erreur : Vous devez assigner un contrat existant.")

    def _validate_name(self):
        """Validates the event name."""
        if not self.name:
            raise ValueError("❌ Erreur : Le nom de l'événement ne peut pas être vide.")

    def _validate_event_date(self):
        """Validates the event date."""
        if not isinstance(self.event_date, datetime):
            # Normalising date
            self.event_date = self.event_date.strip()
            self.event_date = self.event_date.replace('_', ' ')

            # If the length is 10, it means the time part is missing, so add a default time
            if len(self.event_date) == 10:
                self.event_date += " 12:00"
            try:
                event_dt = datetime.strptime(self.event_date, "%Y-%m-%d %H:%M")
                self.event_date = event_dt  # datetime convertion
            except ValueError:
                raise ValueError("❌ Erreur : Format de date invalide. Utilisez 'YYYY-MM-DD' ou 'YYYY-MM-DD_HH:MM'.")

        # Check if date is updated
        if self.id:
            try:
                original_event = Event.get(Event.id == self.id)
                if original_event.event_date == self.event_date:
                    return self.event_date
            except Event.DoesNotExist:
                pass  # Goto normal check (not in the past)

        # Check if the date is in the past
        if self.event_date < datetime.now():
            raise ValueError("❌ Erreur : La date de l'événement ne peut pas être dans le passé.")

        return self.event_date

    def _validate_attendees(self):
        """Validates the number of attendees."""
        if self.attendees <= 0:
            raise ValueError("❌ Erreur : Le nombre d'invités doit être un nombre entier positif.")

    def _validate_team_contact(self):
        """Validates that team contact has a Support role."""
        try:
            if self.team_contact_id and self.team_contact_id.role.name.lower() != "support":
                raise ValueError("❌ Erreur : Vous devez assigner un utilisateur ayant le rôle de 'Support'.")
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
