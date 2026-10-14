resource "aws_security_group" "alb" {
  name        = "cloud-adminhub-alb-sg"
  description = "Security group for the public Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "cloud-adminhub-alb-sg"
  }
}

resource "aws_security_group" "app" {
  name        = "cloud-adminhub-app-sg"
  description = "Security group for FastAPI ECS tasks"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "cloud-adminhub-app-sg"
  }
}

resource "aws_security_group" "db" {
  name        = "cloud-adminhub-db-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "cloud-adminhub-db-sg"
  }
}

resource "aws_security_group" "endpoints" {
  name        = "cloud-adminhub-endpoints-sg"
  description = "Security group for private AWS service endpoints"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "cloud-adminhub-endpoints-sg"
  }
}

# Public HTTP traffic may reach the future load balancer.
resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id

  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 80
  to_port     = 80
  ip_protocol = "tcp"

  description = "Allow HTTP from the internet to the ALB"
}

# The ALB may send requests and health checks to FastAPI.
resource "aws_vpc_security_group_egress_rule" "alb_to_app" {
  security_group_id            = aws_security_group.alb.id
  referenced_security_group_id = aws_security_group.app.id

  from_port   = 8000
  to_port     = 8000
  ip_protocol = "tcp"

  description = "Allow ALB traffic to FastAPI"
}

# FastAPI accepts traffic only from the ALB.
resource "aws_vpc_security_group_ingress_rule" "app_from_alb" {
  security_group_id            = aws_security_group.app.id
  referenced_security_group_id = aws_security_group.alb.id

  from_port   = 8000
  to_port     = 8000
  ip_protocol = "tcp"

  description = "Allow FastAPI traffic from the ALB"
}

# FastAPI may connect to the PostgreSQL database.
resource "aws_vpc_security_group_egress_rule" "app_to_db" {
  security_group_id            = aws_security_group.app.id
  referenced_security_group_id = aws_security_group.db.id

  from_port   = 5432
  to_port     = 5432
  ip_protocol = "tcp"

  description = "Allow FastAPI to connect to PostgreSQL"
}

resource "aws_vpc_security_group_ingress_rule" "db_from_app" {
  security_group_id            = aws_security_group.db.id
  referenced_security_group_id = aws_security_group.app.id

  from_port   = 5432
  to_port     = 5432
  ip_protocol = "tcp"

  description = "Allow PostgreSQL traffic from FastAPI"
}

# FastAPI may use HTTPS to reach private AWS service endpoints.
resource "aws_vpc_security_group_egress_rule" "app_to_endpoints" {
  security_group_id            = aws_security_group.app.id
  referenced_security_group_id = aws_security_group.endpoints.id

  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"

  description = "Allow HTTPS to private AWS service endpoints"
}

resource "aws_vpc_security_group_ingress_rule" "endpoints_from_app" {
  security_group_id            = aws_security_group.endpoints.id
  referenced_security_group_id = aws_security_group.app.id

  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"

  description = "Allow HTTPS from FastAPI to private AWS service endpoints"
}