# TruePeopleSearch Scraper - VPS Deployment Guide

## Requirements
- Hostinger VPS (or any Ubuntu 20.04+ server)
- SSH access
- 4GB RAM minimum

---

## Step 1: SSH Into Your VPS

```bash
ssh root@YOUR_VPS_IP
```

---

## Step 2: Install Dependencies

```bash
# Update system
apt update && apt upgrade -y

# Install Python and required packages
apt install python3 python3-pip screen -y

# Install Firefox dependencies
apt install -y libgtk-3-0 libdbus-glib-1-2 libxt6 libx11-xcb1
```

---

## Step 3: Upload Project Files

Upload the project folder to your VPS:

```bash
# From your LOCAL PC (not SSH):
scp -r TruePeople root@YOUR_VPS_IP:/root/
```

Or use FileZilla/WinSCP to upload to `/root/TruePeople/`

---

## Step 4: Install Python Packages

```bash
cd /root/TruePeople

# Install dependencies
pip3 install -r requirements.txt

# Install Playwright Firefox
playwright install firefox
playwright install-deps firefox
```

---

## Step 5: Configure Proxy

Edit `.env` file with your proxy credentials:

```bash
nano .env
```

Replace with your actual credentials:
```
PROXY_HOST=residential.evomi.com
PROXY_PORT=3128
PROXY_USERNAME=your-username
PROXY_PASSWORD=your-password
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## Step 6: Run the Scraper

```bash
# Start a screen session (keeps running after disconnect)
screen -S scraper

# Run the scraper
python3 main.py
```

**Detach from screen:** Press `Ctrl+A`, then `D`

**Reconnect later:** 
```bash
screen -r scraper
```

---

## Step 7: Monitor Progress (Optional)

In a new SSH window:
```bash
cd /root/TruePeople
screen -S monitor
python3 monitor.py
```

---

## Checking Results

Results are saved to `leads.xlsx` Column C:

```bash
# Download updated file to your PC:
scp root@YOUR_VPS_IP:/root/TruePeople/leads.xlsx ./
```

---

## Common Commands

| Command | Purpose |
|---------|---------|
| `screen -r scraper` | Reconnect to scraper |
| `screen -r monitor` | Reconnect to monitor |
| `Ctrl+C` | Stop the script |
| `python3 main.py` | Restart scraper |

---

## Troubleshooting

**Script stopped?**
```bash
screen -r scraper
python3 main.py
```

**Check errors:**
```bash
ls errors/
```

**Restart from scratch:**
```bash
rm progress.json
python3 main.py
```

---

## Expected Timeline

| Leads | Time (2 workers) |
|-------|------------------|
| 1,000 | ~1 day |
| 10,000 | ~10 days |
| 50,000 | ~35-50 days |
