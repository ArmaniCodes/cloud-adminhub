
# Dedicated execution role for the one-off database bootstrap task.
resource "aws_iam_role" "ecs_bootstrap_execution" {
  name               = "cloud-adminhub-bootstrap-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json

  tags = {
    Name = "cloud-adminhub-bootstrap-execution"
  }
}

# Standard ECR image-pull and CloudWatch logging permissions.
resource "aws_iam_role_policy_attachment" "ecs_bootstrap_execution" {
  role = aws_iam_role.ecs_bootstrap_execution.name

  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Allow the execution role to retrieve only the three required secrets.
resource "aws_iam_role_policy" "ecs_bootstrap_secrets" {
  name = "cloud-adminhub-bootstrap-secrets"
  role = aws_iam_role.ecs_bootstrap_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_db_instance.postgres.master_user_secret[0].secret_arn,
          aws_secretsmanager_secret.app_db_credentials.arn,
          aws_secretsmanager_secret.migration_db_credentials.arn
        ]
      }
    ]
  })
}

# Separate application identity for the bootstrap container.
# It receives no additional AWS permissions.
resource "aws_iam_role" "ecs_bootstrap_task" {
  name               = "cloud-adminhub-bootstrap-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json

  tags = {
    Name = "cloud-adminhub-bootstrap-task"
  }
}

# Separate log group so bootstrap logs aren't mixed with API logs.
resource "aws_cloudwatch_log_group" "bootstrap" {
  name              = "/ecs/cloud-adminhub-db-bootstrap"
  retention_in_days = 7

  tags = {
    Name = "cloud-adminhub-db-bootstrap"
  }
}

# One-off Fargate task definition; defining it doesn't start a task.
resource "aws_ecs_task_definition" "bootstrap" {
  family                   = "cloud-adminhub-db-bootstrap"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"

  execution_role_arn = aws_iam_role.ecs_bootstrap_execution.arn
  task_role_arn      = aws_iam_role.ecs_bootstrap_task.arn

  container_definitions = jsonencode([
    {
      name      = "db-bootstrap"
      image     = "${aws_ecr_repository.api.repository_url}:${var.api_image_tag}"
      essential = true

      # Override the normal FastAPI startup command.
      command = [
        "python",
        "scripts/bootstrap_db_roles.py"
      ]

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
          name      = "RDS_MASTER_SECRET_JSON"
          valueFrom = aws_db_instance.postgres.master_user_secret[0].secret_arn
        },
        {
          name      = "APP_DB_SECRET_JSON"
          valueFrom = aws_secretsmanager_secret.app_db_credentials.arn
        },
        {
          name      = "MIGRATION_DB_SECRET_JSON"
          valueFrom = aws_secretsmanager_secret.migration_db_credentials.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.bootstrap.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "bootstrap"
        }
      }
    }
  ])

  tags = {
    Name = "cloud-adminhub-db-bootstrap"
  }
}
