# VPS Installation Guide - Hostinger + CyberPanel

## Server Requirements

- **VPS**: Hostinger VPS
- **Control Panel**: CyberPanel
- **OS**: Ubuntu 20.04/22.04 (recommended)
- **RAM**: 8GB minimum (for 2-4 workers)
- **Storage**: 20GB minimum
- **Python**: 3.10 or higher

---

## Step 1: Connect to VPS via SSH

```bash
ssh root@your-vps-ip
```

Enter your password when prompted.

---

## Step 2: Install Python 3.10+ and Dependencies

### Check Python Version
```bash
python3 --version
```

If Python 3.10+, skip to Step 3. Otherwise:

### Install Python 3.10
```bash
apt update
apt install -y software-properties-common
add-apt-repository ppa:deadsnakes/ppa
apt update
apt install -y python3.10 python3.10-venv python3-pip
```

### Set Python 3.10 as default
```bash
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
```

---

## Step 3: Install System Dependencies

```bash
apt install -y wget curl git
```

---

## Step 4: Install Playwright Dependencies

```bash
# Install browser dependencies
apt install -y \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2
```

---

## Step 5: Create Project Directory

```bash
cd /home
mkdir scraper
cd scraper
```

---

## Step 6: Upload Project Files

### Option A: From GitHub (Recommended)
```bash
git clone https://github.com/cognitioo/TruePeople.git .
```

### Option B: Manual Upload (if no GitHub)
Use SFTP/SCP to upload these files:
- `truepeoplesearch_firefox.py`
- `main.py`
- `monitor.py`
- `requirements.txt`
- `.env`
- `leads.xlsx`

Example using SCP from local machine:
```bash
scp -r /path/to/Web-scrapping/* root@your-vps-ip:/home/scraper/
```

---

## Step 7: Create Python Virtual Environment

```bash
cd /home/scraper
python3 -m venv venv
source venv/bin/activate
```

---

## Step 8: Install Python Requirements

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 9: Install Playwright Browsers

```bash
playwright install firefox
playwright install-deps firefox
```

---

## Step 10: Configure Proxy Settings

Edit the `.env` file:
```bash
nano .env
```

Add your BrightData credentials:
```
PROXY_HOST=brd.superproxy.io
PROXY_PORT=33335
PROXY_USERNAME=your-username-here
PROXY_PASSWORD=your-password-here
```

Save with `Ctrl+X`, then `Y`, then `Enter`.

---

## Step 11: Prepare Input File

Upload your `leads.xlsx` file with addresses:
```bash
# If using SCP from local machine:
scp leads.xlsx root@your-vps-ip:/home/scraper/
```

Verify file exists:
```bash
ls -lh leads.xlsx
```

---

## Step 12: Test Run (Verify Everything Works)

```bash
cd /home/scraper
source venv/bin/activate
python truepeoplesearch_firefox.py
```

Press `Ctrl+C` after 1-2 addresses complete successfully.

---

## Step 13: Run in Background (Production Mode)

### Using `screen` (Recommended)

#### Install screen
```bash
apt install -y screen
```

#### Start scraper in screen
```bash
cd /home/scraper
source venv/bin/activate
screen -S scraper
python main.py
```

#### Detach from screen
Press `Ctrl+A`, then `D`

#### Reattach to see progress
```bash
screen -r scraper
```

#### Monitor in separate screen
```bash
screen -S monitor
cd /home/scraper
source venv/bin/activate
python monitor.py
```
Press `Ctrl+A`, then `D` to detach.

#### List all screens
```bash
screen -ls
```

---

## Step 14: Enable Auto-Start on Reboot (Optional)

Create systemd service:

```bash
nano /etc/systemd/system/scraper.service
```

