output "aws_account_id" {
  description = "AWS account ID used by Terraform"
  value       = data.aws_caller_identity.current.account_id
}

output "vpc_id" {
  description = "ID of the Cloud AdminHub VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "availability_zones" {
  description = "Availability Zones used by Cloud AdminHub"
  value       = aws_subnet.public[*].availability_zone
}

output "alb_security_group_id" {
  description = "Security group ID for the Application Load Balancer"
  value       = aws_security_group.alb.id
}

output "app_security_group_id" {
  description = "Security group ID for FastAPI ECS tasks"
  value       = aws_security_group.app.id
}

output "db_security_group_id" {
  description = "Security group ID for RDS PostgreSQL"
  value       = aws_security_group.db.id
}

output "endpoints_security_group_id" {
  description = "Security group ID for private AWS service endpoints"
  value       = aws_security_group.endpoints.id
}

output "ecr_repository_url" {
  description = "URL used to tag and push Docker images to ECR"
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_repository_arn" {
  description = "ARN of the Cloud AdminHub ECR repository"
  value       = aws_ecr_repository.api.arn
}

output "rds_endpoint" {
  description = "Private DNS endpoint for Cloud AdminHub PostgreSQL"
  value       = aws_db_instance.postgres.address
}

output "rds_port" {
  description = "PostgreSQL connection port"
  value       = aws_db_instance.postgres.port
}

output "rds_database_name" {
  description = "Cloud AdminHub database name"
  value       = aws_db_instance.postgres.db_name
}

output "rds_master_secret_arn" {
  description = "ARN of the RDS-managed master password secret"
  value       = aws_db_instance.postgres.master_user_secret[0].secret_arn
}

output "ecs_cluster_name" {
  description = "Name of the Cloud AdminHub ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the Cloud AdminHub ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "ecs_task_execution_role_arn" {
  description = "IAM role used by ECS to pull images and send logs"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "ecs_task_role_arn" {
  description = "IAM role assigned to the application container"
  value       = aws_iam_role.ecs_task.arn
}

output "ecs_log_group_name" {
  description = "CloudWatch log group for the API"
  value       = aws_cloudwatch_log_group.api.name
}

output "app_db_secret_arn" {
  description = "ARN of the runtime PostgreSQL credentials secret"
  value       = aws_secretsmanager_secret.app_db_credentials.arn
}

output "migration_db_secret_arn" {
  description = "ARN of the database migration credentials secret"
  value       = aws_secretsmanager_secret.migration_db_credentials.arn
}


output "bootstrap_task_definition_arn" {
  description = "Task definition ARN for the one-off database bootstrap task"
  value       = aws_ecs_task_definition.bootstrap.arn
}

output "bootstrap_log_group_name" {
  description = "CloudWatch log group for database bootstrap execution"
  value       = aws_cloudwatch_log_group.bootstrap.name
}

output "migration_task_definition_arn" {
  description = "Task definition ARN for the one-off Alembic migration task"
  value       = aws_ecs_task_definition.migration.arn
}

output "migration_log_group_name" {
  description = "CloudWatch log group for database migration execution"
  value       = aws_cloudwatch_log_group.migration.name
}

output "api_service_name" {
  description = "ECS service name for Cloud AdminHub"
  value       = aws_ecs_service.api.name
}

output "api_task_definition_arn" {
  description = "Task definition ARN for the FastAPI application"
  value       = aws_ecs_task_definition.api.arn
}

output "alb_dns_name" {
  description = "Public DNS name of the Application Load Balancer"
  value       = aws_lb.api.dns_name
}

output "api_base_url" {
  description = "Temporary HTTP URL for initial health checks"
  value       = "http://${aws_lb.api.dns_name}"
}