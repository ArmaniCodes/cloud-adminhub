# Cloud AdminHub — AWS Deployment Guide

## 1. Project Overview

Cloud AdminHub is a FastAPI application for internal user administration, authentication, role-based access control (RBAC), session management, and audit logging.

The project is being migrated from local Docker development to AWS. Infrastructure is defined with Terraform, containers are stored in Amazon ECR, and one-off tasks run on Amazon ECS with AWS Fargate.

### Target Architecture

- **Amazon VPC:** Isolated network for application infrastructure.
- **Application Load Balancer (ALB):** Intended public entry point for HTTP/HTTPS requests to the API.
- **Amazon ECS with AWS Fargate:** Runs the containerized FastAPI application and controlled one-off tasks.
- **Amazon ECR:** Stores immutable, Git-tagged Docker images.
- **Amazon RDS for PostgreSQL:** Managed relational database in private subnets.
- **AWS Secrets Manager:** Stores the RDS-managed master password and dedicated application/migration credentials.
- **Amazon CloudWatch:** Stores container and task logs.
- **AWS IAM:** Separates ECS execution permissions from application task permissions.
- **Terraform:** Defines and manages AWS infrastructure.

**Current deployment status:** The network, private service endpoints, ECR, RDS, database roles, ECS cluster, bootstrap task, and migration task are deployed. The RDS schema has been migrated and verified at Alembic revision `7fd04a2937e7` (head). The FastAPI ECS service and Application Load Balancer are not yet deployed.

## 2. AWS Account Preparation

### Completed

- [x] Created the `iamadmin` IAM user for infrastructure setup.
- [x] Enabled MFA for the administrative IAM account.
- [x] Created an AWS monthly cost budget with notifications.
- [x] Installed AWS CLI in Ubuntu/WSL.
- [x] Installed Terraform.
- [x] Configured browser-based AWS CLI authentication using `aws login`.
- [x] Verified the AWS identity using STS.
- [x] Configured the `cloudadminhub` AWS CLI profile.
- [x] Configured `terraform-cloudadminhub` to obtain credentials through AWS CLI's `credential_process`.
- [x] Selected US East (N. Virginia), `us-east-1`, as the deployment region.

### Authentication

Terraform uses the `terraform-cloudadminhub` profile. It obtains credentials through the `cloudadminhub` AWS CLI profile.

Verify the AWS identity:

```bash
aws sts get-caller-identity --profile terraform-cloudadminhub
aws sts get-caller-identity --profile cloudadminhub
```

If the AWS CLI session expires, reauthenticate:

```bash
aws login --remote --profile cloudadminhub --region us-east-1
```

Temporary authentication sessions expire periodically. Reauthenticate before running AWS CLI or Terraform commands if you see `NoCredentials`, `No valid credential sources found`, or a `credential_process` error.

Do not store AWS credentials, access keys, secret keys, authorization codes, or session tokens in the project repository. Do not paste them into tickets or logs.

### Security and Cost Controls

