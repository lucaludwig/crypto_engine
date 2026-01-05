#!/bin/bash
# CADVI Auto-Trader - Cloud Deployment Script

set -e

echo "=================================================="
echo "CADVI AUTO-TRADER - CLOUD DEPLOYMENT"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found!"
    echo "Create .env with your API keys first:"
    echo ""
    echo "CMC_API_KEY=your_coinmarketcap_key"
    echo "BINANCE_API_KEY=your_binance_key"
    echo "BINANCE_SECRET_KEY=your_binance_secret"
    echo ""
    exit 1
fi

echo "✓ .env file found"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ ERROR: Docker not installed!"
    echo "Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✓ Docker installed"
echo ""

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ ERROR: docker-compose not installed!"
    echo "Install docker-compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ docker-compose installed"
echo ""

# Stop existing container if running
echo "Stopping existing container (if any)..."
docker-compose down 2>/dev/null || true
echo ""

# Build and start
echo "Building Docker image..."
docker-compose build
echo ""

echo "Starting CADVI Auto-Trader..."
docker-compose up -d
echo ""

# Show status
echo "=================================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=================================================="
echo ""
echo "Status:"
docker-compose ps
echo ""
echo "Commands:"
echo "  View logs:        docker-compose logs -f"
echo "  Stop trader:      docker-compose down"
echo "  Restart trader:   docker-compose restart"
echo "  Check status:     docker-compose ps"
echo ""
echo "🚀 Your auto-trader is now running 24/7!"
echo ""
