import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

# DATABASE
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
APP_BASE_URL = os.getenv("APP_BASE_URL")

# SECRET KEY
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
PERMANENT_SESSION_LIFETIME = timedelta(
    minutes=int(os.getenv("SESSION_COOKIE_LIFETIME_MINUTES", "60"))
)

# EMAIL CONFIG
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USE_TLS = True

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER") or MAIL_USERNAME
