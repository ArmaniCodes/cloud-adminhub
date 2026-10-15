resource "aws_secretsmanager_secret" "app_db_credentials" {
  name        = "cloud-adminhub/app-db-credentials"
  description = "Runtime PostgreSQL credentials for Cloud AdminHub"

  # This is a learning project; remove the secret immediately
  # when intentionally destroying the infrastructure.
  recovery_window_in_days = 0

  tags = {
    Name = "cloud-adminhub-app-db-credentials"
  }
}


resource "aws_secretsmanager_secret" "migration_db_credentials" {
  name        = "cloud-adminhub/migration-db-credentials"
  description = "Database credentials used exclusively for Alembic migrations"

  recovery_window_in_days = 0

  tags = {
    Name = "cloud-adminhub-migration-db-credentials"
  }
}