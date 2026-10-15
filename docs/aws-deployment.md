# Cloud AdminHub — AWS Deployment Guide

## 1. Project Overview

Cloud AdminHub is a FastAPI application for internal user administration, authentication, role-based access control (RBAC), session management, and audit logging.

The application is being migrated from a local development environment to AWS using Terraform for infrastructure as code and Amazon ECS with AWS Fargate for container hosting.

### Planned Architecture

- **Amazon VPC:** Isolated network for application infrastructure.
- **Application Load Balancer (ALB):** Routes incoming HTTP/HTTPS requests to the API.
- **Amazon ECS with AWS Fargate:** Runs the containerized FastAPI application.
- **Amazon ECR:** Stores Docker images.
- **Amazon RDS for PostgreSQL:** Managed relational database.
- **AWS Secrets Manager:** Stores application secrets and database credentials.
- **Amazon CloudWatch:** Application logs, metrics, and alarms.
- **AWS IAM:** Controls permissions for deployment and application components.
- **Terraform:** Defines and manages AWS infrastructure.

## 2. AWS Account Preparation

### Completed

- [x] Created the `iamadmin` IAM user with administrative permissions for infrastructure setup.
- [x] Enabled MFA for the IAM administrative account.
- [x] Created an AWS monthly cost budget with spending notifications.
- [x] Installed AWS CLI in the Ubuntu/WSL environment.
- [x] Installed Terraform.
- [x] Configured browser-based AWS CLI authentication using `aws login`.
- [x] Verified the AWS identity using STS.
- [x] Configured the `cloudadminhub` AWS CLI profile.
- [x] Configured the `terraform-cloudadminhub` profile to obtain temporary credentials through AWS CLI's `credential_process`.
- [x] Selected US East (N. Virginia), `us-east-1`, as the deployment region.

### Authentication

Terraform uses the `terraform-cloudadminhub` profile. This profile obtains credentials through the `cloudadminhub` AWS CLI profile.

Verify the active AWS identity:

```bash
aws sts get-caller-identity --profile terraform-cloudadminhub
```

If the AWS CLI session expires, reauthenticate:

```bash
aws login --remote --profile cloudadminhub --region us-east-1
```

Complete the browser sign-in flow, then verify the identity again.

Do not store AWS credentials, access keys, secret keys, or session tokens in the project repository.

### Security and Cost Controls

- The application will use dedicated IAM roles with least-privilege permissions.
- Infrastructure changes must be reviewed using `terraform plan` before being applied.
- Monthly AWS budget notifications are alerts, not hard spending limits.
- Review resource costs throughout deployment and remove resources that are no longer needed.
- Do not commit environment files, credentials, or Terraform state files.

## 3. Local Development and Docker

### Completed

- [x] Created a Dockerfile for the FastAPI application.
- [x] Created a `.dockerignore` file.
- [x] Built the `cloud-adminhub:local` Docker image.
- [x] Installed Docker Desktop with WSL integration.
- [x] Created a Docker Compose environment for the API and PostgreSQL.
- [x] Created a local administrator bootstrap script.
- [x] Successfully tested login against the containerized PostgreSQL database.

### Local Container Environment

The local development architecture consists of two containers:

- `api`: FastAPI application, exposed on port 8000.
- `db`: PostgreSQL database, accessible to the API through Docker Compose networking.

The API connects to the database using the Compose service hostname `db`, not `127.0.0.1`.

### Common Commands

Start the environment:

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

### Database Migrations

The application schema is managed using Alembic.

Apply migrations to the local Docker database:

```bash
docker compose --env-file .env.docker run --rm api alembic upgrade head
```

Database migrations are executed explicitly rather than creating tables automatically when the FastAPI application starts.

## 4. Terraform Setup

### Completed

