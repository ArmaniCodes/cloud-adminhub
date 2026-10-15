
# ECS cluster: logical home for Cloud AdminHub tasks and services
resource "aws_ecs_cluster" "main" {
  name = "cloud-adminhub"

  tags = {
    Name = "cloud-adminhub"
  }
}

# Shared trust policy for ECS tasks
data "aws_iam_policy_document" "ecs_tasks_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# Execution role: used by ECS/Fargate to pull images and send logs
resource "aws_iam_role" "ecs_task_execution" {
  name               = "cloud-adminhub-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json

  tags = {
    Name = "cloud-adminhub-ecs-execution"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role = aws_iam_role.ecs_task_execution.name

  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Application role: leave without permissions until the app needs AWS APIs
resource "aws_iam_role" "ecs_task" {
  name               = "cloud-adminhub-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json

  tags = {
    Name = "cloud-adminhub-ecs-task"
  }
}

# Pre-create the log group and retain logs for seven days
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/cloud-adminhub-api"
  retention_in_days = 7

  tags = {
    Name = "cloud-adminhub-api"
  }
}
