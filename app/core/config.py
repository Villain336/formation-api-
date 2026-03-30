from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Formation API"
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    BASE_URL: str = "http://localhost:8000"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/formation_api"

    # Auth
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_KEY_HEADER: str = "X-API-Key"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Registered Agent
    REGISTERED_AGENT_ANNUAL_FEE: int = 9900  # $99.00 in cents

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
