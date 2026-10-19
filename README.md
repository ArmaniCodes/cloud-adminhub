# Cloud AdminHub

Cloud AdminHub is a backend API for employee and user administration, built to demonstrate backend engineering and AWS infrastructure skills.

> **Deployment status:** The AWS demo environment was deployed and validated in October 2026, then intentionally destroyed to avoid ongoing charges. There is no live hosted API. The Terraform files still describe infrastructure that can incur charges if intentionally recreated; do not run `terraform apply` unless you are deliberately redeploying it.

## Features

- FastAPI REST API with generated OpenAPI documentation.
- PostgreSQL persistence through SQLAlchemy and versioned Alembic migrations.
- Password hashing with `pwdlib`'s recommended password-hashing configuration.
- Short-lived JWT access tokens and opaque refresh tokens.
- SHA-256 hashed refresh-token storage, rotation, revocation, and reuse handling.
- Role-based access control with `admin`, `support`, and `viewer` roles.
- Admin-restricted user creation, updates, deletion, and audit-log access.
- Audit events for user and password changes.
- Docker Compose development environment with PostgreSQL.
- Terraform configuration documenting the AWS deployment architecture.

## Technology

Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL 16, PyJWT, pwdlib/Argon2, Docker Compose, Terraform, Amazon ECS/Fargate, Amazon RDS, Amazon ECR, AWS Secrets Manager, CloudWatch, and IAM.

## Architecture

During the AWS demo, a public Application Load Balancer forwarded HTTP traffic to a private FastAPI service on ECS/Fargate. The service connected to private PostgreSQL on RDS. ECR stored container images, Secrets Manager supplied runtime secrets, CloudWatch collected logs, and Terraform defined the network, security groups, compute, database, and supporting resources.

That deployment was for demonstration only and was **not configured for HTTPS**. Its AWS resources have since been destroyed. Do not send real credentials or tokens over the former HTTP endpoint.

## API overview

| Method | Endpoint | Access |
|---|---|---|
| POST | `/auth/login` | Public |
| POST | `/auth/refresh` | Public; requires a valid refresh token |
| POST | `/auth/logout` | Public; requires a refresh token to revoke |
| GET | `/auth/me` | Authenticated |
| POST | `/auth/change-password` | Authenticated |
| GET | `/users` | Authenticated |
| GET | `/users/{user_id}` | Authenticated |
| POST | `/users` | Admin |
| PATCH | `/users/{user_id}` | Admin |
| DELETE | `/users/{user_id}` | Admin |
| GET | `/audit-logs` | Admin |

Interactive API docs are available at `/docs` when the application is running locally.

## Run locally with Docker Compose

### Prerequisites

- Docker Desktop with Docker Compose v2, or another Docker Compose v2 environment.
- Python 3.12 if running the test suite directly on your machine.

### 1. Configure the environment

From the repository root:

```bash
cp .env.example .env
openssl rand -hex 32
```

Paste the generated random value into `SECRET_KEY` in `.env`. Replace the example database password with a strong, local-only password. The `.env` file is ignored by Git; never commit it.

### 2. Start PostgreSQL and the API

```bash
docker compose up --build -d
docker compose ps
```

### 3. Apply database migrations

```bash
docker compose exec api alembic upgrade head
```

Schema changes are managed by Alembic. Do not use `Base.metadata.create_all()` as a substitute for migrations.

### 4. Create an administrator

```bash
docker compose exec api python scripts/create_admin.py
```

Follow the prompts to enter the administrator name, email, and password.

### 5. Check the API

- OpenAPI docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

Stop containers but retain the local database volume with:

```bash
docker compose down
```

To delete the local database volume as well (this removes local database data):

```bash
docker compose down -v
```

## Run unit tests

Install the project requirements in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
pytest -q
```

On Windows, activate the environment with `.venv\\Scripts\\activate` in PowerShell.

The unit tests cover access-token validation, refresh-token hashing, password-hashing helpers, and role authorization. They do not replace database-backed endpoint integration tests; extending coverage for login, refresh rotation/reuse, CRUD permissions, and audit-log persistence is a useful next step.

A GitHub Actions workflow is included to run the unit test suite on pushes and pull requests.

## Repository layout

```text
app/
  routes/       API route handlers
  schemas/      Pydantic request and response schemas
  models/       SQLAlchemy ORM models
  services/     Authentication, user, and audit business logic
  security/     Password and token helpers, authorization dependencies
  test/         Pytest unit tests
alembic/        Versioned database migrations
scripts/        Administrator and database bootstrap utilities
terraform/      AWS infrastructure configuration
docs/           Deployment history and teardown notes
```

## Security and operational notes

- Use a unique, strong `SECRET_KEY` outside tests.
- Keep `.env`, AWS credentials, secret values, Terraform state, and plan files out of Git.
- Use HTTPS before exposing authenticated endpoints outside a local development environment.
- Budget alerts are not spending caps. Review AWS Billing after any future deployment.
- The Terraform backend is configured to use local state after the S3 state bucket was deleted. Terraform state files are ignored by Git; keep local backups secure.
- Terraform configuration can recreate billable AWS resources. Review the plan and expected costs before intentionally deploying anything.

## Deployment history

See [docs/aws-deployment.md](docs/aws-deployment.md) for the architecture, configuration decisions, deployment validation, and completed teardown record.