- [x] Created the main Terraform configuration directory.
- [x] Configured the AWS provider for `us-east-1`.
- [x] Declared Terraform and AWS provider version constraints.
- [x] Initialized the AWS provider.
- [x] Committed the Terraform dependency lock file.
- [x] Verified the AWS identity through Terraform.
- [x] Created a dedicated S3 bucket for Terraform state.
- [x] Enabled S3 bucket versioning and server-side encryption.
- [x] Blocked public access to the state bucket.
- [x] Migrated the bootstrap Terraform state into S3.
- [x] Configured the main Terraform project to use a separate S3 state key.
- [x] Enabled S3-native state locking with `use_lockfile = true`.

### Directory Structure

```text
terraform/
├── versions.tf
├── provider.tf
├── variables.tf
├── main.tf
├── network.tf
├── security_groups.tf
├── ecr.tf
├── rds.tf
├── endpoints.tf
├── outputs.tf
├── .terraform.lock.hcl
└── bootstrap-state/
    ├── versions.tf
    ├── provider.tf
    ├── main.tf
    └── outputs.tf
```

The bootstrap configuration manages the remote-state bucket. The main configuration manages the application infrastructure.

### Remote State

Terraform state is stored in a dedicated S3 bucket. The bootstrap and main configurations use separate state keys so they can be managed independently.

- Bootstrap state: `bootstrap/terraform.tfstate`
- Main infrastructure state: `cloud-adminhub/terraform.tfstate`

S3 versioning supports recovery of previous state versions. S3-native locking helps prevent concurrent Terraform operations from modifying the same state at the same time.

Terraform state can contain sensitive information. It must not be committed to Git or made publicly accessible.

### Terraform Workflow

Run commands from the appropriate Terraform directory.

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

Inspect managed resources:

```bash
terraform state list
```

Inspect outputs:

```bash
terraform output
```

### Terraform Security and Version Control

The repository should commit `.terraform.lock.hcl`, but exclude Terraform working directories and state files.

The root `.gitignore` should include:

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

Review these exclusions against the actual repository configuration before committing changes. Do not commit real environment files or generated Terraform state.

## 5. VPC Networking

### Status: Deployed

Region: `us-east-1` — US East (N. Virginia)

VPC CIDR: `10.0.0.0/16`

The VPC spans two Availability Zones and contains four subnets.

| Subnet | CIDR | Intended purpose |
|---|---|---|
| Public 1 | `10.0.1.0/24` | Future Application Load Balancer |
| Public 2 | `10.0.2.0/24` | Future Application Load Balancer |
| Private 1 | `10.0.11.0/24` | Future ECS tasks and RDS |
| Private 2 | `10.0.12.0/24` | Future ECS tasks and RDS |

### Implemented Resources

- [x] VPC with DNS support and DNS hostnames enabled.
- [x] Internet Gateway.
- [x] Two public subnets.
- [x] Two private subnets.
- [x] Public route table with a default route to the Internet Gateway.
- [x] Private route table for each private subnet.
- [x] Route table associations for all four subnets.
- [x] Terraform outputs for the VPC ID, subnet IDs, Availability Zones, and security group IDs.

The public route table provides a route to the Internet Gateway. The private route tables currently have no internet route. Public subnets do not automatically assign public IP addresses to launched instances.

No NAT gateways, ECS services, or load balancers have been created yet. The RDS PostgreSQL instance is deployed in the private subnets. Four interface VPC endpoints and one S3 gateway endpoint are now deployed for private access to required AWS services.

### Verification

From the main `terraform/` directory:

```bash
terraform output
terraform state list
terraform plan
```

The plan should report no changes when the deployed infrastructure matches the configuration.

## 6. Network Security Groups

### Status: Deployed

Terraform creates four security groups in VPC `vpc-07e99495df3b0366b`. They establish the intended traffic boundaries for the future load balancer, FastAPI tasks, database, and private AWS service endpoints.

| Security group | Resource ID | Purpose |
|---|---|---|
| ALB | `sg-0340189952a96b1c8` | Public web entry point |
| App | `sg-07505808890a04860` | FastAPI ECS tasks |
| Database | `sg-0e1854b33caba0cba` | RDS PostgreSQL |
| Endpoints | `sg-05a44d9f9d66e1265` | Interface VPC endpoints |

