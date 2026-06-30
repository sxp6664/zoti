"""Central config. Everything tunable lives here and reads from env so the
same image runs locally and on AWS."""
import os


class Settings:
    PG_DSN: str = os.getenv(
        "PG_DSN",
        "postgresql+psycopg2://zoti:zoti@postgres:5432/zoti",
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MIN: int = int(os.getenv("JWT_EXPIRE_MIN", "120"))

    # AWS Textract (set these in your env / AWS task role)
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    OCR_PROVIDER: str = os.getenv("OCR_PROVIDER", "mock")  # mock | textract

    # Stripe (test mode keys only)
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_ENABLED: bool = bool(os.getenv("STRIPE_SECRET_KEY"))

    ROOM_CACHE_TTL: int = int(os.getenv("ROOM_CACHE_TTL", "30"))


settings = Settings()
