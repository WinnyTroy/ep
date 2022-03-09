from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "EP-credit-notes"
    app_description: str = ""
    app_version: str = "v0.0.1"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_root_path="/dev/"
    debug: bool = True
    sentry_dsn: str = "https://76b647949c0e4db5a8a6c1ad7a809ed6@o1162014.ingest.sentry.io/6248725"
    unleashed_api_key = "wxkI3HUObJvZGwvuqD2Q0bfa8cTL0hOZ8cSsEJqvvEVgANtAxKRRKAdDCvA6wiZbJVf1IAY4LmhrHB3VsTNw=="
    unleashed_api_id = "e82aef74-5d53-4ff1-9fa7-ec3ed7b3a4e6"
    unleashed_url = "https://api.unleashedsoftware.com/"

settings = Settings()