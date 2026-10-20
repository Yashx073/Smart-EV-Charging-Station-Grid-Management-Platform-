from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Smart EV Charging Station Management"
    app_env: str = "development"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    mongodb_uri: str = "mongodb://root:changeme@localhost:27017/smart_ev_charging?authSource=admin"
    mongodb_db: str = "smart_ev_charging"

    secret_key: str = "dev-insecure-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    cookie_secure: bool = False
    cookie_same_site: str = "lax"

    seed_admin_email: str = "admin@evcharging.local"
    seed_admin_password: str = "AdminPass123!"
    seed_admin_full_name: str = "System Administrator"


settings = Settings()
