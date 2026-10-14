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