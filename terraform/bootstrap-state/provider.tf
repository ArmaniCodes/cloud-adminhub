provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project   = "CloudAdminHub"
      ManagedBy = "Terraform"
      Purpose   = "TerraformState"
    }
  }
}