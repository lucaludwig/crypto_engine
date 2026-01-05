# ☁️ Cloud Deployment Guide - CADVI Auto-Trader

Deploy your auto-trader to run 24/7 in the cloud!

---

## 🚀 Quick Start (Recommended: DigitalOcean)

**Cost:** ~$6/month for basic VPS

### 1. Create DigitalOcean Account
- Go to [digitalocean.com](https://digitalocean.com)
- Sign up (get $200 free credit with referral)
- Click "Create" → "Droplets"

### 2. Configure Droplet
- **Image:** Ubuntu 22.04 LTS
- **Plan:** Basic ($6/month - 1GB RAM, 1 vCPU)
- **Datacenter:** Choose closest to you
- **Authentication:** SSH Key (recommended) or Password
- Click **Create Droplet**

### 3. Connect to Your Server
```bash
# Replace YOUR_SERVER_IP with your droplet IP
ssh root@YOUR_SERVER_IP
```

### 4. Install Docker
```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install docker-compose
apt install docker-compose -y

# Verify installation
docker --version
docker-compose --version
```

### 5. Upload Your Bot
```bash
# On your LOCAL machine (not server):
cd /Users/l.ludwig/Documents/Private/cadvi

# Upload files to server (replace YOUR_SERVER_IP)
scp -r . root@YOUR_SERVER_IP:/root/cadvi

# Or use git:
# git init
# git add .
# git commit -m "Initial commit"
# git push to your private repo
# Then on server: git clone YOUR_REPO
```

### 6. Deploy on Server
```bash
# On SERVER:
cd /root/cadvi

# Make deploy script executable
chmod +x deploy_cloud.sh

# Run deployment
./deploy_cloud.sh
```

### 7. Monitor Your Bot
```bash
# View live logs
docker-compose logs -f

# Check status
docker-compose ps

# Check portfolio
docker exec -it cadvi-auto-trader python monitor.py
```

---

## 🛡️ Security Setup (IMPORTANT!)

### Secure Your Server
```bash
# Create non-root user
adduser trader
usermod -aG sudo,docker trader

# Disable root SSH login
nano /etc/ssh/sshd_config
# Change: PermitRootLogin no
systemctl restart sshd

# Setup firewall
ufw allow 22/tcp
ufw enable
```

### Secure Your API Keys
```bash
# Ensure .env has correct permissions
chmod 600 .env

# Never commit .env to git!
echo ".env" >> .gitignore
```

---

## 📊 Monitoring Commands

### Check Bot Status
```bash
# Is it running?
docker-compose ps

# View recent logs
docker-compose logs --tail=50

# Live log stream
docker-compose logs -f

# Check portfolio
docker exec -it cadvi-auto-trader python monitor.py
```

### Manage Bot
```bash
# Stop trading
docker-compose down

# Start trading
docker-compose up -d

# Restart bot
docker-compose restart

# Update code and redeploy
git pull  # if using git
docker-compose down
docker-compose build
docker-compose up -d
```

---

## 💰 Cost Comparison

| Provider | Plan | RAM | Cost/Month | Free Tier |
|----------|------|-----|------------|-----------|
| **DigitalOcean** | Basic | 1GB | $6 | $200 credit |
| **AWS Lightsail** | Micro | 1GB | $5 | 3 months free |
| **Hetzner** | CX11 | 2GB | €4 (~$4.50) | None |
| **Linode** | Nanode | 1GB | $5 | $100 credit |
| **Vultr** | Regular | 1GB | $6 | $100 credit |

**Recommendation:** DigitalOcean (easy) or Hetzner (cheapest)

---

## 🔧 Alternative: AWS Lightsail (Also Easy)

### 1. Create Instance
- Go to [lightsail.aws.amazon.com](https://lightsail.aws.amazon.com)
- Click "Create instance"
- Choose Ubuntu 22.04 LTS
- Select $5/month plan
- Create instance

### 2. Connect & Deploy
```bash
# Download SSH key from Lightsail console
# Connect
ssh -i your-key.pem ubuntu@YOUR_INSTANCE_IP

# Follow same deployment steps as DigitalOcean
```

---

## 🆘 Troubleshooting

### Bot Not Starting
```bash
# Check logs for errors
docker-compose logs

# Check if .env exists
ls -la .env

# Rebuild container
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Out of Memory
```bash
# Add swap space
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### Check Bot Health
```bash
# CPU/Memory usage
docker stats cadvi-auto-trader

# Container info
docker inspect cadvi-auto-trader
```

---

## 📱 Next Steps (Optional)

After deployment, you can add:
1. **Telegram Notifications** - Get alerts on your phone
2. **Web Dashboard** - View portfolio in browser
3. **Automated Backups** - Backup trade logs daily
4. **Email Alerts** - Daily performance reports

---

## 🚨 Emergency Stop

If something goes wrong:
```bash
# Stop immediately
docker-compose down

# Check what happened
docker-compose logs

# Close all positions manually in Binance app
```

---

## ✅ Deployment Checklist

- [ ] Server created and running
- [ ] Docker installed
- [ ] Files uploaded to server
- [ ] .env file configured with API keys
- [ ] Bot deployed with `./deploy_cloud.sh`
- [ ] Logs checked - no errors
- [ ] Monitor script works
- [ ] Firewall configured
- [ ] Server secured (non-root user)
- [ ] Binance app ready for emergencies

---

**🎉 Congratulations! Your bot is now running 24/7 in the cloud!**

For support or questions, check the logs first:
```bash
docker-compose logs -f
```