- The application and one-off tasks use dedicated IAM roles; the application task role has no additional AWS permissions attached at present.
- Review `terraform plan` before applying infrastructure changes.
- Budget notifications are alerts, not hard spending limits.
- RDS and the four interface VPC endpoints are billable while provisioned; other resources can also incur charges.
- This is a portfolio project intended to be run for a short period for end-to-end testing and then taken offline. See [Cleanup Plan](#15-cleanup-plan-after-end-to-end-testing).
- Do not commit environment files, credentials, secret values, temporary files containing secret JSON, or Terraform state.

## 3. Local Development and Docker

### Completed

- [x] Created a Dockerfile for the FastAPI application.
- [x] Created a `.dockerignore` file.
- [x] Built the `cloud-adminhub:local` Docker image.
- [x] Installed Docker Desktop with WSL integration.
- [x] Created a Docker Compose environment for the API and PostgreSQL.
- [x] Created a local administrator bootstrap script.
- [x] Successfully tested login against containerized PostgreSQL.
- [x] Verified the local database's Alembic revision is `7fd04a2937e7` (head).

### Local Container Environment

The local development architecture consists of two containers:

- `api`: FastAPI application, exposed on port 8000.
- `db`: PostgreSQL database, accessible to the API through Docker Compose networking.

The API container uses the Compose service hostname `db`, not `127.0.0.1`. The host's `.env` uses `127.0.0.1` when connecting to a local database port from the host environment.

### Common Commands

Start the local environment:

```bash
docker compose --env-file .env.docker up -d
```

View container status:

```bash
docker compose --env-file .env.docker ps
```

View API logs:

```bash
docker compose --env-file .env.docker logs --tail=100 api
```

Stop the environment:

```bash
docker compose --env-file .env.docker down
```

The named PostgreSQL volume preserves database data when containers are stopped or recreated. Do not use `docker compose down -v` unless you intend to delete the local database volume.

### Local Database Migrations

Apply migrations to the local Docker database:

```bash
docker compose --env-file .env.docker run --rm api alembic upgrade head
```

Check the local current revision:

```bash
docker compose --env-file .env.docker run --rm api alembic current
```

The local Docker database was verified at `7fd04a2937e7` (head). Database migrations are executed explicitly rather than creating tables automatically when the FastAPI application starts.

## 4. Terraform Setup

### Completed

- [x] Created the main Terraform configuration directory.
- [x] Configured the AWS provider for `us-east-1`.
- [x] Declared Terraform and AWS provider version constraints.
- [x] Committed the Terraform dependency lock file.
- [x] Verified the AWS identity through Terraform.
- [x] Created a dedicated S3 bucket for Terraform state.
- [x] Enabled S3 bucket versioning and server-side encryption.
- [x] Blocked public access to the state bucket.
- [x] Migrated bootstrap Terraform state into S3.
- [x] Configured the main Terraform project to use a separate S3 state key.
- [x] Enabled S3-native state locking using `use_lockfile = true`.

### Directory Structure

The main Terraform configuration includes these resource files (alongside `versions.tf`, `provider.tf`, `variables.tf`, `main.tf`, `outputs.tf`, and `.terraform.lock.hcl`):

```text
terraform/
├── network.tf
├── security_groups.tf
├── ecr.tf
├── rds.tf
├── endpoints.tf
├── ecs.tf
├── secrets.tf
├── bootstrap_task.tf
├── migration_task.tf
└── bootstrap-state/
    ├── versions.tf
    ├── provider.tf
    ├── main.tf
    └── outputs.tf
```

The `bootstrap-state/` configuration manages the remote-state bucket. The main configuration manages application infrastructure. Terraform loads all `.tf` files in the same directory as one configuration.

### Remote State

Terraform state is stored in the S3 bucket:

`cloud-adminhub-tfstate-364503394646-us-east-1`

The bootstrap and main configurations use separate state keys:

- Bootstrap state: `bootstrap/terraform.tfstate`
- Main infrastructure state: `cloud-adminhub/terraform.tfstate`

S3 versioning supports recovery of previous state versions. S3-native locking helps prevent concurrent Terraform operations from modifying the same state at the same time. Terraform state can contain sensitive information; it must not be committed to Git or made publicly accessible.

### Terraform Workflow

Run commands from the appropriate Terraform directory, normally `terraform/` for application infrastructure.

Authenticate the Terraform profile:

```bash
export AWS_PROFILE=terraform-cloudadminhub
```

Format configuration:

```bash
terraform fmt
```

Validate configuration:

```bash
terraform validate
```

Preview changes:

```bash
terraform plan
```

Apply only after reviewing the plan:

```bash
terraform apply
```

Inspect managed resources and outputs:

```bash
terraform state list
terraform output
```

If credentials have expired, reauthenticate using `aws login --remote --profile cloudadminhub --region us-east-1`, then retry.

### Terraform Security and Version Control

Commit `.terraform.lock.hcl`, but exclude Terraform working directories and state files. The root `.gitignore` should include exclusions equivalent to:

```gitignore
.env
.env.*
!.env.example

.venv/
__pycache__/
*.py[cod]
.pytest_cache/

**/.terraform/*
*.tfstate
*.tfstate.*
*.tfplan
crash.log
crash.*.log
```

Review these exclusions against the actual repository configuration before committing. Also ensure Docker build context and Git commits exclude credentials and temporary secret files.

## 5. VPC Networking

### Status: Deployed

- Region: `us-east-1` — US East (N. Virginia)
- VPC CIDR: `10.0.0.0/16`
- VPC ID: `vpc-07e99495df3b0366b`
- Availability Zones: `us-east-1a`, `us-east-1b`

The VPC contains two public and two private subnets:

| Subnet | CIDR | Intended purpose |
|---|---|---|
| Public 1 | `10.0.1.0/24` | Application Load Balancer |
| Public 2 | `10.0.2.0/24` | Application Load Balancer |
| Private 1 | `10.0.11.0/24` | ECS tasks and RDS |
| Private 2 | `10.0.12.0/24` | ECS tasks and RDS |

### Implemented Resources

- [x] VPC with DNS support and DNS hostnames enabled.
- [x] Internet Gateway.
- [x] Two public subnets and two private subnets.
- [x] Public route table with a default route to the Internet Gateway.
- [x] Separate private route tables and associations.
- [x] Terraform outputs for the VPC, subnet IDs, Availability Zones, and security group IDs.

Public subnets do not automatically assign public IP addresses to launched instances. The private route tables do not have a default internet route, and no NAT gateway has been created. Private tasks use VPC endpoints for the AWS services listed in Section 9.

### Verification

From `terraform/`:

```bash
terraform output
terraform state list
terraform plan
```

The plan should report no changes when the deployed infrastructure matches the configuration.

## 6. Network Security Groups

### Status: Deployed

Terraform creates four security groups in the VPC to establish traffic boundaries for the future load balancer, API tasks, database, and interface endpoints.

| Security group | Resource ID | Purpose |
|---|---|---|
| ALB | `sg-0340189952a96b1c8` | Public web entry point |
| App | `sg-07505808890a04860` | FastAPI ECS tasks and one-off DB tasks |
| Database | `sg-0e1854b33caba0cba` | RDS PostgreSQL |
| Endpoints | `sg-05a44d9f9d66e1265` | Interface VPC endpoints |

### Allowed Traffic

| Source | Destination | Protocol / port | Purpose |
|---|---|---|---|
| Internet (`0.0.0.0/0`) | ALB security group | TCP 80 | HTTP entry to load balancer (HTTPS not yet configured) |
| ALB security group | App security group | TCP 8000 | Forward requests to FastAPI |
| App security group | Database security group | TCP 5432 | PostgreSQL connections |
| App security group | Endpoints security group | TCP 443 | HTTPS connections to private AWS service endpoints |
| App security group | Regional S3 managed prefix list `pl-63a5400a` | TCP 443 | ECR image layers through the S3 gateway endpoint |

The corresponding ingress rules allow traffic from the intended source security group, except for the public ALB HTTP rule. The application and database ports are not directly open to the internet. Rules are managed by standalone Terraform ingress/egress rule resources in `security_groups.tf`.

**Current limitation:** the ALB security group permits inbound HTTP on port 80; HTTPS and a custom domain have not been configured.

### Verification

```bash
terraform output
terraform state list | grep security_group
terraform plan
```

## 7. Amazon ECR Container Registry

### Status: Deployed

A private Amazon Elastic Container Registry repository is used for Cloud AdminHub images.

- Repository name: `cloud-adminhub-api`
- Region: `us-east-1`
- Repository URL: `364503394646.dkr.ecr.us-east-1.amazonaws.com/cloud-adminhub-api`
- Repository ARN: `arn:aws:ecr:us-east-1:364503394646:repository/cloud-adminhub-api`
- Terraform resources: `aws_ecr_repository.api`, `aws_ecr_lifecycle_policy.api`

### Repository Configuration

- [x] Image scanning on push enabled.
- [x] Image tag mutability set to `IMMUTABLE`.
- [x] Lifecycle policy retains the ten most recent images with tags beginning `git-`.
- [x] Lifecycle policy expires untagged images after one day.
- [x] Git-tagged images built and pushed to ECR.
- [x] Pushed image tags verified using `aws ecr describe-images`.

The current image used by the successful migration task is tagged `git-9fa439a`. The bootstrap task and prior diagnostic iterations also used earlier immutable tags. Since tags are immutable, each new code revision is published with a new Git-derived tag.

The `.dockerignore` file reduced the Docker build context from about 1.67 GB to only a few kilobytes, excluding local artifacts such as virtual environments, Git metadata, environment files, and Terraform working/state files. Keep `.dockerignore` up to date so local secrets and unrelated files are not sent to the build engine.

### Build, Authenticate, Push, and Verify

Run Docker commands from the repository root, where the `Dockerfile` is located:

```bash
export AWS_PROFILE=cloudadminhub

AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ECR_IMAGE="${ECR_REGISTRY}/cloud-adminhub-api"
IMAGE_TAG="git-$(git rev-parse --short HEAD)"

docker build -t "${ECR_IMAGE}:${IMAGE_TAG}" .

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY"

docker push "${ECR_IMAGE}:${IMAGE_TAG}"
```

Verify a pushed image:

```bash
aws ecr describe-images \
  --repository-name cloud-adminhub-api \
  --image-ids "imageTag=${IMAGE_TAG}" \
  --region "$AWS_REGION" \
  --query 'imageDetails[0].{Tags:imageTags,Digest:imageDigest,PushedAt:imagePushedAt}' \
  --output table
```

#### WSL Docker credential-store workaround

If `docker login` fails while saving credentials with an error such as `The stub received bad data`, use a temporary Docker configuration for that login/push session:

```bash
export DOCKER_CONFIG="$(mktemp -d)"
chmod 700 "$DOCKER_CONFIG"
```

After the push completes, remove the temporary configuration:

```bash
rm -rf "$DOCKER_CONFIG"
unset DOCKER_CONFIG
```

A temporary configuration can contain an encoded ECR login token. Remove it after use.

From `terraform/`, verify the repository outputs and resources:

```bash
terraform output ecr_repository_url
terraform output ecr_repository_arn
terraform state list | grep ecr
terraform plan
```

## 8. Amazon RDS for PostgreSQL

### Status: Deployed; schema migrated and verified

Terraform provisions PostgreSQL in private subnets. The DB subnet group contains both private subnets in separate Availability Zones; the database instance itself is single-AZ for this development environment.

| Setting | Value |
|---|---|
| DB instance identifier | `cloud-adminhub-postgres` |
| Engine | PostgreSQL `16.15` |
| Instance class | `db.t4g.micro` |
| Database name | `cloud_adminhub` |
| Master username | `cloudadminhub_admin` |
| Port | `5432` |
| Endpoint | `cloud-adminhub-postgres.ckvgy46sep04.us-east-1.rds.amazonaws.com` |
| DB subnet group | `cloud-adminhub-db-subnet-group` |
| Database security group | `sg-0e1854b33caba0cba` |
| Public accessibility | Disabled |
| Storage | 20 GiB gp3, encrypted |
| Multi-AZ | Disabled (development configuration) |
| Automated backup retention | 1 day |
| Deletion protection | Enabled |
| Master password | Managed by RDS in Secrets Manager |

The endpoint is private; a machine outside the VPC cannot connect directly unless private network access is deliberately configured. Do not open port 5432 to `0.0.0.0/0`.

### Application and Migration Credentials

Two separate Secrets Manager secrets hold runtime credentials:

- Application secret name: `cloud-adminhub/app-db-credentials`
- Migration secret name: `cloud-adminhub/migration-db-credentials`

The actual secret values must never be included in documentation or committed to Git. The RDS master password is managed by RDS through its own Secrets Manager secret. ECS tasks receive secret values at runtime through task-definition secret injection.

The one-off bootstrap task successfully created two PostgreSQL login roles and configured their permissions:

- `cloud_adminhub_app`: application data access; not granted schema creation permission.
- `cloud_adminhub_migrator`: database schema migration permissions used by Alembic.

Both credentials were verified by running a private ECS task that authenticated with each secret and logged the expected PostgreSQL username. The bootstrap task exited with code `0`.

### Alembic Migration Status

**Status: Completed and verified against RDS**

- [x] Created and applied the database schema migrations from a one-off ECS/Fargate task.
- [x] Used the dedicated `cloud_adminhub_migrator` account, not the RDS master account.
- [x] Ran the task in private subnets with public IP assignment disabled.
- [x] Confirmed the migration task exited with code `0`.
- [x] Ran `alembic current` against RDS and verified `7fd04a2937e7 (head)`.

The migration log showed these revisions being applied:

```text
 -> 87c75f7ea531, create users table
87c75f7ea531 -> 6205175b21c4, create refresh tokens table
6205175b21c4 -> c7c2f2bbbe8f, make frefresh token expiration timezone aware
c7c2f2bbbe8f -> 5f644160634f, create audit logs table
5f644160634f -> 81ff1c79c551, make target_user_id null on deletion
81ff1c79c551 -> 7fd04a2937e7, make user_id and actor_user_id nullifiable
```

Last verified RDS Alembic revision: `7fd04a2937e7` (head). The local Docker database was also verified at this revision. The application has not yet been deployed to ECS, so end-to-end API connectivity to RDS remains to be tested.

### Backup and Lifecycle Notes

- Storage encryption is enabled.
- Automated backup retention is one day, intended only for this development setup.
- Deletion protection is enabled and must be explicitly disabled before destroying the RDS instance.
- `skip_final_snapshot = false` requests a final snapshot on deletion. A unique `final_snapshot_identifier` is required for any later deletion/recreation that could otherwise reuse an existing identifier.
- Stopping RDS reduces instance compute charges but does not remove storage charges, and a stopped RDS instance can automatically restart after seven consecutive days.
- Verify the live DB status before running tasks; it has been stopped and restarted during development.

### Verification Commands

```bash
terraform output rds_endpoint
terraform output rds_port
terraform output rds_database_name
terraform output rds_master_secret_arn

aws rds describe-db-instances \
  --db-instance-identifier cloud-adminhub-postgres \
  --region us-east-1 \
  --query 'DBInstances[0].{Status:DBInstanceStatus,PubliclyAccessible:PubliclyAccessible,Encrypted:StorageEncrypted,DeletionProtection:DeletionProtection,Endpoint:Endpoint.Address}' \
  --output table
```

For RDS-hosted migrations, use the ECS migration task described in Section 12 rather than running `alembic` directly from the laptop.

## 9. Private VPC Endpoints

### Status: Deployed; all five verified `available`

Five VPC endpoints provide private subnet access to services required for ECS/Fargate without a NAT gateway.

| Endpoint service | Type | Purpose | Verified status |
|---|---|---|---|
| `com.amazonaws.us-east-1.ecr.api` | Interface | ECR API and registry metadata | `available` |
| `com.amazonaws.us-east-1.ecr.dkr` | Interface | Docker registry access for image pulls | `available` |
| `com.amazonaws.us-east-1.secretsmanager` | Interface | Secret retrieval by ECS task execution roles | `available` |
| `com.amazonaws.us-east-1.logs` | Interface | Publish container logs to CloudWatch Logs | `available` |
| `com.amazonaws.us-east-1.s3` | Gateway | Access ECR image layers stored in S3 | `available` |

### Configuration

- Four interface endpoints are deployed in both private subnets across two Availability Zones.
- Private DNS is enabled for the interface endpoints.
- The interface endpoints use security group `sg-05a44d9f9d66e1265`, which allows HTTPS ingress from the application security group.
- The S3 gateway endpoint is associated with both private route tables.
- The application security group allows HTTPS egress to the regional S3 prefix list `pl-63a5400a` for image-layer access.
- No NAT gateway exists. Private workloads can reach the listed AWS services through VPC endpoints, but do not have general internet egress.

### Cost Notes

Interface endpoints incur hourly charges for every endpoint in every Availability Zone, plus applicable data-processing charges. At the previously used estimate of $0.01 per endpoint-hour, four interface endpoint services across two Availability Zones cost about $58.40 for 730 hours before data processing. The S3 gateway endpoint has no hourly endpoint charge. These are estimates, not a bill guarantee; check current regional pricing and Cost Explorer.

### Verification

```bash
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)" \
  --region us-east-1 \
  --query 'VpcEndpoints[].{Service:ServiceName,State:State,Type:VpcEndpointType}' \
  --output table

terraform state list | grep vpc_endpoint
terraform plan
```

## 10. ECS Foundation and Bootstrap Task

### ECS Foundation Status: Deployed

The ECS cluster and base IAM/logging resources have been created. These resources organize tasks but do not by themselves deploy the persistent FastAPI service.

| Resource | Value | Purpose |
|---|---|---|
| ECS cluster | `cloud-adminhub` | Logical home for tasks and future API service |
| Cluster ARN | `arn:aws:ecs:us-east-1:364503394646:cluster/cloud-adminhub` | Cluster identifier |
| Task execution role | `cloud-adminhub-ecs-execution` | Used by ECS to pull images and send logs for the API task |
| Application task role | `cloud-adminhub-ecs-task` | Separate application identity; no additional permissions attached yet |
| API log group | `/ecs/cloud-adminhub-api` | Intended API container logs, seven-day retention |

### Bootstrap Task Status: Completed and Verified

A separate one-off Fargate task provisions PostgreSQL login roles and permissions. It uses `/ecs/cloud-adminhub-db-bootstrap` for logs.

- [x] Created a dedicated bootstrap task definition and execution role.
- [x] Scoped its execution role to retrieve the RDS-managed master secret and the application/migration credential secrets.
- [x] Kept the bootstrap task role separate and without additional AWS permissions.
- [x] Ran the task in private subnets with public IP assignment disabled.
- [x] Verified the bootstrap task exited with code `0`.
- [x] Verified both `cloud_adminhub_app` and `cloud_adminhub_migrator` authenticated successfully.

The bootstrap task's initial failure was traced to PostgreSQL reporting SQLSTATE `42P18` (`IndeterminateDatatype`) from an untyped parameter in the PostgreSQL `format()` call. The helper was updated to cast bound parameters explicitly to `text`; the succeeding task completed with `Database roles and permissions configured successfully.`

The latest image used for the successful RDS Alembic migration is `git-9fa439a`. The current bootstrap task definition was also updated to use the shared `api_image_tag` variable.

## 11. Secrets Manager and Database Role Security

### Status: Deployed and verified

Terraform manages secret containers for runtime application credentials and migration credentials. Secret values are written directly to Secrets Manager, not Terraform variables or source files.

| Purpose | Secret name | Intended access |
|---|---|---|
| RDS master password | RDS-managed secret | Bootstrap execution role only, for initial provisioning |
| Application DB login | `cloud-adminhub/app-db-credentials` | API task execution role when API deployment is configured |
| Alembic migration login | `cloud-adminhub/migration-db-credentials` | Migration task execution role |

The dedicated database bootstrap role has `secretsmanager:GetSecretValue` only for the three required secrets. The migration task execution role is scoped to retrieve only the migration secret. The normal application task role has no additional AWS permissions attached.

Passwords are not documented, printed, or committed. The temporary files used to populate secrets were stored outside the repository and removed after use.

## 12. ECS/Fargate Alembic Migration Task

### Status: Created and successfully run

Terraform defines the one-off task family `cloud-adminhub-db-migration`. Its container command is:

```bash
alembic upgrade head
```

Configuration:

- Runtime: Fargate, `awsvpc` network mode, `256` CPU units, `512` MiB memory.
- Image: `364503394646.dkr.ecr.us-east-1.amazonaws.com/cloud-adminhub-api:git-9fa439a`.
- Database host/name/port: injected as non-secret environment settings from RDS resource outputs.
- Credentials: `MIGRATION_DB_SECRET_JSON`, injected from `cloud-adminhub/migration-db-credentials`.
- Execution role: `cloud-adminhub-migration-execution`, attached to `AmazonECSTaskExecutionRolePolicy` plus permission to retrieve only the migration secret.
- Task role: `cloud-adminhub-migration-task`, with no additional AWS permissions.
- CloudWatch log group: `/ecs/cloud-adminhub-db-migration`, seven-day retention.
- Network: private subnets, application security group, and `assignPublicIp=DISABLED`.

### Verified Result

- [x] Registered the migration task definition.
- [x] Ran `alembic upgrade head` against RDS.
- [x] Verified the task stopped with exit code `0`.
- [x] Confirmed Alembic applied six revisions, ending at `7fd04a2937e7`.
- [x] Ran a follow-up `alembic current` task and verified `7fd04a2937e7 (head)`.

Run a migration task only when RDS is `available`. Launching the task is not proof of migration success; always check the exit code and logs.

Example task launch pattern (run from `terraform/` with a valid `cloudadminhub` AWS CLI session):

```bash
TASK_DEF="$(terraform output -raw migration_task_definition_arn)"

aws ecs run-task \
  --cluster cloud-adminhub \
  --task-definition "$TASK_DEF" \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-008255b204b1cfa5b,subnet-0b9b2802cbccec3d1],securityGroups=[sg-07505808890a04860],assignPublicIp=DISABLED}" \
  --region us-east-1 \
  --query '{TaskArns:tasks[*].taskArn,Failures:failures}' \
  --output json
```

After capturing the task ARN, wait for completion and inspect status:

```bash
aws ecs wait tasks-stopped --cluster cloud-adminhub --tasks "$TASK_ARN" --region us-east-1
aws ecs describe-tasks \
  --cluster cloud-adminhub \
  --tasks "$TASK_ARN" \
  --region us-east-1 \
  --query 'tasks[0].{Status:lastStatus,Reason:stoppedReason,Containers:containers[].{Name:name,ExitCode:exitCode}}' \
  --output json
aws logs tail /ecs/cloud-adminhub-db-migration --since 15m --region us-east-1
```

## 13. Deployment Roadmap

### Milestone 1: Network Security and Container Registry — Complete

- [x] Create security groups for the future load balancer, API, database, and endpoints.
- [x] Restrict inbound and inter-service traffic to intended ports.
- [x] Create a private ECR repository.
- [x] Enable scan-on-push, immutable image tags, and image lifecycle cleanup.
- [x] Build, push, and verify Git-tagged images in ECR.

### Milestone 2: RDS and Database Preparation — Complete

- [x] Create a DB subnet group using private subnets.
- [x] Provision encrypted PostgreSQL RDS without public accessibility.
- [x] Enable RDS-managed master password storage.
- [x] Configure backup retention and deletion protection.
- [x] Create application and migration credential secrets.
- [x] Create the `cloud_adminhub_app` and `cloud_adminhub_migrator` PostgreSQL roles.
- [x] Verify both role credentials.
- [x] Run Alembic migrations against RDS and verify revision `7fd04a2937e7`.

### Milestone 3: Private AWS Service Access — Complete

- [x] Create interface endpoints for ECR API, ECR Docker Registry, Secrets Manager, and CloudWatch Logs in both private subnets.
- [x] Create an S3 gateway endpoint for both private route tables.
- [x] Permit HTTPS egress to the regional S3 prefix list.
- [x] Verify all five endpoints are `available`.

### Milestone 4: ECS/Fargate Foundation and One-Off Tasks — Complete

- [x] Create the ECS cluster and base execution/application roles.
- [x] Create CloudWatch log groups.
- [x] Create the database bootstrap task and narrowly scope its secret permissions.
- [x] Run the bootstrap task and verify the application and migration logins.
- [x] Create the migration task with access only to migration credentials.
- [x] Run RDS schema migrations and verify the current Alembic revision.
- [ ] Configure the persistent FastAPI Fargate task definition.
- [ ] Configure application runtime database credentials securely.
- [ ] Create and test the ECS service in private subnets.

### Milestone 5: Application Load Balancer — Pending

- [ ] Create an ALB in the public subnets.
- [ ] Configure target group and `/health` health checks.
- [ ] Route HTTP traffic to FastAPI for initial testing.
- [ ] Configure HTTPS and a domain if available before treating the service as production-ready.
- [ ] Test API authentication, CRUD, RBAC, and audit logging end to end against RDS.

### Milestone 6: Monitoring and Operational Security — Pending

- [ ] Verify log retention and log redaction.
- [ ] Add useful CloudWatch metrics and alarms as appropriate.
- [ ] Review IAM permissions for least privilege.
- [ ] Verify secret handling and deployed refresh-token/session behavior.
- [ ] Verify budget alerts and teardown procedures.

### Milestone 7: CI/CD and Infrastructure Automation — Optional / Pending

- [ ] Automate tests and Docker builds with GitHub Actions.
- [ ] Automate publishing images to ECR.
- [ ] Automate ECS deployments.
- [ ] Review secure GitHub-to-AWS authentication using OIDC.
- [ ] Document rollback and troubleshooting procedures.

### Milestone 8: Cost Cleanup After Testing — Pending

- [ ] Complete end-to-end API tests during a short runtime window.
- [ ] Save any required data and decide whether an RDS snapshot is needed.
- [ ] Disable RDS deletion protection through Terraform before destroying RDS.
- [ ] Set a unique final snapshot identifier if retaining a snapshot.
- [ ] Remove billable application resources and the four interface endpoints.
- [ ] Decide whether to retain or delete the ECR images/repository and Terraform state bucket.
- [ ] Verify the final state in the AWS console and billing/Cost Explorer.

## 14. Git Workflow and Documentation

Each meaningful milestone should be committed separately.

Recommended workflow:

1. Modify application or Terraform configuration.
2. Format and validate configuration.
3. Run `terraform plan` and review all proposed changes.
4. Apply only after the plan is understood and accepted.
5. Verify deployed resources and task exit codes.
6. Update this guide with actual configuration and results.
7. Commit the relevant Terraform, application code, and documentation together.

Never commit secrets, local environment files, Terraform state files, temporary credential files, or generated secret JSON.

## 15. Cleanup Plan After End-to-End Testing

The project is intended to run only long enough to demonstrate the architecture. **The infrastructure has not yet been fully torn down.** RDS and the interface endpoints can incur ongoing charges while they exist, even if no API requests are being served.

Do not treat stopping an ECS service or stopping RDS as complete cleanup. RDS storage and backups can still incur charges while the DB instance is stopped; stopped RDS instances can automatically restart after seven consecutive days. Interface endpoints keep accruing hourly charges until deleted.

After the ALB/API end-to-end test succeeds:

1. Record test results and decide whether database data or a final snapshot must be retained.
2. Review the Terraform plan for changes to runtime resources before applying cleanup.
3. Ensure no API service or one-off ECS task is still running.
4. In `terraform/rds.tf`, set `deletion_protection = false`. If you need a final snapshot, set `final_snapshot_identifier` to a new unique name. Review and apply this change before the destroy operation.
5. Consider whether the existing final snapshot must be retained. Snapshots can incur storage charges; delete them later only if you no longer need the data.
6. Review the ECR repository's image contents. The repository may need to be emptied or configured for deliberate deletion before Terraform can remove it, since `force_delete` is not enabled by default.
7. Run `terraform plan -destroy` from the main `terraform/` directory, review the entire plan carefully, and run `terraform destroy` only after confirming it will remove the intended application resources.
8. Confirm the RDS instance, ALB/ECS resources, interface endpoints, ECR resources (if chosen), and associated application resources are removed as intended.
9. Decide whether to retain the separate Terraform state bucket and bootstrap state. Retaining the state bucket supports recreating the project, but that bucket is separate from the main infrastructure and is not removed by destroying the main Terraform configuration.
10. Check AWS billing/Cost Explorer after cleanup. Budget notifications are not hard spending limits.

Keep the Terraform configuration and documentation in Git so the architecture can be recreated later. Never remove or overwrite remote Terraform state manually as a substitute for Terraform destroy.

## 16. Current Status Summary

### Completed

- Local Docker development environment and local PostgreSQL.
- AWS CLI authentication, Terraform setup, and remote state with separate bootstrap and main state keys.
- VPC, Internet Gateway, two public subnets, two private subnets, route tables, and routing.
- Four security groups with restricted ALB-to-app, app-to-database, app-to-endpoint, and S3 egress.
- Four private interface VPC endpoints and one S3 gateway endpoint, all verified `available`.
- Private ECR repository with image scanning, immutable tags, and lifecycle cleanup.
- ECS cluster, execution/application roles, and CloudWatch API log group.
- RDS PostgreSQL with encrypted storage, private accessibility, RDS-managed master password, one-day backup retention, and deletion protection.
- Application and migration Secrets Manager secret values populated without committing credentials.
- PostgreSQL application and migration roles provisioned and both logins verified.
- One-off database bootstrap ECS task completed successfully.
- Dedicated ECS migration task completed successfully; RDS Alembic revision verified as `7fd04a2937e7 (head)`.
- Current image used by the successful migration task: `git-9fa439a`.

### Next Steps

1. Create the persistent FastAPI ECS task definition and service, injecting the application database secret (not the master or migration secrets).
2. Add the Application Load Balancer and health checks.
3. Test the API end to end against RDS, including authentication, CRUD, RBAC, and audit logging.
4. Update this guide and commit the final deployment milestone.
5. Tear down billable AWS resources promptly after testing, using the cleanup plan above.
