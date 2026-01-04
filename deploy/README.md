# StorageHub Deployment Guide

## Overview

This guide sets up a development workflow where you:
- Develop and prototype on your laptop
- Deploy to production server (192.168.200.13) with a single command

## Quick Start

Once everything is set up, deploying is as simple as:
```bash
./deploy/deploy.sh
```

---

## Initial Setup (One-Time)

### Step 1: Set Up SSH Key Access

On your laptop, run:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "storagehub-deploy"

# Copy your public key to the server (you'll need the server password)
ssh-copy-id john@192.168.200.13

# Test the connection (should not ask for password)
ssh john@192.168.200.13 "echo 'SSH key access working!'"
```

### Step 2: Provision the Server

Run the provisioning script from your laptop:

```bash
./deploy/provision-server.sh
```

This installs Docker, Docker Compose, and sets up the project directory on the server.

### Step 3: Configure Environment

Copy and edit the production environment file:

```bash
cp deploy/.env.production.example deploy/.env.production
nano deploy/.env.production  # Edit with your settings
```

Important settings to configure:
- `SECRET_KEY` - Generate a secure random key
- `OPENAI_API_KEY` - For AI features
- Domain/SSL settings if using HTTPS

### Step 4: Initial Deployment

```bash
./deploy/deploy.sh
```

---

## Daily Workflow

### Development (Laptop)

```bash
# Start local development
docker-compose up

# Make changes, test locally
# Commit when ready
git add . && git commit -m "feat: My new feature"
git push
```

### Deploy to Production

```bash
# From your laptop - deploys latest code to server
./deploy/deploy.sh

# Optional: View server logs
./deploy/logs.sh

# Optional: SSH to server
ssh john@192.168.200.13
```

---

## Useful Commands

```bash
# Deploy to production
./deploy/deploy.sh

# View production logs
./deploy/logs.sh

# View specific service logs
./deploy/logs.sh backend
./deploy/logs.sh celery

# Restart production services
./deploy/restart.sh

# SSH to production server
ssh john@192.168.200.13

# Run database migrations on production
./deploy/migrate.sh

# Backup production database
./deploy/backup.sh
```

---

## Troubleshooting

### SSH Connection Refused
```bash
# Check if SSH is running on server
ssh john@192.168.200.13 "sudo systemctl status ssh"
```

### Docker Permission Denied
```bash
# On server, add user to docker group
sudo usermod -aG docker $USER
# Then logout and login again
```

### Container Won't Start
```bash
# Check logs
./deploy/logs.sh

# Rebuild containers
./deploy/deploy.sh --build
```
