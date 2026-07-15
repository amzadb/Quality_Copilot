"""Normalize database URLs from hosted platforms (e.g. Render)."""


def normalize_database_url(url: str) -> str:
    """Convert common Postgres URL schemes to SQLAlchemy + psycopg form."""
    value = (url or "").strip()
    if value.startswith("postgres://"):
        return "postgresql+psycopg://" + value[len("postgres://") :]
    if value.startswith("postgresql://") and "+psycopg" not in value.split("://", 1)[0]:
        return "postgresql+psycopg://" + value[len("postgresql://") :]
    return value
