import os
from dotenv import load_dotenv
from peewee import *
from playhouse.migrate import PostgresqlMigrator

load_dotenv()
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

psql_db = PostgresqlDatabase(DB_NAME, user=DB_USER, password=DB_PASSWORD)
psql_migrator = PostgresqlMigrator(psql_db)


class BaseModel(Model):
    """The base model for Peewee models using PostgreSQL."""

    class Meta:
        database = psql_db
        migrator = psql_migrator
