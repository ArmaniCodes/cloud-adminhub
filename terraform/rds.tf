# Database subnet group: keeps RDS in the private subnets
resource "aws_db_subnet_group" "main" {
  name        = "cloud-adminhub-db-subnet-group"
  description = "Private subnets for Cloud AdminHub PostgreSQL"

  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "cloud-adminhub-db-subnet-group"
  }
}

# PostgreSQL database for Cloud AdminHub
resource "aws_db_instance" "postgres" {
  identifier = "cloud-adminhub-postgres"

  engine         = "postgres"
  engine_version = "16.15"
  instance_class = "db.t4g.micro"

  db_name  = "cloud_adminhub"
  username = "cloudadminhub_admin"

  # AWS generates and manages the master password in Secrets Manager.
  manage_master_user_password = true

  # Storage
  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  # Network
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false
  port                   = 5432
  multi_az               = false

  # Backups and protection
  backup_retention_period    = 1
  auto_minor_version_upgrade = true
  deletion_protection        = true
  skip_final_snapshot        = false
  final_snapshot_identifier  = "cloud-adminhub-postgres-final-snapshot"
  copy_tags_to_snapshot      = true

  tags = {
    Name = "cloud-adminhub-postgres"
  }
}