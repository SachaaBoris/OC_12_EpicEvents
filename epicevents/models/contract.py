from datetime import datetime
from peewee import (
    BooleanField,
    FloatField,
    DateTimeField,
    ForeignKeyField,
    DoesNotExist,
    IntegrityError
)
from epicevents.models.database import BaseModel
from epicevents.models.customer import Customer
from epicevents.models.user import User


class Contract(BaseModel):
    """Represents a contract in the CRM system."""

    customer = ForeignKeyField(
        Customer,
        backref="customer_contracts",
        on_delete="SET NULL",
        null=True
    )
    signed = BooleanField(default=False)
    date_created = DateTimeField(default=datetime.now)
    date_updated = DateTimeField(default=datetime.now)
    amount_total = FloatField()
    amount_due = FloatField(null=True)
    team_contact_id = ForeignKeyField(
        User,
        backref="assigned_contracts",
        on_delete="SET NULL",
        null=True
    )

    def save(self, *args, **kwargs):
        """Saves the contract's data with validation checks."""
        self._validate_signed()
        self._validate_amounts()
        self._validate_date()
        self._validate_team_contact()
        self.date_updated = datetime.now()
        super().save(*args, **kwargs)

    def _validate_signed(self):
        if not self.signed:
            raise IntegrityError("❌ Erreur : Le Contrat doit être signé avant d'être sauvegardé.")

    def _validate_amounts(self):
        """Validates the total amount and amount due."""
        if self.amount_total < 0:
            raise ValueError("❌ Erreur : Le montant total ne peut pas être inférieur à zéro.")
        if self.amount_due and self.amount_due > self.amount_total:
            raise ValueError("❌ Erreur : Le montant dû ne peut pas être supérieur au montant total.")

    def _validate_date(self):
        """Validates the date."""
        if isinstance(self.date_created, datetime):
            return
        else:
            raise ValueError("❌ Erreur : La date de création doit être au format datetime valide.")

    def _validate_team_contact(self):
        """Validates that team contact has a Management role."""
        try:
            if self.team_contact_id and self.team_contact_id.role.name.lower() != "management":
                raise ValueError("❌ Erreur : Vous devez assigner un utilisateur ayant le rôle de 'Gestionnaire'.")
        except DoesNotExist:
            self.team_contact_id = None

    def get_data(self):
        """Returns a dictionary with the contract's information."""
        return {
            "contract_id": self.id,
            "customer": self.customer.get_data() if self.customer else None,
            "signed": self.signed,
            "date_created": self.date_created,
            "date_updated": self.date_updated,
            "amount_total": self.amount_total,
            "amount_due": self.amount_due if self.amount_due else 0.0,
            "team_contact_id": self.team_contact_id.get_data() if self.team_contact_id else None
        }
