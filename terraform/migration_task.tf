
# Dedicated execution role for the Alembic migration task.
resource "aws_iam_role" "ecs_migration_execution" {
  name               = "cloud-adminhub-migration-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json

  tags = {
    Name = "cloud-adminhub-migration-execution"
  }
}

# Standard ECS image-pull and CloudWatch logging permissions.
resource "aws_iam_role_policy_attachment" "ecs_migration_execution" {
  role       = aws_iam_role.ecs_migration_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# The migration task can retrieve only the migration credentials secret.
resource "aws_iam_role_policy" "ecs_migration_secret" {
  name = "cloud-adminhub-migration-secret"
  role = aws_iam_role.ecs_migration_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = aws_secretsmanager_secret.migration_db_credentials.arn
      }
    ]
  })
}

# Application code running inside the migration task needs no AWS API permissions.
resource "aws_iam_role" "ecs_migration_task" {
  name               = "cloud-adminhub-migration-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json

  tags = {
    Name = "cloud-adminhub-migration-task"
  }
}

# Keep migration logs separate from API and bootstrap logs.
resource "aws_cloudwatch_log_group" "migration" {
  name              = "/ecs/cloud-adminhub-db-migration"
  retention_in_days = 7

  tags = {
    Name = "cloud-adminhub-db-migration"
  }
}

# One-off task definition for applying database schema migrations.
resource "aws_ecs_task_definition" "migration" {
  family                   = "cloud-adminhub-db-migration"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"

  execution_role_arn = aws_iam_role.ecs_migration_execution.arn
  task_role_arn      = aws_iam_role.ecs_migration_task.arn

  container_definitions = jsonencode([
    {
      name      = "db-migration"
      image     = "${aws_ecr_repository.api.repository_url}:${var.api_image_tag}"
      essential = true

      command = ["alembic", "upgrade", "head"]

      environment = [
        {
          name  = "DB_HOST"
          value = aws_db_instance.postgres.address
        },
        {
          name  = "DB_PORT"
          value = tostring(aws_db_instance.postgres.port)
        },
        {
          name  = "DB_NAME"
          value = aws_db_instance.postgres.db_name
        }
      ]

      secrets = [
        {
          name      = "MIGRATION_DB_SECRET_JSON"
          valueFrom = aws_secretsmanager_secret.migration_db_credentials.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.migration.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "migration"
        }
      }
    }
  ])

  tags = {
    Name = "cloud-adminhub-db-migration"
  }
}
