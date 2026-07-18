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
ssh-copy-id user@192.168.200.13

# Test the connection (should not ask for password)
ssh user@192.168.200.13 "echo 'SSH key access working!'"
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

**Required** (compose refuses to start without them — `${VAR:?...}` interpolation):
- `SECRET_KEY` — generate with `openssl rand -hex 32` (or `just genkey`)
- `POSTGRES_PASSWORD` — any strong password

Optional but recommended:
- `OPENAI_API_KEY` — pre-fills the wizard's AI step. You can also paste it
  during onboarding or set it later under Admin → AI Settings.
- `FRONTEND_URL` — public URL where users will reach the app, used for QR
  codes and share links.
- `CORS_ORIGINS` — comma-separated additional origins (e.g. LAN IP plus a
  domain name).

### Step 4: Initial Deployment

```bash
./deploy/deploy.sh
```

### Step 5: Run the Setup Wizard

Open `https://192.168.200.13` in a browser. With an empty database the app
detects this is a fresh install and redirects you to `/setup`. The wizard
walks you through:

1. Creating the admin account (email + password are required — admins sign
   in via "Administer this instance" on the login screen, not the household
   card grid).
2. Pasting an OpenAI API key (optional; persisted in the database, can be
   rotated later in Admin → AI Settings).
3. Picking the languages the AI generates content in (defaults to `en, no`).
4. Adding your first storage location (optional).

After "Open StorageHub" you're already logged in.

> **Note:** The first time you visit, your browser will warn about the
> self-signed certificate. nginx generates one automatically on first boot
> so HTTPS works out of the box. Click "Advanced" and "Proceed". For a real
> domain you can later replace the cert via the SSL admin panel (custom
> upload or Let's Encrypt through the bundled certbot service).

---

## Daily Workflow

### Development (Laptop)

```bash
# Start local development (the justfile at the repo root wraps the most
# common operations — see `just --list`)
just up
just logs backend       # tail logs for one service
just check              # frontend type checks before committing

# .githooks/pre-commit runs `just check` automatically on staged frontend
# changes. Enable it once per clone:
just install-hooks

# Commit and push as usual
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
ssh user@192.168.200.13
```

---

## Useful Commands

```bash
# Deploy to production
./deploy/deploy.sh

# Deploy with database migrations (after schema changes)
./deploy/deploy.sh --migrate

# View production logs
./deploy/logs.sh

# View specific service logs
./deploy/logs.sh backend
./deploy/logs.sh celery

# Restart production services
./deploy/restart.sh

# SSH to production server
ssh user@192.168.200.13

# Run database migrations on production
./deploy/migrate.sh

# Backup production database
./deploy/backup.sh

# Create an additional user from the CLI (the first admin is created by
# the in-app /setup wizard; this script is for adding more users later)
./deploy/create-admin.sh "Name" "email@example.com" "password"
```

---

## Backups

### Built-in Backup System

StorageHub has a built-in backup system accessible from the Admin panel:

1. Go to **Admin → Backups** in the web interface
2. Click **Create Backup** for manual backups
3. Configure automatic backups with retention policies
4. Optionally enable Google Drive sync for off-site storage

### Manual Database Backup (CLI)

```bash
# Create a database dump (runs pg_dump on the server over SSH)
./deploy/backup.sh

# Backups are saved on your LOCAL machine in ./backups
# as storagehub_<timestamp>.sql.gz
```

> **Warning:** `backup.sh` backs up the **database only**. Uploaded photos
> (the `uploads_data` Docker volume on the server) are NOT included — back
> those up separately if you need them.

### Restoring from Backup

Use the Admin panel to restore from any backup, or manually. Backups are
gzipped SQL dumps, so restore them with `psql` (not `pg_restore`):

```bash
# From your laptop — pipe the local backup into postgres on the server
gunzip -c backups/storagehub_YYYYMMDD_HHMMSS.sql.gz | \
  ssh user@192.168.200.13 "cd /opt/storagehub && docker compose exec -T postgres psql -U storagehub storagehub"

# Or, if the backup file is already on the server:
gunzip -c backups/<file>.sql.gz | docker compose exec -T postgres psql -U storagehub storagehub
```

---

## Troubleshooting

### SSH Connection Refused
```bash
# Check if SSH is running on server
ssh user@192.168.200.13 "sudo systemctl status ssh"
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
