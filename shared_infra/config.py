"""Shared configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM APIs
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    local_llm_endpoint: str = "http://localhost:11434/api/generate"

    # Internal systems
    erp_system_endpoint: str = ""
    erp_api_key: str = ""
    mes_system_endpoint: str = ""
    mes_api_key: str = ""
    crm_system_endpoint: str = ""
    crm_api_key: str = ""
    internal_saas_api_key: str = ""

    # External product systems
    product_db_endpoint: str = ""
    user_analytics_api_key: str = ""
    cs_ticket_system_api: str = ""
    payment_gateway_api: str = ""

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "axeworks"
    postgres_user: str = "axeworks"
    postgres_password: str = "axeworks_dev_password"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Vector DB
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # Service ports
    axengine_port: int = 8001
    axe_poe_port: int = 8002
    policy_engine_port: int = 8003
    poqat_port: int = 8004
    data_foundation_port: int = 8005
    cockpit_port: int = 3000

    # Security
    jwt_secret: str = "change-me-in-production"
    api_key_salt: str = "change-me-in-production"

    # Human-in-the-Loop
    confidence_threshold: float = 0.80

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
