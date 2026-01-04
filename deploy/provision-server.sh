#!/bin/bash
#
# StorageHub Server Provisioning Script
# Run this from your laptop to set up a fresh server
#
set -e

# Configuration
SERVER_HOST="${STORAGEHUB_SERVER:-192.168.200.13}"
SERVER_USER="${STORAGEHUB_USER:-john}"
PROJECT_DIR="/opt/storagehub"

echo "=========================================="
echo "  StorageHub Server Provisioning"
echo "=========================================="
echo ""
echo "Server: ${SERVER_USER}@${SERVER_HOST}"
echo "Project directory: ${PROJECT_DIR}"
echo ""

# Check SSH access
echo "Checking SSH access..."
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "${SERVER_USER}@${SERVER_HOST}" "echo 'SSH OK'" 2>/dev/null; then
    echo ""
    echo "ERROR: Cannot connect to server via SSH."
    echo ""
    echo "Please set up SSH key access first:"
    echo "  ssh-copy-id ${SERVER_USER}@${SERVER_HOST}"
    echo ""
    exit 1
fi

echo "SSH access confirmed!"
echo ""

# Run provisioning on server
echo "Provisioning server..."
ssh "${SERVER_USER}@${SERVER_HOST}" bash << 'REMOTE_SCRIPT'
set -e

echo "==> Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

echo "==> Installing required packages..."
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    htop \
    ncdu

echo "==> Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh

    # Add current user to docker group
    sudo usermod -aG docker $USER
    echo "NOTE: You may need to log out and back in for docker group to take effect"
else
    echo "Docker already installed"
fi

echo "==> Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo apt-get install -y docker-compose-plugin
    # Also install standalone for compatibility
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose already installed"
fi

echo "==> Creating project directory..."
sudo mkdir -p /opt/storagehub
sudo chown $USER:$USER /opt/storagehub

echo "==> Creating data directories..."
sudo mkdir -p /opt/storagehub/data/{postgres,redis,uploads,backups}
sudo chown -R $USER:$USER /opt/storagehub/data

echo "==> Enabling Docker service..."
sudo systemctl enable docker
sudo systemctl start docker

echo ""
echo "==> Server provisioning complete!"
docker --version
docker-compose --version || docker compose version
REMOTE_SCRIPT

echo ""
echo "=========================================="
echo "  Provisioning Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Configure environment: cp deploy/.env.production.example deploy/.env.production"
echo "  2. Edit settings: nano deploy/.env.production"
echo "  3. Deploy: ./deploy/deploy.sh"
echo ""
