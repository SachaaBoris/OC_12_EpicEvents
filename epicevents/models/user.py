import re
from peewee import CharField, ForeignKeyField
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from epicevents.models.database import BaseModel
from epicevents.models.role import Role


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
        pattern = r"^[a-zA-ZÀ-ÿ\-_\s]+$"
        if not re.match(pattern, self.first_name) or not re.match(pattern, self.last_name):
            raise ValueError("❌ Erreur : Le prénom et le nom ne doivent contenir que des lettres, tirets ou espaces.")

    def _validate_email(self):
        """Validates the email address."""
        if not self.email or len(self.email) < 5:  # smallest mail in the universe
            raise ValueError("❌ Erreur : Veuillez entrer un email valide.")

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, self.email):
            raise ValueError("❌ Erreur : Veuillez entrer un email valide.")

        if ".." in self.email or self.email.count("@") != 1:
            raise ValueError("❌ Erreur : Veuillez entrer un email valide.")

    def _validate_phone(self):
        """Validates phone number."""
        pattern = r"^\+?[0-9]{7,15}$"
        if not re.match(pattern, self.phone):
            raise ValueError("❌ Erreur : Veuillez entrer un numéro de téléphone valide.")

    def _validate_role(self):
        """Validates user role."""
        if not self.role:
            raise ValueError("❌ Erreur : L'utilisateur doit avoir un rôle assigné.")

        if self.role.name.lower() not in ["admin", "management", "sales", "support"]:
            raise ValueError("❌ Erreur : Le rôle doit être 'admin' (1), 'management' (2), 'sales' (3) ou 'support' (4).")

    def verify_password(self, password: str) -> bool:
        """Checks input password equals saved."""
        try:
            return ph.verify(self.password, password)
        except VerifyMismatchError:
            return False

    def get_data(self):
        """Returns a dictionnary with user's information."""
        user_data = {
            "user_id": self.id,
            "email": self.email,
            "role_id": self.role.id if self.role else None
        }

        return user_data
