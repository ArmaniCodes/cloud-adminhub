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