### Allowed Traffic

| Source | Destination | Protocol / port | Purpose |
|---|---|---|---|
| Internet (`0.0.0.0/0`) | ALB security group | TCP 80 | HTTP entry to the load balancer |
| ALB security group | App security group | TCP 8000 | Forward requests to FastAPI |
| App security group | Database security group | TCP 5432 | PostgreSQL connections |
| App security group | Endpoints security group | TCP 443 | HTTPS connections to future private AWS service endpoints |

The corresponding destination ingress rules allow traffic only from the intended source security group, except for the ALB's public HTTP rule. The application and database ports are not directly open to the internet. The rules are defined as standalone Terraform ingress/egress rule resources in `security_groups.tf`.

**Current limitations:** the ALB security group allows HTTP on port 80; HTTPS has not been configured yet. The endpoints security group is attached to the four interface endpoints described in the private VPC endpoints section. Private AWS service access is now configured without a NAT gateway. HTTPS to the regional S3 prefix list is explicitly allowed from the application security group for ECR image-layer downloads.

### Verification

From the main `terraform/` directory, confirm the outputs and managed resources:

```bash
terraform output
terraform state list | grep security_group
terraform plan
```

The plan should report no changes when the deployed infrastructure matches the configuration.

## 7. Amazon ECR Container Registry

### Status: Deployed

A private Amazon Elastic Container Registry (ECR) repository has been created for the Cloud AdminHub API image.

- Repository name: `cloud-adminhub-api`
- Region: `us-east-1`
- Repository URL: `364503394646.dkr.ecr.us-east-1.amazonaws.com/cloud-adminhub-api`
- Repository ARN: `arn:aws:ecr:us-east-1:364503394646:repository/cloud-adminhub-api`
- Terraform resource: `aws_ecr_repository.api`
- Lifecycle policy resource: `aws_ecr_lifecycle_policy.api`

### Repository Configuration

- [x] Enabled image scanning on push.
- [x] Set image tag mutability to `IMMUTABLE` to prevent overwriting existing tags.
- [x] Added a lifecycle rule to retain the 10 most recent images with tags beginning `git-`.
- [x] Added a lifecycle rule to expire untagged images after one day.
- [x] Added Terraform outputs for the repository URL and ARN.

The lifecycle policy expects published Git-versioned images to use tags such as `git-a1b2c3d`. Untagged images are eligible for expiration after one day. The application image has now been built and pushed to ECR. The build used a `.dockerignore` file that reduced the Docker build context from about 1.67 GB to 3.79 kB, excluding local artifacts such as virtual environments, Git metadata, environment files, and Terraform working/state files. Keep `.dockerignore` up to date so local secrets and unrelated files are not sent to the build engine.

### Verified Image

- Image tag: `git-2c6bacd`
- Image digest: `sha256:c419448d5500f13d77b55d7ae03ba049f004d7973114ae53fbd14efb4daa4943`
- Pushed at: `2026-10-14 16:51:34 -04:00`

The digest and tag were verified using `aws ecr describe-images`.

### Build, Authenticate, Push, and Verify

Run the Docker commands from the repository root, where the `Dockerfile` is located. The Git-based image tag is derived from the current commit hash.

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
  --image-ids imageTag="$IMAGE_TAG" \
  --region "$AWS_REGION" \
  --query 'imageDetails[0].{Tags:imageTags,Digest:imageDigest,PushedAt:imagePushedAt}' \
  --output table
