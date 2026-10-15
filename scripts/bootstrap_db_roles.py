import json
import os
import sys

from sqlalchemy import URL, create_engine, text


APP_ROLE = "cloud_adminhub_app"
MIGRATION_ROLE = "cloud_adminhub_migrator"


def read_secret_env(variable_name: str) -> dict:
    """Parse a JSON secret injected into this one-off ECS task."""
    value = os.getenv(variable_name)
    if not value:
        raise RuntimeError(
            f"Required secret environment variable {variable_name} is missing"
        )

    try:
        secret = json.loads(value)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"{variable_name} does not contain valid JSON"
        ) from None

    if not isinstance(secret, dict):
        raise RuntimeError(f"{variable_name} must contain a JSON object")

    if not secret.get("username") or not secret.get("password"):
        raise RuntimeError(
            f"{variable_name} must contain username and password fields"
        )

    return secret


def execute_formatted(connection, statement_format: str, *args) -> None:
    """Safely quote PostgreSQL identifiers and literals with format()."""
    placeholders = [f":p{i}" for i in range(len(args))]
    statement = text(
        "SELECT format(:fmt, " + ", ".join(placeholders) + ")"
    )

    parameters = {
        "fmt": statement_format,
        **{f"p{i}": arg for i, arg in enumerate(args)},
    }

    sql = connection.execute(statement, parameters).scalar_one()
    connection.exec_driver_sql(sql)


def synchronize_login_role(connection, role_name: str, password: str) -> None:
    """Create or update a restricted login role without granting admin rights."""
    exists = connection.execute(
        text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :role)"),
        {"role": role_name},
    ).scalar_one()

    action = "ALTER ROLE" if exists else "CREATE ROLE"

    try:
        execute_formatted(
            connection,
            (
                f"{action} %I WITH LOGIN PASSWORD %L "
                "NOSUPERUSER NOCREATEDB NOCREATEROLE "
                "NOREPLICATION NOBYPASSRLS"
            ),
            role_name,
            password,
        )
    except Exception as exc:
        original_error = getattr(exc, "orig", None)
        error_type = type(original_error or exc).__name__
        sqlstate = getattr(original_error, "sqlstate", None)

        raise RuntimeError(
            f"Could not create or update database role {role_name} "
            f"(error type: {error_type}, "
            f"SQLSTATE: {sqlstate or 'unknown'})"
        )from None


def build_engine(username: str, password: str):
    required = ("DB_HOST", "DB_NAME")
    missing = [name for name in required if not os.getenv(name)]

    if missing:
        raise RuntimeError(
            "Missing required database settings: " + ", ".join(missing)
        )

    url = URL.create(
        drivername="postgresql+psycopg",
        username=username,
        password=password,
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.environ["DB_NAME"],
        query={"sslmode": "require"},
    )

    return create_engine(
        url,
        pool_pre_ping=True,
        hide_parameters=True,
    )


def main() -> None:
    master = read_secret_env("RDS_MASTER_SECRET_JSON")
    app = read_secret_env("APP_DB_SECRET_JSON")
    migrator = read_secret_env("MIGRATION_DB_SECRET_JSON")

    database_name = os.environ["DB_NAME"]

    # Use the RDS-managed master credentials only for initial provisioning.
    admin_engine = build_engine(master["username"], master["password"])

    try:
        with admin_engine.begin() as connection:
            synchronize_login_role(
                connection, APP_ROLE, app["password"]
            )
            synchronize_login_role(
                connection, MIGRATION_ROLE, migrator["password"]
            )

            execute_formatted(
                connection,
                "GRANT CONNECT ON DATABASE %I TO %I",
                database_name,
                APP_ROLE,
            )
            execute_formatted(
                connection,
                "GRANT CONNECT ON DATABASE %I TO %I",
                database_name,
                MIGRATION_ROLE,
            )

            execute_formatted(
                connection,
                "GRANT USAGE ON SCHEMA public TO %I",
                APP_ROLE,
            )
            execute_formatted(
                connection,
                "REVOKE CREATE ON SCHEMA public FROM %I",
                APP_ROLE,
            )
            execute_formatted(
                connection,
                "GRANT USAGE, CREATE ON SCHEMA public TO %I",
                MIGRATION_ROLE,
            )

            execute_formatted(
                connection,
                (
                    "GRANT SELECT, INSERT, UPDATE, DELETE "
                    "ON ALL TABLES IN SCHEMA public TO %I"
                ),
                APP_ROLE,
            )
            execute_formatted(
                connection,
                (
                    "GRANT USAGE, SELECT, UPDATE "
                    "ON ALL SEQUENCES IN SCHEMA public TO %I"
                ),
                APP_ROLE,
            )

        # Default privileges must be established as the migration role.
        migration_engine = build_engine(
            migrator["username"], migrator["password"]
        )

        try:
            with migration_engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                        "GRANT SELECT, INSERT, UPDATE, DELETE "
                        "ON TABLES TO cloud_adminhub_app"
                    )
                )
                connection.execute(
                    text(
                        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                        "GRANT USAGE, SELECT, UPDATE "
                        "ON SEQUENCES TO cloud_adminhub_app"
                    )
                )
        finally:
            migration_engine.dispose()

    finally:
        admin_engine.dispose()

    print("Database roles and permissions configured successfully.")

if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        # RuntimeError messages in this script are deliberately sanitized.
        print(
            f"Database bootstrap failed: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:
        # Do not expose passwords, connection strings, or SQL statements.
        print(
            f"Database bootstrap failed: {type(exc).__name__}. "
            "Check the task configuration and database connectivity.",
            file=sys.stderr,
        )
        sys.exit(1)