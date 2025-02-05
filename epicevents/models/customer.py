import re
from datetime import datetime, timedelta, timezone
from peewee import *
from .database import BaseModel
from .company import Company
from .user import User


class Customer(BaseModel):
    """Represents a customer in the CRM system."""

    first_name = CharField(max_length=25)
    last_name = CharField(max_length=25)
    email = CharField(max_length=50, unique=True)
    phone = CharField(max_length=20)
    company = ForeignKeyField(Company, backref="customers")
    date_created = DateTimeField(default=datetime.now)
    date_updated = DateTimeField(default=datetime.now)
    team_contact = ForeignKeyField(
        User,
        backref="assigned_customers",
        on_delete="SET NULL",
        null=True
    )

    def save(self, *args, **kwargs):
        """Saves the customer's information with validation checks."""
        self._validate_name()
        self._validate_email()
        self._validate_phone()
        self._validate_date()
        self.date_updated = datetime.now()
        super().save(*args, **kwargs)

    def _validate_name(self):
        """Validates the first name and last name."""
        if not self.first_name.isalpha() or not self.last_name.isalpha():
            raise ValueError("Erreur : Le prénom et le nom ne doivent contenir que des lettres.")

    def _validate_email(self):
        """Validates the email address."""
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, self.email):
            raise ValueError("Erreur : Veuillez entrer un email valide.")

    def _validate_phone(self):
        """Validates the phone number."""
        pattern = r"^\+?[0-9]{7,20}$"
        if not re.match(pattern, self.phone):
            raise ValueError("Erreur : Veuillez entrer un numéro de téléphone valide.")

    def _validate_date(self):
        """Validates date fields."""
        if isinstance(self.date_created, datetime):
            return  # Si la date est déjà un objet datetime valide, on passe
        else:
            raise ValueError("Erreur : La date de création doit être au format datetime valide.")

    def get_data(self):
        """Returns a dictionary with the customer's information."""
        return {
            "customer_id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company.name if self.company else None,
            "team_contact": self.team_contact.get_data() if self.team_contact else None,
            "date_created": self.date_created,
            "date_updated": self.date_updated,
        }