```

The current verified image is tagged `git-2c6bacd` with digest `sha256:c419448d5500f13d77b55d7ae03ba049f004d7973114ae53fbd14efb4daa4943`.

#### WSL Docker credential-store workaround

If `docker login` fails while saving credentials with an error such as `The stub received bad data`, use a temporary Docker configuration in WSL before running the login and push commands:

```bash
export DOCKER_CONFIG="$(mktemp -d)"
chmod 700 "$DOCKER_CONFIG"
```

After the push is complete, remove the temporary credential configuration:

```bash
rm -rf "$DOCKER_CONFIG"
unset DOCKER_CONFIG
```

Use this workaround only for that session; the temporary configuration may contain an encoded ECR login token.

From the main `terraform/` directory, verify the registry infrastructure:

```bash
terraform output ecr_repository_url
terraform output ecr_repository_arn
terraform state list | grep ecr
terraform plan
```

The expected Terraform resources in state are `aws_ecr_repository.api` and `aws_ecr_lifecycle_policy.api`. The plan should report no changes when the deployed infrastructure matches the configuration.

## 8. Amazon RDS for PostgreSQL

### Status: Deployed

Terraform provisions a PostgreSQL database in the private subnets. The DB subnet group contains both private subnets in separate Availability Zones; the database itself is single-AZ for this development environment.

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
| Master secret | Stored and managed by RDS in AWS Secrets Manager |
| Master secret ARN | `arn:aws:secretsmanager:us-east-1:364503394646:secret:rds!db-d477a5c4-4926-456e-8830-9bd52300e8fd-YoNfqh` |

The RDS endpoint is private; a machine outside the VPC cannot connect to it directly unless private network access is deliberately configured. The existing database security group allows PostgreSQL ingress from the application security group only. Do not open port 5432 to `0.0.0.0/0`.

RDS manages the master password through Secrets Manager, so no database password is hardcoded in Terraform configuration. Do not retrieve the secret value for documentation or commit it to Git. The application should eventually use a separate, least-privilege database user rather than the RDS master user.

### Backup and lifecycle notes

- Storage encryption is enabled.
- Automated backup retention is configured for one day, which is suitable only for this initial development setup and should be reviewed before production.
- Deletion protection is enabled.
- `skip_final_snapshot = false` requests a final snapshot on deletion. The configured final snapshot identifier must be changed to a new unique value if a later deletion/recreation would reuse an existing snapshot name.
- RDS incurs ongoing charges while provisioned; check AWS billing and remove billable resources when they're no longer needed. Deletion protection must be explicitly disabled before Terraform can delete the instance.

### Outputs and verification

From the main `terraform/` directory:

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

terraform plan
```

Verify that the RDS status is `available`, `PubliclyAccessible` is `False`, storage is encrypted, and deletion protection is enabled. The Terraform plan should show no changes when the deployed resources match the configuration.

### Still required before application integration

- [ ] Create a separate application database user with only the required privileges.
- [ ] Configure private application access to the database and required AWS services.
- [ ] Run Alembic migrations against RDS from a controlled environment inside the VPC or another secure path.
- [ ] Verify database connectivity and migrations without exposing the database publicly.

## 9. Private VPC Endpoints

### Status: Deployed

Five VPC endpoints have been created so workloads in the private subnets can access the AWS services required for an ECS/Fargate deployment without a NAT gateway.

| Endpoint service | Endpoint type | Intended use | Status verified |
|---|---|---|---|
| `com.amazonaws.us-east-1.ecr.api` | Interface | ECR API and registry metadata | `available` |
| `com.amazonaws.us-east-1.ecr.dkr` | Interface | Docker registry access for image pulls | `available` |
| `com.amazonaws.us-east-1.secretsmanager` | Interface | Retrieve the RDS-managed master secret at task startup | `available` |
| `com.amazonaws.us-east-1.logs` | Interface | Publish container logs to CloudWatch Logs | `available` |
| `com.amazonaws.us-east-1.s3` | Gateway | Download ECR image layers stored in S3 | `available` |

### Configuration

- The four interface endpoints are deployed in both private subnets across the two Availability Zones.
- Private DNS is enabled for the interface endpoints.
- The interface endpoints use the existing endpoints security group, `sg-05a44d9f9d66e1265`, which allows HTTPS ingress from the application security group.
- The S3 gateway endpoint is associated with both private route tables.
- The application security group has an HTTPS egress rule to the AWS-managed regional S3 prefix list (`pl-63a5400a`) for image-layer access.
- No NAT gateway has been created. Private workloads can access these listed AWS services through VPC endpoints, but they do not have general internet egress.