Add:
```ini
[Unit]
Description=TruePeopleSearch Scraper
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/scraper
Environment="PATH=/home/scraper/venv/bin"
ExecStart=/home/scraper/venv/bin/python /home/scraper/main.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

Save and enable:
```bash
systemctl daemon-reload
systemctl enable scraper
systemctl start scraper
```

Check status:
```bash
systemctl status scraper
```

View logs:
```bash
journalctl -u scraper -f
```

---

## Monitoring Your Scraper

### View Progress
```bash
cd /home/scraper
cat progress.json
```

### View Stats
```bash
cat monitoring_stats.json
```

### Real-Time Dashboard
```bash
cd /home/scraper
source venv/bin/activate
python monitor.py
```

### Download Results
From your local machine:
```bash
scp root@your-vps-ip:/home/scraper/output.xlsx ./
```

---

## Troubleshooting

### Check if script is running
```bash
ps aux | grep python
```

### Check memory usage
```bash
free -h
```

### Check disk space
```bash
df -h
```

### View error screenshots
```bash
ls -lh /home/scraper/errors/
```

Download screenshots to local machine:
```bash
scp root@your-vps-ip:/home/scraper/errors/*.png ./
```

### Restart scraper
```bash
# If using screen:
screen -r scraper
# Press Ctrl+C
python main.py

# If using systemd:
systemctl restart scraper
```

---

## Performance Optimization

### Increase Workers (if you have enough RAM)

Edit `truepeoplesearch_firefox.py`:
```bash
nano truepeoplesearch_firefox.py
```

Find line ~60:
```python
PARALLEL_WORKERS = 2  # Change to 4 or 6
```

**RAM Requirements**:
- 2 workers = 4-6GB RAM
- 4 workers = 8-12GB RAM
- 6 workers = 12-16GB RAM

---

## Security Best Practices

### 1. Change SSH port
```bash
nano /etc/ssh/sshd_config
# Change Port 22 to Port 2222
systemctl restart sshd
```

### 2. Enable firewall
```bash
ufw allow 2222/tcp  # Or your SSH port
ufw enable
```

### 3. Regular backups
```bash
# Backup results daily
crontab -e

# Add:
0 0 * * * cp /home/scraper/output.xlsx /home/scraper/backups/output_$(date +\%Y\%m\%d).xlsx
```

---

## Cost Estimates

### Hostinger VPS Pricing
- **VPS 1** (4GB RAM): ~$10/month - Good for 2 workers
- **VPS 2** (8GB RAM): ~$20/month - Good for 4 workers
- **VPS 3** (12GB RAM): ~$30/month - Good for 6 workers

### Proxy Costs (50k Leads)

**Residential Proxy** ($15/GB):
- Per address: ~3-5 MB
- 50k addresses: ~150-250 GB
- **Cost**: $2,250-$3,750

**Datacenter Proxy** ($0.49/GB):
- Same usage: 150-250 GB
- **Cost**: $73.50-$122.50
- **Savings**: ~$2,100-$3,600!

> **Recommendation**: Use datacenter proxies if TruePeopleSearch allows. Much cheaper!

---

## Expected Timeline (50k Leads)

| Workers | Addresses/Day | Total Days | VPS Cost | Proxy Cost (DC) |
|---------|---------------|------------|----------|-----------------|
| 2 | ~1,200 | 42 days | $20-40 | $73-122 |
| 4 | ~2,400 | 21 days | $40-60 | $73-122 |
| 6 | ~3,600 | 14 days | $60-90 | $73-122 |

**Total Project Cost** (50k leads with 4 workers):
- VPS: $40-60
- Proxy: $73-122
- **Total**: $113-182

---

## Support Checklist

Before running 50k leads, verify:

- [ ] VPS has enough RAM (8GB for 4 workers)
- [ ] Proxy credentials are correct
- [ ] `leads.xlsx` has all 50k addresses
- [ ] Test run completed successfully (1-2 addresses)
- [ ] Screen session is working
- [ ] Monitor dashboard shows progress
- [ ] Error screenshots folder is accessible
- [ ] Backup strategy is in place

---

## Quick Reference Commands

```bash
# Start scraper
cd /home/scraper && source venv/bin/activate && screen -S scraper
python main.py

# Monitor progress
screen -S monitor
python monitor.py

# Check progress file
cat /home/scraper/progress.json

# Download results NOW
# (Run from local machine)
scp root@your-vps-ip:/home/scraper/output.xlsx ./

# Restart if hung
screen -r scraper
# Ctrl+C
python main.py
```

---

**Your scraper is now ready to run 24/7 on VPS!** 🚀

For support, check error screenshots in `/home/scraper/errors/`
