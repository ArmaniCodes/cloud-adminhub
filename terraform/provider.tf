provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "CloudAdminHub"
      Environment = "dev"
      ManagedBy   = "Terraform"
    }
  }
}