### Cost and teardown planning

Interface endpoints incur hourly charges for each endpoint in each Availability Zone, in addition to applicable data-processing charges. With four interface endpoint services across two Availability Zones, the approximate baseline at the previously estimated rate is about $58.40 per 730-hour month, before data processing and other AWS charges. The S3 gateway endpoint has no hourly endpoint charge. These are estimates, not a bill guarantee; check current regional pricing and Cost Explorer.

This project is intended to run only long enough to validate the architecture. After end-to-end testing, remove chargeable runtime resources rather than leaving them running. Keep the Terraform configuration and remote state so the environment can be recreated. Before teardown, retain any data or database snapshot you need, explicitly disable RDS deletion protection, and review the planned destruction carefully. Removing the RDS instance, interface endpoints, load balancer, and ECS resources is a separate operation from simply stopping application tasks.

### Verification

From the main `terraform/` directory:

```bash
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)" \
  --region us-east-1 \
  --query 'VpcEndpoints[].{Service:ServiceName,State:State,Type:VpcEndpointType}' \
  --output table

terraform state list | grep vpc_endpoint
terraform plan
```

The five endpoints were verified as `available`: four interface endpoints and one S3 gateway endpoint. The plan should report no changes when deployed resources match the configuration.

## 10. ECS Foundation

### Status: Deployed

The initial ECS foundation has been created in `us-east-1`. These resources prepare the project for Fargate tasks but do not run the application yet.

| Resource | Value | Purpose |
|---|---|---|
| ECS cluster | `cloud-adminhub` | Logical home for the API service and tasks |
| Cluster ARN | `arn:aws:ecs:us-east-1:364503394646:cluster/cloud-adminhub` | Cluster identifier |
| Task execution role | `cloud-adminhub-ecs-execution` | Used by ECS to pull container images and send logs |
| Execution role policy | `AmazonECSTaskExecutionRolePolicy` | Standard image-pull and logging permissions |
| Application task role | `cloud-adminhub-ecs-task` | Separate application identity; no additional permissions attached yet |
| CloudWatch log group | `/ecs/cloud-adminhub-api` | API container logs, retained for seven days |

### Verification

Terraform outputs confirmed the cluster name and ARN, both IAM role ARNs, and the log group name.

```bash
terraform output ecs_cluster_name
terraform output ecs_cluster_arn
terraform output ecs_task_execution_role_arn
terraform output ecs_task_role_arn
terraform output ecs_log_group_name
```

The Fargate task definition and ECS service have not been created yet. Before deploying tasks, configure the application to consume database connection settings securely, grant the execution role access to the required Secrets Manager secret, and create a least-privilege database user instead of using the RDS master user for routine application connections.

## 11. Deployment Roadmap

The following milestones remain.

### Milestone 1: Network Security and Container Registry

- [x] Create security groups for the future load balancer, API, database, and endpoints.
- [x] Restrict inbound and inter-service traffic to the required ports.
- [x] Create a private Amazon ECR repository.
- [x] Enable scan-on-push, immutable image tags, and an image lifecycle policy.
- [x] Build the AdminHub Docker image with a Git-based tag.
- [x] Authenticate Docker to ECR and push the image.
- [x] Verify the pushed image tag and digest.
- [x] Document image publishing, verification, and the WSL credential-store workaround.

### Milestone 2: Amazon RDS for PostgreSQL

- [x] Create a DB subnet group using the private subnets.
- [x] Create the RDS security group and restrict PostgreSQL ingress to the app security group.
- [x] Provision PostgreSQL in private subnets.
- [x] Enable RDS-managed master password storage in Secrets Manager.
- [x] Configure encrypted storage, backups, and deletion protection.
- [x] Record the private endpoint and master secret ARN in this guide.
- [ ] Create a least-privilege application database user.
- [ ] Run Alembic migrations against RDS.
- [ ] Verify application connectivity and migrations.

