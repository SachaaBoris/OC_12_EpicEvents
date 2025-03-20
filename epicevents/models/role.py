import re
from peewee import CharField
from epicevents.models.database import BaseModel


class Role(BaseModel):
    """Represents a role in the CRM system (1 admin, 2 management, 3 sales, 4 support)."""
    name = CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        """Saves the company's information with validation checks."""
        self._validate_name()
        super().save(*args, **kwargs)

    def _validate_name(self):
        """ Validates the name. """
        pattern = r"^[a-zA-ZÀ-ÿ0-9\s\.\,\-\_\&]+$"

        if not self.name:
            raise ValueError("❌ Erreur : Le role ne peut pas être vide.")

        if not re.match(pattern, self.name):
            raise ValueError("❌ Erreur : Un caractère n'est pas pris en charge.")
