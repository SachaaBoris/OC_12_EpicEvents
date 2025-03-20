import os
from dotenv import load_dotenv


# Loading Environment to global variables, don't edit below
load_dotenv()
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
SECRET_KEY = os.getenv('SECRET_KEY')
TOKEN_EXP = int(os.getenv('TOKEN_EXP', 2))
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
CURRENCY = os.getenv('CURRENCY')
ITEMS_PER_PAGE = int(os.getenv("ITEMS_PER_PAGE", 20))
SENTRY_DSN = os.getenv('SENTRY_DSN')
SENTRY_ENV = os.getenv('SENTRY_ENV', "production")

if not SECRET_KEY:
    raise ValueError("La clé secrète JWT n'est pas définie dans les variables d'environnement")
