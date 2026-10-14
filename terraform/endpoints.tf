
locals {
  interface_endpoint_services = toset([
    "ecr.api",
    "ecr.dkr",
    "logs",
    "secretsmanager",
  ])
}

# Private interface endpoints for AWS services
resource "aws_vpc_endpoint" "interface" {
  for_each = local.interface_endpoint_services

  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.${each.key}"
  vpc_endpoint_type = "Interface"

  private_dns_enabled = true
  subnet_ids          = aws_subnet.private[*].id

  security_group_ids = [
    aws_security_group.endpoints.id
  ]

  tags = {
    Name = "cloud-adminhub-${each.key}-endpoint"
  }
}

# S3 gateway endpoint for ECR image layers
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"

  route_table_ids = aws_route_table.private[*].id

  tags = {
    Name = "cloud-adminhub-s3-endpoint"
  }
}

# AWS-managed prefix list for S3 in the configured region
data "aws_prefix_list" "s3" {
  name = "com.amazonaws.${var.aws_region}.s3"
}
