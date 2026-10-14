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

No NAT gateways, ECS services, load balancers, VPC endpoints, or RDS instances have been created yet.

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
| Endpoints | `sg-05a44d9f9d66e1265` | Future interface VPC endpoints |

### Allowed Traffic

| Source | Destination | Protocol / port | Purpose |
|---|---|---|---|
| Internet (`0.0.0.0/0`) | ALB security group | TCP 80 | HTTP entry to the load balancer |
| ALB security group | App security group | TCP 8000 | Forward requests to FastAPI |
| App security group | Database security group | TCP 5432 | PostgreSQL connections |
| App security group | Endpoints security group | TCP 443 | HTTPS connections to future private AWS service endpoints |

The corresponding destination ingress rules allow traffic only from the intended source security group, except for the ALB's public HTTP rule. The application and database ports are not directly open to the internet. The rules are defined as standalone Terraform ingress/egress rule resources in `security_groups.tf`.

**Current limitations:** the ALB security group allows HTTP on port 80; HTTPS has not been configured yet. The endpoints security group is only a security group at this stage—the VPC endpoint resources themselves have not been created. Before ECS tasks can pull images, retrieve secrets, or publish logs without NAT, the required VPC endpoints and routes must be planned and deployed.

### Verification

From the main `terraform/` directory, confirm the outputs and managed resources:

```bash
terraform output
terraform state list | grep security_group
terraform plan
```

The plan should report no changes when the deployed infrastructure matches the configuration.

## 7. Deployment Roadmap

The following milestones remain.

### Milestone 1: Network Security and Container Registry

- [x] Create security groups for the future load balancer, API, database, and endpoints.
- [x] Restrict inbound and inter-service traffic to the required ports.
- [ ] Create an Amazon ECR repository.
- [ ] Build, tag, and push the AdminHub Docker image to ECR.
- [ ] Document image publishing and verification commands.

### Milestone 2: Amazon RDS for PostgreSQL

- [ ] Create a DB subnet group using the private subnets.
- [x] Create the RDS security group and restrict PostgreSQL ingress to the app security group.
- [ ] Provision PostgreSQL in private subnets.
- [ ] Store database credentials in AWS Secrets Manager.
- [ ] Run Alembic migrations against RDS.
- [ ] Verify database connectivity and migrations.
- [ ] Document backup, deletion protection, and cost considerations.

### Milestone 3: ECS and Fargate

- [ ] Create an ECS cluster.
- [ ] Define the task execution role and application task role.
- [ ] Configure the Fargate task definition.
- [ ] Configure the application environment and secrets.
- [ ] Configure CloudWatch logging.
- [ ] Deploy the FastAPI service in private subnets.
- [ ] Verify health checks and database connectivity.

### Milestone 4: Application Load Balancer

- [ ] Create an Application Load Balancer in the public subnets.
- [ ] Configure target groups and health checks.
- [ ] Allow inbound web traffic only through the intended entry point.
- [ ] Configure HTTPS and a domain if available.
- [ ] Test the deployed API endpoints.

### Milestone 5: Monitoring and Operational Security

- [ ] Configure CloudWatch log retention.
- [ ] Add useful metrics and alarms.
- [ ] Review IAM permissions for least privilege.
- [ ] Verify secret handling and log redaction.
- [ ] Review refresh-token and session behavior in the deployed environment.
- [ ] Verify cost alerts and resource cleanup procedures.

### Milestone 6: CI/CD and Infrastructure Automation

- [ ] Automate tests and Docker builds with GitHub Actions.
- [ ] Automate publishing container images to ECR.
- [ ] Automate deployment to ECS.
- [ ] Review options for secure GitHub-to-AWS authentication using OIDC.
- [ ] Review infrastructure and deployment changes through Git.
- [ ] Document rollback and troubleshooting procedures.

## 8. Git Workflow and Documentation

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

## 9. Current Status

The following have been completed:

- Local Docker development environment.
- Local PostgreSQL container and administrator bootstrap.
- AWS CLI authentication and Terraform setup.
- Remote Terraform state with separate bootstrap and main state keys.
- VPC, Internet Gateway, public/private subnets, and routing.
- Four network security groups with restricted ALB-to-app, app-to-database, and app-to-endpoint traffic.

**Next milestone:** create an Amazon ECR repository and push the container image. Then prepare the private RDS deployment, including outbound access through suitable VPC endpoints or NAT as required.