# Quick Start Guide

## NEW: Unbreakable Mode + Real-Time Monitoring

### Option 1: RECOMMENDED - Unbreakable Mode (Auto-Restart)

Run the scraper with automatic error recovery:

```bash
python main.py
```

**Features:**
- ✅ **Auto-restarts** on any error
- ✅ **Infinite loop** - runs until all 50k addresses complete
- ✅ **Smart cooldown** - waits 60s between restarts
- ✅ **Crash protection** - extended cooldown if crashing rapidly
- ✅ **Stats tracking** - tracks total runs and crashes

**This is the best option for large-scale 50k+ scraping!**

---

### Option 2: View Real-Time Progress

In a **SECOND terminal** (while scraper is running):

```bash
python monitor.py
```

**Dashboard shows:**
- ✅ Current progress (X / 50,000)
- ✅ Completion percentage
- ✅ Processing rate (addresses/hour)
- ✅ Estimated time remaining
- ✅ Status breakdown (Found, Blocked, Errors)
- ✅ System stats (Crashes, Uptime)

**Auto-refreshes every 10 seconds!**

---

### Option 3: Manual Run (Old Way)

If you want manual control:

```bash
python truepeoplesearch_firefox.py
```

---

## Typical Workflow for 50k Leads

### 1. Start the Scraper
```bash
python main.py
```

### 2. Open Monitoring Dashboard (in new terminal)
```bash
python monitor.py
```

### 3. Let it run for days
- Don't touch it!
- Check dashboard once per day
- Scraper auto-restarts on errors

### 4. Check Results
- `output.xlsx` - Final results
- `progress.json` - Resume point
- `monitoring_stats.json` - System stats

---

## What Happens on Errors?

### Automatic Recovery Flow:

1. **Script crashes** → Logs error
2. **Waits 60 seconds** → Cooldown
3. **Automatically restarts** → Continues from last checkpoint
4. **Resumes scraping** → Uses progress.json

### Rapid Crash Protection:

If script crashes **3 times in 5 minutes**:
- Extended cooldown: **5 minutes**
- Prevents infinite crash loops
- Gives time for temporary issues to resolve

---

## Monitoring Files

### `monitoring_stats.json`
```json
{
  "total_runs": 15,
  "total_crashes": 2,
  "started_at": "2024-12-21T10:00:00",
  "last_crash": "2024-12-21T14:30:00"
}
```

View anytime to see system health.

### `progress.json`
```json
{
  "completed": ["address1", "address2", ...]
}
```

Resume checkpoint - auto-updated after each address.

---

## Stopping the Scraper

### Graceful Stop (RECOMMENDED):
```
Press Ctrl+C in terminal
```

- Saves progress
- Closes browsers cleanly
- Can resume later with `python main.py`

### Force Stop (NOT RECOMMENDED):
- Close terminal window
- May lose current batch progress

---

## FAQ

**Q: Can I check progress without stopping?**  
A: Yes! Run `python monitor.py` in a second terminal.

**Q: What if my internet disconnects?**  
A: Script auto-restarts after 60s cooldown.

**Q: What if my computer restarts?**  
A: Run `python main.py` again - it resumes from checkpoint.

**Q: How do I know it's working?**  
A: Watch the `monitor.py` dashboard - progress counter increases.

**Q: Can I run this on a server?**  
A: YES! Perfect for VPS/server deployment. Use `screen` or `tmux`.

---

## VPS Deployment (24/7 Operation)

### Using screen (keeps running after disconnect)

```bash
# Start screen session
screen -S scraper

# Run unbreakable scraper
python main.py

# Detach (Ctrl+A, then D)
# Now you can disconnect - it keeps running!

# Reattach later
screen -r scraper

# View monitoring
screen -S monitor
python monitor.py
# Detach with Ctrl+A, D
```

---

## Performance Monitoring

Check stats anytime:
```bash
cat monitoring_stats.json
cat progress.json
```

Or use the live dashboard:
```bash
python monitor.py
```

---

## Example Dashboard Output

```
================================================================================
📊 TRUEPEOPLESEARCH SCRAPER - REAL-TIME DASHBOARD
================================================================================
🕐 Current Time: 2024-12-21 16:30:45

📈 PROGRESS:
   Completed: 1,245 / 50,000 addresses
   Remaining: 48,755
   Progress: 2.5%
   [██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 2.5%

⚡ PERFORMANCE:
   Processing Rate: 52.3 addresses/hour
   Est. Daily Rate: 1,255 addresses/day
   Est. Time Remaining: 38.8 days

🖥️ SYSTEM:
   Total Runs: 8
   Total Crashes: 1
   Last Crash: 2024-12-21 14:30:22

📋 STATUS BREAKDOWN:
   ✅ FOUND: 1,089
   ℹ️ NO_PHONE: 98
   ℹ️ NO_PROFILES: 45
   ❌ ERROR: 13

================================================================================
Press Ctrl+C to exit | Auto-refresh every 10 seconds
================================================================================
```

---

**Ready to scrape 50k leads unbreakably!** 🚀
