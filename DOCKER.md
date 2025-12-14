# SkinCheck - Docker Deployment Guide

## Prerequisites
- Docker installed (version 20.10+)
- Docker Compose installed (version 1.29+)

## Quick Start

### 1. Build and Run
```bash
# Build and start the container
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### 2. Access the Application
Open your browser and navigate to:
```
http://localhost:5000
```

## Docker Commands

### Build Only
```bash
docker-compose build
```

### Start Container
```bash
docker-compose up -d
```

### Stop Container
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f web
```

### Restart Container
```bash
docker-compose restart
```

### Rebuild After Code Changes
```bash
docker-compose up --build -d
```

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, edit `docker-compose.yml` and change:
```yaml
ports:
  - "8080:5000"  # Use port 8080 instead
```

### Container Won't Start
Check logs:
```bash
docker-compose logs web
```

### Reset Everything
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Production Deployment

For production, consider:
1. Using environment variables for secrets
2. Setting up reverse proxy (nginx)
3. Enabling HTTPS
4. Using Docker secrets for sensitive data
5. Setting resource limits in docker-compose.yml

## Health Check
The container includes a health check that verifies the app is running.
Check status:
```bash
docker-compose ps
```
