from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CloudCost Intelligence API"
    environment: str = "development"
    database_url: str = "sqlite+pysqlite:///./cloudcost.db"
    demo_mode: bool = True
    allow_live_sync: bool = False
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    aws_cost_explorer_enabled: bool = False
    aws_region: str = "us-east-1"
    aws_cost_explorer_role_arn: str | None = None

    azure_cost_management_enabled: bool = False
    azure_subscription_id: str | None = None
    azure_tenant_id: str | None = None
    azure_client_id: str | None = None
    azure_client_secret: str | None = Field(default=None, repr=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CLOUDCOST_",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
