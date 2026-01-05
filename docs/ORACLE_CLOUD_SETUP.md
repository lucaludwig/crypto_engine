# Oracle Cloud Free Tier Setup Guide

Deploy your CADVI trading bot 24/7 for **FREE FOREVER** on Oracle Cloud.

## Why Oracle Cloud?

- ✅ **Truly Free Forever** - No credit card charges
- ✅ **Generous Resources** - 4 ARM CPUs + 24GB RAM
- ✅ **24/7 Uptime** - Perfect for trading bots
- ✅ **No Sleep** - Unlike Render/Railway

---

## Step 1: Create Oracle Cloud Account

1. Go to https://cloud.oracle.com/
2. Click **"Start for free"**
3. Fill in your details (credit card required but **won't be charged**)
4. Verify your email and phone

---

## Step 2: Create a VM Instance

1. **Log in** to Oracle Cloud Console
2. Click **"Create a VM Instance"** (big blue button)

3. **Configure the instance:**
   - **Name**: `cadvi-trading-bot`
   - **Image**: `Ubuntu 22.04 (Canonical)`
   - **Shape**:
     - Click "Change Shape"
     - Select **"Ampere" (ARM-based)**
     - Choose **VM.Standard.A1.Flex**
     - Set **OCPUs: 2** and **Memory: 12 GB**

4. **Networking:**
   - Use default VCN (Virtual Cloud Network)
   - ✅ Check "Assign a public IPv4 address"

5. **SSH Keys:**
   - Download the private key (`.key` file) - **SAVE THIS!**
   - Or use your own SSH public key

6. Click **"Create"**

7. **Wait 2-3 minutes** for instance to provision

8. **Note down the Public IP address** (you'll need it)

---

## Step 3: Configure Firewall (Security List)

By default, Oracle blocks most ports. We don't need to open any for the bot, but if you want to add a web dashboard later:

1. Go to **Networking** → **Virtual Cloud Networks**
2. Click your VCN → **Security Lists** → **Default Security List**
3. Click **"Add Ingress Rules"**
4. Add rule: **Source CIDR**: `0.0.0.0/0`, **Destination Port**: `80,443`

---

## Step 4: Connect to Your VM

### On Mac/Linux:
```bash
# Make the key file secure
chmod 600 ~/Downloads/ssh-key-*.key

# Connect to your VM
ssh -i ~/Downloads/ssh-key-*.key ubuntu@<YOUR_PUBLIC_IP>
```

### On Windows:
Use **PuTTY** or **Windows Terminal** with the private key.

---

## Step 5: Install Docker

Once connected to your VM, run:

```bash
# Download and run the deployment script
curl -fsSL https://raw.githubusercontent.com/docker/docker-install/master/install.sh -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo apt-get update
sudo apt-get install -y docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

**Important**: Log out and log back in for docker group to take effect:
```bash
exit
# Then SSH back in
```

---

## Step 6: Upload Your Bot

### Option A: Direct SCP (from your Mac)

```bash
# From your local machine (Mac):
cd /Users/l.ludwig/Documents/Private/cadvi

# Upload all files (replace <VM_IP> with your Oracle VM's public IP)
scp -i ~/Downloads/ssh-key-*.key -r ./* ubuntu@<VM_IP>:~/cadvi/
```

### Option B: Git Clone (if using GitHub)

```bash
# On the Oracle VM:
cd ~
git clone https://github.com/your-username/cadvi.git
cd cadvi
```

---

## Step 7: Create .env File

```bash
# On the Oracle VM:
cd ~/cadvi
nano .env
```

Add your credentials:
```bash
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## Step 8: Deploy the Bot

```bash
cd ~/cadvi

# Start the bot
docker compose up -d

# Check if it's running
docker ps

# View logs
docker logs -f cadvi-auto-trader

# Press Ctrl+C to exit logs (bot keeps running)
```

---

## Step 9: Verify It's Working

You should see:
```
================================================================================
CADVI AUTO TRADER
LIVE TRADING MODE 🔴
================================================================================

Connecting to Binance... ✓
🧠 Initializing Learning Engine... ✓
📊 Initializing Position Monitor... ✓
```

Check Telegram - you should receive a startup notification!

---

## Useful Commands

```bash
# View live logs
docker logs -f cadvi-auto-trader

# Stop the bot
docker compose down

# Restart the bot
docker compose restart

# Update the bot (after making changes)
docker compose down
docker compose build --no-cache
docker compose up -d

# Check disk space
df -h

# Check memory usage
free -h

# View running processes
docker ps
```

---

## Auto-Start on Reboot

Make the bot start automatically if the VM reboots:

```bash
# Enable Docker to start on boot
sudo systemctl enable docker

# The docker-compose.yml already has "restart: unless-stopped"
# So your bot will auto-restart
```

---

## Monitor Your Bot Remotely

### Option 1: SSH from anywhere
```bash
ssh -i ~/Downloads/ssh-key-*.key ubuntu@<VM_IP>
docker logs -f cadvi-auto-trader
```

### Option 2: Telegram Notifications
Your bot sends all updates to Telegram - just check your phone! 📱

---

## Troubleshooting

### Bot not starting?
```bash
# Check logs for errors
docker logs cadvi-auto-trader

# Check if .env file exists
cat .env

# Rebuild if needed
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Can't SSH?
- Check your Security List allows SSH (port 22)
- Verify you're using the correct private key
- Check the public IP is correct

### Out of disk space?
```bash
# Clean up old Docker images
docker system prune -a

# Check space
df -h
```

---

## Cost Breakdown

- **VM Instance**: $0/month (Always Free ARM instance)
- **Storage**: $0/month (up to 200GB included)
- **Network**: $0/month (10TB outbound included)
- **Total**: **$0/month** ✅

---

## Security Best Practices

1. **Never share your SSH private key**
2. **Keep .env file secure** (has API keys)
3. **Enable 2FA** on Oracle Cloud account
4. **Whitelist your IP** in Binance API settings
5. **Use read-only API keys** if possible (for monitoring)

---

## Next Steps

Your bot is now running 24/7 in the cloud! 🎉

- Monitor via Telegram notifications
- Check logs via SSH when needed
- Bot will automatically:
  - Monitor positions
  - Apply trailing stops
  - Take partial profits
  - Learn from exits
  - Find new opportunities

**Pro Tip**: Set up a cron job to backup `trades_log.json` and `position_metadata.json` daily:

```bash
# On Oracle VM:
crontab -e

# Add this line (backs up to ~/backups daily at 3am):
0 3 * * * mkdir -p ~/backups && cp ~/cadvi/*.json ~/backups/backup-$(date +\%Y\%m\%d).json
```

---

**Need Help?**
- Oracle Cloud docs: https://docs.oracle.com/en-us/iaas/
- Docker docs: https://docs.docker.com/
