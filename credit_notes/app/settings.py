import urllib.parse
from pydantic import BaseSettings
from .local_settings import settings


class Settings(BaseSettings):
    app_name: str = "EP-credit-notes"
    app_description: str = ""
    app_version: str = "v0.0.1"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_root_path="/dev/"
    debug: bool = True
    # Sentry
    sentry_dsn: str = "https://76b647949c0e4db5a8a6c1ad7a809ed6@o1162014.ingest.sentry.io/6248725"
    # Unleashed
    unleashed_api_key = "wxkI3HUObJvZGwvuqD2Q0bfa8cTL0hOZ8cSsEJqvvEVgANtAxKRRKAdDCvA6wiZbJVf1IAY4LmhrHB3VsTNw=="
    unleashed_api_id = "e82aef74-5d53-4ff1-9fa7-ec3ed7b3a4e6"
    unleashed_url = "https://api.unleashedsoftware.com/"
    # Database
    db_user = 'middleware_user'
    db_password = 'DoK@#laV236!an'
    parsed_db_password = urllib.parse.quote(db_password)
    db_host = 'sunculture-production.cigs2xzvtic5.eu-central-1.rds.amazonaws.com'
    db_port = 3306
    db_name = 'sunculture_main'
    database_url = f"mysql+pymysql://{db_user}:{parsed_db_password}@{db_host}:{db_port}/{db_name}"

settings = Settings()