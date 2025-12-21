# TruePeopleSearch Scraper - Documentation

## Overview
This bot scrapes phone numbers from TruePeopleSearch.com using residential proxies and parallel processing. It's designed for **stability** over speed, with human-like behavior to avoid detection.

---

## Features

### ✅ Parallel Processing
- Runs **2 browser instances** simultaneously
- Each worker processes different addresses
- Automatic staggered start (10-15s delay between workers)

### ✅ Resume Capability
- Saves progress after each address
- Automatically skips completed addresses on restart
- Safe to stop/start anytime

### ✅ Anti-Detection
- **Cloudflare bypass** - Waits up to 90 seconds for challenges
- **CAPTCHA recovery** - Attempts 30-45 second cooldown when blocked
- **Human-like behavior** - Random delays, mouse movements, realistic typing
- **Proxy rotation** - New IP session every 3 addresses

### ✅ Robust Error Handling
- Multiple click attempts (normal → force → JavaScript → direct navigation)
- Page health checks after each action
- Automatic recovery from temporary blocks
- Thread-safe Excel updates

---

## Performance Metrics

### Current Configuration (2 Workers)

| Metric | Value |
|--------|-------|
| **Addresses per hour** | ~40-60 |
| **Addresses per day (24h)** | **~1,000-1,500** |
| **Time per address** | ~60-90 seconds |
| **Batch size** | 3 addresses per IP session |

### Time Breakdown Per Address
- Page load + Cloudflare wait: 10-20s
- Form filling: 8-15s
- Search results: 5-10s
- Profile navigation: 8-12s
- Phone extraction: 3-5s
- **Total: ~60-90 seconds**

### Scaling Options

| Workers | Per Day | Time for 50k Leads |
|---------|---------|-------------------|
| 2 (current) | ~1,000-1,500 | 33-50 days |
| 4 | ~2,000-3,000 | 17-25 days |
| 6 | ~3,000-4,500 | 11-17 days |

> **Note**: More workers require more RAM (2GB per worker) and may increase proxy costs.

---

## Files

### Main Script
- `truepeoplesearch_firefox.py` - The scraper

### Configuration
- `.env` - Proxy credentials (DO NOT SHARE)
- `requirements.txt` - Python dependencies

### Data Files
- `leads.xlsx` - **INPUT**: Addresses to scrape
- `output.xlsx` - **OUTPUT**: Scraped results
- `progress.json` - Resume checkpoint

### Folders
- `errors/` - Screenshots for debugging
- `recourses/` - Reference files

---

## Setup

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
playwright install firefox
```

### 2. Configure Proxy
Edit `.env` file:
```
PROXY_HOST=brd.superproxy.io
PROXY_PORT=33335
PROXY_USERNAME=your-username-here
PROXY_PASSWORD=your-password-here
```

### 3. Prepare Input File
- Open `leads.xlsx`
- Column A: Full name (optional)
- **Column B**: Address (REQUIRED)
  - Format: `Street, City, State ZIP`
  - Example: `91 Liberty St, Rockland, MA 02370`
- Column C: Phone (will be filled by bot)

---

## Usage

### Start the Bot
```bash
python truepeoplesearch_firefox.py
```

### Stop the Bot
- Press `Ctrl+C` in terminal
- Progress is auto-saved

### Resume After Stop
- Just run the command again
- Bot automatically skips completed addresses

### View Progress
```bash
cat progress.json
```

---

## Understanding the Output

### Terminal Output
```
🦊 [Worker 1] Starting browser session...
📍 Searching: 91 Liberty St, Rockland, MA 02370
  ✅ SUCCESS!
     Phone: (339) 788-2182
     💾 Progress saved: 15 completed
```

### Excel Output (`output.xlsx`)
| Address | Name | Age | Phone | Profile URL | Status |
|---------|------|-----|-------|-------------|--------|
| 91 Liberty St... | John Smith | 45 | (339) 788-2182 | https://... | FOUND |

### Status Meanings
- **FOUND** ✅ - Phone number extracted
- **NO_PHONE** ℹ️ - Profile found but no phone
- **NO_PROFILES** ℹ️ - No matching profile
- **BLOCKED** ⛔ - CAPTCHA/Cloudflare block
- **ERROR** ❌ - Scraping error

---

## Configuration Settings

Edit these in `truepeoplesearch_firefox.py`:

### Parallel Workers
```python
PARALLEL_WORKERS = 2  # Number of browsers (2-6 recommended)
```

### Batch Size
```python
BATCH_SIZE = 3  # Addresses per IP session
```

### Speed vs Stability
```python
# Current (STABLE):
DELAY_MIN = 4.0
DELAY_MAX = 7.0

# Faster (RISKY):
DELAY_MIN = 2.0
DELAY_MAX = 4.0
```

---

## Troubleshooting

### "BLOCKED" Errors
**Cause**: Too many requests, CAPTCHA triggered  
**Solution**: Bot auto-recovers after 30-45s cooldown

### "Address input error"
**Cause**: Page not fully loaded  
**Solution**: Already has 3 retry attempts with different methods

### Browser Crashes
**Cause**: Memory issues  
**Solution**: Reduce `PARALLEL_WORKERS` to 1

### Proxy Errors
**Cause**: Invalid credentials or no residential access  
**Solution**: Contact BrightData for KYC verification

---

## Proxy Cost Estimation

### BrightData Residential Pricing
- **Cost**: ~$15/GB
- **Per address**: ~2-5 MB
- **50k addresses**: ~100-250 GB = **$1,500-$3,750**

### Cost Optimization
1. Increase `BATCH_SIZE` (more addresses per IP)
2. Use datacenter proxies for testing ($0.50/GB)
3. Request BrightData KYC access for lower rates

---

## Best Practices

### ✅ DO
- Run on VPS for 24/7 operation
- Monitor first 100-200 addresses
- Keep `HEADLESS = False` for debugging
- Check `errors/` folder for issues

### ❌ DON'T
- Run on unstable internet connection
- Change settings mid-run
- Modify `progress.json` manually
- Share `.env` file

---

## Technical Details

### Technologies
- **Browser**: Firefox (Playwright)
- **Proxy**:  Residential
- **Language**: Python 3.11+
- **Parallel**: ThreadPoolExecutor

### Anti-Detection Features
1. **Realistic User-Agent** - Rotates between Firefox versions
2. **Mouse Movements** - Random scrolling and hovering
3. **Typing Delays** - 60-180ms per character
4. **Page Warm-up** - Random browsing before search
5. **Randomized Delays** - 4-7 seconds between actions

---

## Support

### Common Questions

**Q: Can I run this on Windows?**  
A: Yes, tested on Windows 10/11.

**Q: How much RAM needed?**  
A: 4GB minimum, 8GB recommended for 4 workers.

**Q: Can I interrupt and resume?**  
A: Yes, progress auto-saves after each address.

**Q: What if I get blocked?**  
A: Bot automatically waits and retries. If still blocked, it ends the batch and starts fresh.

---

## Version History

### Current Version (Stable)
- Increased delays for stability (4-7s)
- CAPTCHA recovery with 30-45s cooldown
- 3-attempt retry for clicks
- Batch size reduced to 3

### Performance
- **Stability**: High 🟢
- **Speed**: Moderate 🟡
- **Recommended for**: Production use

---

## License & Disclaimer

This tool is for educational purposes. Ensure compliance with TruePeopleSearch Terms of Service and local data privacy laws.

---

**Last Updated**: December 21, 2024  
**Bot Version**: Stable v2.0  
**Maintained by**: Development Team
#
