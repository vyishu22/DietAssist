# Deployment Guide

This document provides deployment options for the DietAssist backend.

## Local Development

To run the backend locally for development:

```bash
cd backend
pip install -r requirements.txt
python run.py
```

Ensure MongoDB and Redis are running:

```bash
# Terminal 1: MongoDB
mongod

# Terminal 2: Redis
redis-server

# Terminal 3: Backend
cd backend
python run.py
```

Environment variables are read from `backend/.env`. Ensure the following are set:
- `MONGO_URI` — Your MongoDB connection string
- `OPENROUTER_API_KEY` — Your API key for the LLM service
- `SECRET_KEY` — Secret key for Flask sessions
- `DEBUG` — Set to `True` for development, `False` for production
- `PORT` — Backend port (default: 5000)

## Kubernetes Deployment

Kubernetes manifests are available in the `k8s/` directory:

- `k8s/backend-deployment.yaml` — Deployment + Service for the backend (reads config from ConfigMap & Secrets)
- `k8s/mongo-redis.yaml` — Optional demo MongoDB and Redis deployments (for local clusters)
- `k8s/secrets-example.yaml` — Example secret manifest to store `OPENROUTER_API_KEY`, `SECRET_KEY`, `SENTRY_DSN` (use `kubectl create secret` or your platform's secret manager in production)

### Prerequisites

For Kubernetes deployment, you'll need to build and push your application image to a container registry. Install Docker or use your cloud provider's build service (e.g., AWS CodeBuild, Google Cloud Build).

Apply the manifests:

```bash
kubectl apply -f k8s/backend-deployment.yaml
# (optional) deploy demo mongodb & redis
kubectl apply -f k8s/mongo-redis.yaml
```

Create secrets (example):

```bash
kubectl create secret generic dietassist-secrets \
  --from-literal=OPENROUTER_API_KEY='your_key' \
  --from-literal=SECRET_KEY='your_flask_secret' \
  --from-literal=SENTRY_DSN='your_sentry_dsn'
```

### Backup and restore

- A sample backup script `scripts/mongo_backup.sh` is provided to create `mongodump` backups and optionally upload to S3 if `AWS_S3_BUCKET` is set.
- A Kubernetes CronJob is included at `k8s/backup-cronjob.yaml` which runs a scheduled `mongodump` and uploads archives to S3.
- For production, use scheduled backups with retention and offsite storage (S3, GCS) and test restores regularly.

### Persistent storage

- A sample `k8s/mongo-pvc.yaml` PersistentVolumeClaim is included for MongoDB persistence. Modify storage class and size as appropriate for your environment.
kubectl delete -f k8s/backend-deployment.yaml
kubectl delete -f k8s/mongo-redis.yaml
```
1. Install Heroku CLI and login
2. Create a Heroku app: `heroku create dietassist-app`
3. Set environment variables:
   - `heroku config:set MONGO_URI='your_mongo_uri' GEMINI_API_KEY='your_key'`
4. Push code: `git push heroku main`

Notes:
- Keep your `GEMINI_API_KEY` secret (use Heroku config vars or container secrets).
- Ensure you have a MongoDB add-on or external MongoDB accessible from the deployment environment.
