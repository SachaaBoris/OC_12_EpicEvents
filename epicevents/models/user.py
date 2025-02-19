import re
from datetime import datetime, timedelta, timezone
from peewee import *
from argon2 import PasswordHasher
from .database import BaseModel
from .role import Role


ph = PasswordHasher()

class User(BaseModel):
    """Represents a user in the CRM system."""
    username = CharField(max_length=25, unique=True)
    password = CharField(max_length=255)
    email = CharField(max_length=50, unique=True)
    first_name = CharField(max_length=25)
    last_name = CharField(max_length=25)
    phone = CharField(max_length=25)
    role = ForeignKeyField(Role, backref="list_users", on_delete="SET NULL")

    def save(self, *args, **kwargs):
        """Saves the user's data with validation checks."""
        self._validate_name()
        self._validate_email()
        self._validate_phone()
        self._validate_role()

        # Hashing password if not already hashed
        if not self.password.startswith("$argon2id$"):
            self.password = ph.hash(self.password)

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
        """Validates phone number."""
        pattern = r"^\+?[0-9]{7,15}$"
        if not re.match(pattern, self.phone):
            raise ValueError("Erreur : Veuillez entrer un numéro de téléphone valide.")

    def _validate_role(self):
        """Validates user role."""
        if not self.role:
            raise ValueError("Erreur : L'utilisateur doit avoir un rôle assigné.")

        if self.role.name.lower() not in ["admin", "management", "sales", "support"]:
            raise ValueError("Erreur : Le rôle doit être 'admin' (1), 'management' (2), 'sales' (3) ou 'support' (4).")

    def verify_password(self, password: str) -> bool:
        """Checks input password equals saved."""
        try:
            return ph.verify(self.password, password)
        except exceptions.VerifyMismatchError:
            return False

    def get_data(self):
        """Returns a dictionnary with user's information."""
        user_data = {
            "user_id": self.id,
            "email": self.email,
            "role_id": self.role.id if self.role else None,
            "jwt_exp": datetime.now(tz=timezone.utc) + timedelta(hours=1),
        }

        return user_data
