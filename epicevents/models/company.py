import re
from peewee import *
from .database import BaseModel


class Company(BaseModel):
    """Represents a company in the CRM system."""

    name = CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        """Saves the company's information with validation checks."""
        self._validate_name()
        super().save(*args, **kwargs)

    def _validate_name(self):
        """ Validates the name. """
        pattern = r"^[a-zA-ZÀ-ÿ0-9\s\.\,\-\_\&]+$"
        
        if not re.match(pattern, self.name):
            raise ValueError(
                "Erreur : Un caractère n'est pas pris en charge."
            )
