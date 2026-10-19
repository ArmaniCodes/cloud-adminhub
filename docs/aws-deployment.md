# Cloud AdminHub — Deployment History and Teardown

## Current status

**The AWS demonstration environment was intentionally destroyed on 2026-10-19 to avoid ongoing charges.** No Cloud AdminHub API is currently hosted in AWS.

The application was deployed briefly and validated at the infrastructure and database-connectivity level. This document records what was built, what was verified, and what was removed. It is a historical deployment record, not a claim that the endpoint or AWS resources are still active.

## Architecture that was deployed

The short-lived development deployment used:

- **Amazon VPC:** Public and private subnets across two Availability Zones.
- **Application Load Balancer:** Public HTTP entry point. HTTPS was not configured, so the endpoint was not safe for submitting real credentials or tokens.
- **Amazon ECS on AWS Fargate:** Containerized FastAPI service, plus one-off bootstrap and migration tasks.
- **Amazon ECR:** Private image repository with immutable image tags, scan-on-push, and a lifecycle policy.
- **Amazon RDS for PostgreSQL:** Encrypted database in private subnets.
- **AWS Secrets Manager:** Database credentials and API signing key.
- **Amazon CloudWatch Logs:** Container and task logs.
- **AWS IAM:** Separate task and execution permissions; dedicated PostgreSQL application and migration roles.
- **Terraform:** Infrastructure definitions and state management.

The database schema was managed by Alembic. The application used the `cloud_adminhub_app` database role, while a separate migrator role performed schema migrations.

## What was verified during deployment

The October 2026 deployment achieved the following:

- The API health route and Swagger/OpenAPI page responded successfully through the load balancer.
- A one-off ECS diagnostic task exited with code `0` and connected to the `cloud_adminhub` database as `cloud_adminhub_app`.
- The database contained `alembic_version`, `users`, `refresh_tokens`, and `audit_logs`.
- The RDS database was at Alembic revision `7fd04a2937e7` (head).
- The bootstrap and migration tasks completed successfully.

**Limit of the validation:** the deployment was short-lived, used HTTP rather than HTTPS, and did not complete full authenticated end-to-end testing through the public endpoint. This project should not be described as a production-hardened or continuously available service.

## Teardown completed

The main Terraform destroy completed with **61 resources destroyed**. The separate state-bucket stack was then destroyed with **4 resources destroyed**. The S3 state bucket `cloud-adminhub-tfstate-364503394646-us-east-1` was removed after migrating Terraform state to local state.

After teardown, AWS CLI checks in `us-east-1` returned no matching Cloud AdminHub entries for:

- RDS database instances and matching manual snapshots
- Matching automated RDS backups
- Load balancers and ECS clusters
- VPC endpoints and available/pending NAT gateways
- ECR repositories and Cloud AdminHub Secrets Manager secrets
- Cloud AdminHub CloudWatch log groups

Additional checks found no Terraform state bucket with the matching name, no Elastic IP addresses, and no unattached EBS volumes in that region. These were point-in-time checks for common leftovers, **not a guarantee that the entire AWS account has zero charges**.

Review [AWS Billing](https://console.aws.amazon.com/billing/home), Bills, and Cost Explorer after the billing data updates. Charges incurred before deletion may still be payable, and budget notifications are not hard spending limits.

## Terraform state and future redeployment

Both Terraform configurations have been migrated away from the deleted S3 backend to local state configuration. State files are intentionally not committed to Git. A local state backup was kept outside the repository at:

`~/cloud-adminhub-state-backups/`

Keep that backup directory private and do not upload or commit its contents. The local backup records resource state from teardown and should not be treated as deployable infrastructure in another account.

The Terraform files still describe the infrastructure. On a fresh clone, there is no Terraform state file, so a normal plan can propose creating AWS resources again. **Do not run `terraform apply` unless you are deliberately redeploying and have reviewed the full plan and expected costs.**

If redeploying later:

1. Recheck the account, AWS profile, region, and current costs.
2. Review the Terraform code and decide how to provision and secure Terraform state for the new deployment.
3. Review the plan carefully; RDS, load balancers, running Fargate tasks, interface endpoints, storage, and logging may incur charges.
4. Configure HTTPS before transmitting real credentials or tokens.
5. Test login, refresh-token rotation/reuse handling, logout, role restrictions, user CRUD, password changes, and audit logging in a non-production environment.
6. Tear down resources when finished and verify the resources and bill again.

RDS deletion protection and final-snapshot behavior are intentionally kept as safeguards in the reusable Terraform configuration; teardown previously required temporary explicit changes. An ECR repository may also need to be emptied or its deletion behavior deliberately configured before destroy can complete.

## Local development

Use the local Docker Compose workflow in the [README](../README.md). It creates local containers only; it does not require deploying AWS resources. Apply database migrations with Alembic rather than creating database tables directly from ORM metadata.

## Security notes

- Do not send login credentials or access/refresh tokens over the former public HTTP endpoint.
- Never commit `.env` files, AWS credentials, secret JSON, Terraform state, or Terraform plan files.
- Use HTTPS for any future public deployment.
- The AWS demo validates deployment and database connectivity, but full authenticated integration tests remain a separate verification task.
