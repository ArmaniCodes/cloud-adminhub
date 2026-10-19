data "aws_caller_identity" "current" {}

# This is a bootstrap resource only; run it when deliberately setting up a
# remote state bucket. force_destroy permits removal of all object versions
# during an intentional cleanup.
resource "aws_s3_bucket" "terraform_state" {
  bucket        = "cloud-adminhub-tfstate-${data.aws_caller_identity.current.account_id}-us-east-1"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}
