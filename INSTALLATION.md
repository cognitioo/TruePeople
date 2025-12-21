# TruePeopleSearch Scraper - Installation Guide

## Quick Start (Docker - Recommended)

### 1. Configure Proxy
Edit `.env` file with your proxy credentials:
```bash
PROXY_HOST=your-proxy-host.com
PROXY_PORT=33335
PROXY_USERNAME=your-username
PROXY_PASSWORD=your-password
```

### 2. Add Your Leads
Place `leads.xlsx` with:
- **Column B**: Address (required)
- **Column C**: "N/A" → will be replaced with phone numbers

### 3. Build & Run
```bash
docker build -t truepeoplesearch .
docker run -it --rm -v $(pwd):/app truepeoplesearch
```

Done! Phone numbers will be written to **Column C** of `leads.xlsx`.

---

## Manual Installation (VPS/Local)

### 1. Install Python 3.10+
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip -y
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
playwright install firefox
playwright install-deps firefox
```

### 3. Run
```bash
python main.py
```

---

## Monitoring (Optional)
```bash
python monitor.py
```

---

## Files
| File | Purpose |
|------|---------|
| `main.py` | Auto-restart wrapper |
| `truepeoplesearch_firefox.py` | Main scraper |
| `monitor.py` | Real-time dashboard |
| `leads.xlsx` | Input/Output - Column C gets phone numbers |
| `.env` | Proxy credentials |

---

## Proxy Providers

| Provider | Host | Port | Cost |
|----------|------|------|------|
| **Evomi** | residential.evomi.com | 3128 | $0.49/GB |
| **BrightData** | brd.superproxy.io | 33335 | $15/GB |
| **Oxylabs** | pr.oxylabs.io | 7777 | $8/GB |
