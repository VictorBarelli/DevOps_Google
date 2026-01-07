# GCP DevOps Dashboard

A Flask web app deployed on Google Cloud Run with automated CI/CD via Cloud Build.

## What it does

- User authentication (login/register with password hashing)
- Admin panel to view all users
- Reaction time game (just for fun)
- Auto-deploys when you push to main

## Tech stack

- Python/Flask
- Docker
- Terraform (for GCP infrastructure)
- Cloud Build (CI/CD)
- Cloud Run (hosting)

## Quick start

1. Clone the repo
2. Set up GCP project and enable APIs:
   ```
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
   ```
3. Deploy infrastructure:
   ```
   cd terraform
   terraform init
   terraform apply
   ```
4. Push to main branch - Cloud Build handles the rest

## Local development

```bash
cd app
pip install -r requirements.txt
python main.py
```

App runs on http://localhost:8080

Default admin login: `admin@admin.com` / `admin123`

## Project structure

```
├── app/
│   ├── main.py            # Flask app
│   ├── templates/         # HTML templates
│   ├── static/            # CSS
│   └── Dockerfile
├── terraform/
│   ├── main.tf            # Cloud Run, Artifact Registry
│   ├── monitoring.tf      # Alerts and uptime checks
│   └── variables.tf
├── cloudbuild.yaml        # CI/CD pipeline
└── tests/                 # pytest tests
```

## CI/CD pipeline

The pipeline runs on every push:
1. Lint (flake8) - code style checks
2. Security scan (Bandit) - Python security vulnerabilities
3. Run tests (pytest)
4. Build Docker image
5. Container scan (Trivy) - image vulnerability scan
6. Push to Artifact Registry
7. Deploy to Cloud Run

### Security scanning

**Bandit** scans Python code for:
- Hardcoded passwords/secrets
- SQL injection risks
- Insecure function usage
- Weak cryptography

**Trivy** scans Docker images for:
- Known CVEs in OS packages
- Vulnerable Python dependencies
- Outdated base images

## Environment variables

| Variable | Description |
|----------|-------------|
| SECRET_KEY | Flask session key |
| ADMIN_EMAIL | Default admin email |
| ADMIN_PASSWORD | Default admin password |

## Monitoring

Terraform sets up Cloud Monitoring alerts for:
- High error rate (5xx responses)
- High latency (p99 > 5s)
- Instance count spikes
- Uptime checks
