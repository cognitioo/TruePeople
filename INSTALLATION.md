# VPS Deployment Guide (CyberPanel + Hostinger)

This guide explains how to deploy the TruePeopleSearch Scraper on a VPS with CyberPanel.

## Prerequisites
- VPS with CyberPanel installed (Hostinger or similar)
- SSH access to your server
- 4GB RAM minimum
- Proxy account (Evomi, BrightData, etc.)

---

## Step 1: Connect via SSH

Open terminal/PowerShell and connect:

```bash
ssh root@your-server-ip
```

---

## Step 2: Install System Dependencies

```bash
# Update package list
apt update && apt upgrade -y

# Install Python 3 and required packages
apt install python3 python3-pip python3-venv screen -y

# Install Firefox browser dependencies
apt install -y wget gnupg libglib2.0-0 libnss3 libnspr4 libdbus-1-3 \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libcairo2 libgtk-3-0 libxt6 libx11-xcb1

# Install supervisor (to keep the app running 24/7)
apt install supervisor -y
```

---

## Step 3: Create Project Directory

```bash
mkdir -p /root/TruePeople
cd /root/TruePeople
```

---

## Step 4: Upload Project Files

Upload these files to `/root/TruePeople/`:

```
TruePeople/
├── main.py
├── monitor.py
├── truepeoplesearch_firefox.py
├── requirements.txt
├── .env
├── leads.xlsx          (your input file)
└── Dockerfile          (optional)
```

**Upload methods:**

1. **SFTP (FileZilla/WinSCP):**
   - Connect to `root@your-server-ip`
   - Navigate to `/root/TruePeople/`
   - Upload all files

2. **SCP (from your PC):**
```bash
scp -r TruePeople/* root@your-server-ip:/root/TruePeople/
```

3. **CyberPanel File Manager:**
   - Upload to `/root/TruePeople/`

---

## Step 5: Create Virtual Environment

```bash
cd /root/TruePeople

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright Firefox browser
playwright install firefox
playwright install-deps firefox
```

---

## Step 6: Configure Proxy (.env file)

```bash
nano .env
```

Add your proxy credentials:
```
PROXY_HOST=residential.evomi.com
PROXY_PORT=3128
PROXY_USERNAME=your-proxy-username
PROXY_PASSWORD=your-proxy-password
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## Step 7: Test the Application

```bash
cd /root/TruePeople
source venv/bin/activate
python3 main.py
```

You should see:
```
🚀 UNBREAKABLE SCRAPER - Auto-Restart Wrapper
📅 Started: 2024-12-21 20:00:00
🔧 Script: truepeoplesearch_firefox.py
```

Press `Ctrl+C` to stop testing.

---

## Step 8: Configure Supervisor (Auto-start 24/7)

Create a supervisor config file:

```bash
nano /etc/supervisor/conf.d/truepeoplesearch.conf
```

Add this content:
```ini
[program:truepeoplesearch]
command=/root/TruePeople/venv/bin/python3 main.py
directory=/root/TruePeople
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/truepeoplesearch.err.log
stdout_logfile=/var/log/truepeoplesearch.out.log
environment=DISPLAY=":99"
```

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

Reload supervisor:
```bash
supervisorctl reread
supervisorctl update
supervisorctl start truepeoplesearch
```

Check status:
```bash
supervisorctl status truepeoplesearch
```

You should see:
```
truepeoplesearch                 RUNNING   pid 12345, uptime 0:00:10
```

---

## Step 9: Monitor Progress (Optional)

Open a new SSH session and run:

```bash
cd /root/TruePeople
source venv/bin/activate
python3 monitor.py
```

Or check the logs:
```bash
tail -f /var/log/truepeoplesearch.out.log
```

---

## Step 10: Download Results

When complete (or to check progress), download the updated leads.xlsx:

```bash
# From your LOCAL PC:
scp root@your-server-ip:/root/TruePeople/leads.xlsx ./
```

Results are in **Column C** (phone numbers replace N/A).

---

## Troubleshooting

### Check Logs
```bash
# Application output
tail -f /var/log/truepeoplesearch.out.log

# Error logs
tail -f /var/log/truepeoplesearch.err.log

# Supervisor status
supervisorctl status
```

### Common Commands
```bash
# Restart scraper
supervisorctl restart truepeoplesearch

# Stop scraper
supervisorctl stop truepeoplesearch

# Start scraper
supervisorctl start truepeoplesearch

# View live output
tail -f /var/log/truepeoplesearch.out.log
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Script not starting | Check logs: `tail -f /var/log/truepeoplesearch.err.log` |
| "No module named..." | Activate venv: `source venv/bin/activate` then `pip install -r requirements.txt` |
| Firefox errors | Run: `playwright install-deps firefox` |
| Proxy errors | Check `.env` file has correct credentials |
| Permission denied | Run as root or fix permissions |

### Restart from Scratch
```bash
cd /root/TruePeople
rm progress.json
supervisorctl restart truepeoplesearch
```

---

## File Structure on Server

```
/root/TruePeople/
├── main.py                      # Auto-restart wrapper
├── truepeoplesearch_firefox.py  # Main scraper
├── monitor.py                   # Progress dashboard
├── requirements.txt             # Python dependencies
├── .env                         # Proxy credentials
├── leads.xlsx                   # Input/Output file
├── progress.json                # Progress tracking
├── venv/                        # Virtual environment
└── errors/                      # Error screenshots
```

---

## Expected Timeline

| Leads | Time (2 workers) |
|-------|------------------|
| 1,000 | ~1 day |
| 10,000 | ~10 days |
| 50,000 | ~35-50 days |

---

## Support

If you encounter issues:

1. Check the logs: `tail -f /var/log/truepeoplesearch.err.log`
2. Verify supervisor status: `supervisorctl status`
3. Check error screenshots: `ls /root/TruePeople/errors/`
4. Contact your developer for script-related issues
