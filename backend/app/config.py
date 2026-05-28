from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://safety:safety@localhost:5432/safetydb"

    mqtt_host: str = "mqtt.devdungeons.com"
    mqtt_port: int = 8883
    mqtt_tls: bool = True
    mqtt_username: str = "backend"
    mqtt_password: str = ""

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "alerts@devdungeons.com"
    alert_recipients: str = ""  # comma-separated

    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 60 * 24

    cors_origins: str = "https://dashboard.devdungeons.com,http://localhost:3000,http://localhost:8080"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def alert_recipients_list(self) -> list[str]:
        return [r.strip() for r in self.alert_recipients.split(",") if r.strip()]


settings = Settings()
