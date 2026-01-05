#!/bin/bash
# Oracle Cloud Deployment Script
# Run this ON YOUR ORACLE CLOUD VM after SSH'ing in

set -e

echo "========================================="
echo "CADVI Trading Bot - Oracle Cloud Setup"
echo "========================================="

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✓ Docker installed"
else
    echo "✓ Docker already installed"
fi

# Install Docker Compose plugin if not present
if ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
    echo "✓ Docker Compose installed"
else
    echo "✓ Docker Compose already installed"
fi

# Create app directory
mkdir -p ~/cadvi
cd ~/cadvi

echo ""
echo "========================================="
echo "NEXT STEPS:"
echo "========================================="
echo ""
echo "1. Copy your project files to this VM:"
echo "   On your LOCAL machine, run:"
echo "   scp -r /Users/l.ludwig/Documents/Private/cadvi/* ubuntu@<ORACLE_VM_IP>:~/cadvi/"
echo ""
echo "2. Create .env file with your Binance credentials:"
echo "   nano ~/cadvi/.env"
echo ""
echo "   Add these lines:"
echo "   BINANCE_API_KEY=your_key_here"
echo "   BINANCE_SECRET_KEY=your_secret_here"
echo "   TELEGRAM_BOT_TOKEN=your_token_here"
echo "   TELEGRAM_CHAT_ID=your_chat_id_here"
echo ""
echo "3. Start the bot:"
echo "   cd ~/cadvi"
echo "   docker compose up -d"
echo ""
echo "4. View logs:"
echo "   docker logs -f cadvi-auto-trader"
echo ""
echo "5. Stop the bot:"
echo "   docker compose down"
echo ""
echo "========================================="
