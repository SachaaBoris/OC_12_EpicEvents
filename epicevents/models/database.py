from peewee import (
    Model,
    PostgresqlDatabase,
)
from playhouse.migrate import PostgresqlMigrator
from epicevents.config import DB_NAME, DB_USER, DB_PASSWORD


psql_db = PostgresqlDatabase(DB_NAME, user=DB_USER, password=DB_PASSWORD)
psql_migrator = PostgresqlMigrator(psql_db)


class BaseModel(Model):
    """The base model for Peewee models using PostgreSQL."""

    class Meta:
        database = psql_db
        migrator = psql_migrator