### Milestone 3: Private AWS Service Access

- [x] Create interface endpoints for ECR API, ECR Docker Registry, Secrets Manager, and CloudWatch Logs in both private subnets.
- [x] Create an S3 gateway endpoint associated with both private route tables.
- [x] Permit application HTTPS egress to the regional S3 prefix list.
- [x] Verify all five endpoints are `available`.

### Milestone 4: ECS and Fargate

- [x] Create the ECS cluster.
- [x] Create the task execution role and attach the standard ECS execution policy.
- [x] Create a separate application task role with no extra permissions initially.
- [x] Create a CloudWatch log group with seven-day retention.
- [ ] Configure the Fargate task definition.
- [ ] Configure the application environment and secrets.
- [ ] Grant the execution role access to the required Secrets Manager secret.
- [ ] Deploy the FastAPI service in private subnets.
- [ ] Verify health checks and database connectivity.

### Milestone 5: Application Load Balancer

- [ ] Create an Application Load Balancer in the public subnets.
- [ ] Configure target groups and health checks.
- [ ] Allow inbound web traffic only through the intended entry point.
- [ ] Configure HTTPS and a domain if available.
- [ ] Test the deployed API endpoints.

### Milestone 6: Monitoring and Operational Security

- [ ] Configure CloudWatch log retention.
- [ ] Add useful metrics and alarms.
- [ ] Review IAM permissions for least privilege.
- [ ] Verify secret handling and log redaction.
- [ ] Review refresh-token and session behavior in the deployed environment.
- [ ] Verify cost alerts and resource cleanup procedures.

### Milestone 7: CI/CD and Infrastructure Automation

- [ ] Automate tests and Docker builds with GitHub Actions.
- [ ] Automate publishing container images to ECR.
- [ ] Automate deployment to ECS.
- [ ] Review options for secure GitHub-to-AWS authentication using OIDC.
- [ ] Review infrastructure and deployment changes through Git.
- [ ] Document rollback and troubleshooting procedures.

## 12. Git Workflow and Documentation

Each meaningful milestone should be committed separately.

Recommended workflow:

1. Modify Terraform or application configuration.
2. Format and validate the configuration.
3. Run `terraform plan` and review all proposed changes.
4. Apply only after the plan is understood and accepted.
5. Verify the deployed resources.
6. Update this deployment guide with the actual configuration and results.
7. Commit the Terraform changes and relevant documentation together.

Never commit secrets, local environment files, Terraform state files, or temporary credentials.

## 13. Current Status

The following have been completed:

- Local Docker development environment.
- Local PostgreSQL container and administrator bootstrap.
- AWS CLI authentication and Terraform setup.
- Remote Terraform state with separate bootstrap and main state keys.
- VPC, Internet Gateway, public/private subnets, and routing.
- Four network security groups with restricted ALB-to-app, app-to-database, and app-to-endpoint traffic.
- Four private interface VPC endpoints (ECR API, ECR Docker Registry, Secrets Manager, CloudWatch Logs) and one S3 gateway endpoint, all verified as `available`.
- ECS cluster, separate task execution and application roles, standard execution-policy attachment, and seven-day CloudWatch log group.
- Private ECR repository with image scanning, immutable tags, and lifecycle cleanup policy.
- Docker image `git-2c6bacd` pushed to ECR and verified by digest.
- Private RDS for PostgreSQL with encrypted storage, RDS-managed master password in Secrets Manager, one-day automated backup retention, and deletion protection.

**Next milestone:** configure the Fargate task definition and ECS service, including secure database settings, permissions for reading the required secret, and CloudWatch logging. The cluster, IAM roles, and log group are already created. The endpoints support access to required AWS services without NAT. RDS is provisioned privately; application database user creation and Alembic migrations remain outstanding. Keep the time-limited test objective in mind and remove billable runtime resources after verification.