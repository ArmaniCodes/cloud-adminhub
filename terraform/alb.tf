
# Public Application Load Balancer.
resource "aws_lb" "api" {
  name               = "cloud-adminhub-alb"
  internal           = false
  load_balancer_type = "application"

  subnets         = aws_subnet.public[*].id
  security_groups = [aws_security_group.alb.id]

  # This is a temporary development deployment.
  enable_deletion_protection = false

  tags = {
    Name = "cloud-adminhub-alb"
  }
}

# Fargate tasks register by IP address.
resource "aws_lb_target_group" "api" {
  name        = "cloud-adminhub-api-tg"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  deregistration_delay = 30

  health_check {
    enabled             = true
    path                = "/health"
    protocol            = "HTTP"
    port                = "traffic-port"
    matcher             = "200"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = {
    Name = "cloud-adminhub-api-tg"
  }
}

# Temporary HTTP listener for initial deployment testing.
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.api.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  tags = {
    Name = "cloud-adminhub-http"
  }
}
