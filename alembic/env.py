
import json
import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import URL, engine_from_config, pool

from app.models.base import Base
from app.models.user import User
from app.models.audit import AuditLog
from app.models.refresh_token import RefreshToken


# Alembic Config object
config = context.config

load_dotenv()

# Local development uses DATABASE_URL.
database_url = os.getenv("DATABASE_URL")

# AWS ECS uses credentials injected from Secrets Manager.
if not database_url:
    secret_json = os.getenv("MIGRATION_DB_SECRET_JSON")
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")

    if not all((secret_json, db_host, db_name)):
        raise ValueError(
            "Set DATABASE_URL or provide MIGRATION_DB_SECRET_JSON, "
            "DB_HOST, and DB_NAME."
        )

    try:
        credentials = json.loads(secret_json)
    except json.JSONDecodeError:
        raise ValueError(
            "MIGRATION_DB_SECRET_JSON must contain valid JSON."
        ) from None

    if (
        not isinstance(credentials, dict)
        or not credentials.get("username")
        or not credentials.get("password")
    ):
        raise ValueError(
            "Migration credentials must contain username and password."
        )

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=credentials["username"],
        password=credentials["password"],
        host=db_host,
        port=int(os.getenv("DB_PORT", "5432")),
        database=db_name,
        query={"sslmode": "require"},
    ).render_as_string(hide_password=False)

# Escape percent signs for Alembic's ConfigParser.
# This preserves percent-encoded characters in database URLs.
config.set_main_option(
    "sqlalchemy.url",
    database_url.replace("%", "%%"),
)

# Configure logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Register model metadata for Alembic autogeneration.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            autogenerate_plugins=[
                "alembic.autogenerate.*",
                "alembic.ext.checkconstraint_byname",
            ],
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
