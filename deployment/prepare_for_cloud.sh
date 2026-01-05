#!/bin/bash
# Prepare CADVI bot for cloud deployment
# This script creates a clean deployment package

set -e

echo "========================================="
echo "CADVI - Prepare for Cloud Deployment"
echo "========================================="

# Create deployment directory
DEPLOY_DIR="cadvi_deploy_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEPLOY_DIR"

echo "📦 Creating deployment package in: $DEPLOY_DIR"

# Copy essential files only
echo "Copying files..."

# Core application files
cp -r api "$DEPLOY_DIR/"
cp auto_trader.py "$DEPLOY_DIR/"
cp requirements.txt "$DEPLOY_DIR/"
cp Dockerfile "$DEPLOY_DIR/"
cp docker-compose.yml "$DEPLOY_DIR/"

# Data files (empty templates)
echo '[]' > "$DEPLOY_DIR/trades_log.json"
echo '{}' > "$DEPLOY_DIR/position_metadata.json"
echo '{}' > "$DEPLOY_DIR/learnings.json"

# Documentation
cp README.md "$DEPLOY_DIR/" 2>/dev/null || true
cp ORACLE_CLOUD_SETUP.md "$DEPLOY_DIR/" 2>/dev/null || true

# Create .env template (user fills this in on cloud)
cat > "$DEPLOY_DIR/.env.example" << 'EOF'
# Binance API Credentials
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here

# Telegram Notifications (optional)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# CoinMarketCap API (optional, for enhanced data)
COINMARKETCAP_API_KEY=your_cmc_api_key_here
EOF

# Create quick start guide
cat > "$DEPLOY_DIR/QUICK_START.txt" << 'EOF'
===========================================
CADVI TRADING BOT - CLOUD DEPLOYMENT
===========================================

STEP 1: Copy .env.example to .env
----------------------------------------
cp .env.example .env
nano .env
(Add your actual API keys)

STEP 2: Build and start the bot
----------------------------------------
docker compose up -d

STEP 3: Check logs
----------------------------------------
docker logs -f cadvi-auto-trader

STEP 4: Stop the bot
----------------------------------------
docker compose down

===========================================
For detailed setup, see ORACLE_CLOUD_SETUP.md
===========================================
EOF

# Calculate package size
SIZE=$(du -sh "$DEPLOY_DIR" | cut -f1)

echo ""
echo "✅ Deployment package ready!"
echo "📦 Location: $DEPLOY_DIR"
echo "💾 Size: $SIZE"
echo ""
echo "========================================="
echo "NEXT STEPS:"
echo "========================================="
echo ""
echo "1. Upload to your cloud VM:"
echo "   scp -r $DEPLOY_DIR ubuntu@<VM_IP>:~/cadvi"
echo ""
echo "2. Or create a zip file:"
echo "   zip -r ${DEPLOY_DIR}.zip $DEPLOY_DIR"
echo ""
echo "3. Don't forget to:"
echo "   - Copy .env.example to .env on the cloud VM"
echo "   - Fill in your actual API keys"
echo "   - Run 'docker compose up -d'"
echo ""
echo "========================================="
echo ""
echo "Need detailed instructions? Read:"
echo "  • ORACLE_CLOUD_SETUP.md (recommended)"
echo "  • FREE_HOSTING_OPTIONS.md (all options)"
echo ""
