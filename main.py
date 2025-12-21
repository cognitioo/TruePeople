#!/usr/bin/env python3
"""
UNBREAKABLE WRAPPER - Auto-Restart Scraper
===========================================
This script runs the scraper in an infinite loop.
If it crashes, it automatically restarts after a brief cooldown.

Features:
- Auto-restart on any error
- Tracks restart count
- Cooldown between restarts (prevents rapid crash loops)
- Clean error logging
"""

import subprocess
import sys
import time
from datetime import datetime
import json
from pathlib import Path

# Configuration
SCRAPER_SCRIPT = "truepeoplesearch_firefox.py"
COOLDOWN_SECONDS = 60  # Wait 60s between restarts
MAX_RAPID_RESTARTS = 3  # If script crashes 3 times in 5 min, wait longer
RAPID_RESTART_WINDOW = 300  # 5 minutes

# Stats file
STATS_FILE = "monitoring_stats.json"


def load_stats():
    """Load monitoring stats"""
    try:
        if Path(STATS_FILE).exists():
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    
    return {
        'total_runs': 0,
        'total_crashes': 0,
        'last_crash': None,
        'started_at': datetime.now().isoformat(),
        'restarts': []
    }


def save_stats(stats):
    """Save monitoring stats"""
    try:
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        print(f"⚠️ Could not save stats: {e}")


def check_rapid_restarts(stats):
    """Check if we're in a rapid restart loop"""
    recent_restarts = [
        r for r in stats['restarts']
        if (datetime.now() - datetime.fromisoformat(r)).total_seconds() < RAPID_RESTART_WINDOW
    ]
    
    return len(recent_restarts) >= MAX_RAPID_RESTARTS


def print_header():
    """Print fancy header"""
    print("\n" + "="*70)
    print("🚀 UNBREAKABLE SCRAPER - Auto-Restart Wrapper")
    print("="*70)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 Script: {SCRAPER_SCRIPT}")
    print(f"⏱️ Cooldown: {COOLDOWN_SECONDS}s between restarts")
    print("="*70 + "\n")


def print_stats(stats):
    """Print current stats"""
    print("\n" + "-"*70)
    print("📊 MONITORING STATS")
    print("-"*70)
    print(f"   Total runs: {stats['total_runs']}")
    print(f"   Total crashes: {stats['total_crashes']}")
    print(f"   Uptime since: {stats['started_at'][:19]}")
    if stats['last_crash']:
        print(f"   Last crash: {stats['last_crash'][:19]}")
    print("-"*70 + "\n")


def main():
    """Main loop - runs scraper forever"""
    print_header()
    
    stats = load_stats()
    
    while True:
        stats['total_runs'] += 1
        save_stats(stats)
        
        print(f"\n{'='*70}")
        print(f"🔄 RUN #{stats['total_runs']} - Starting scraper...")
        print(f"{'='*70}\n")
        
        try:
            # Run the scraper
            result = subprocess.run(
                [sys.executable, SCRAPER_SCRIPT],
                cwd=".",
                text=True
            )
            
            # Check exit code
            if result.returncode == 0:
                print("\n✅ Scraper completed successfully!")
                print("🎉 All addresses processed. Exiting wrapper.")
                break  # Exit if scraper completed normally
            else:
                print(f"\n⚠️ Scraper exited with code {result.returncode}")
                stats['total_crashes'] += 1
                stats['last_crash'] = datetime.now().isoformat()
                stats['restarts'].append(datetime.now().isoformat())
                save_stats(stats)
                
        except KeyboardInterrupt:
            print("\n\n🛑 User interrupted. Exiting...")
            print_stats(stats)
            sys.exit(0)
            
        except Exception as e:
            print(f"\n❌ CRASH: {e}")
            stats['total_crashes'] += 1
            stats['last_crash'] = datetime.now().isoformat()
            stats['restarts'].append(datetime.now().isoformat())
            save_stats(stats)
        
        # Print current stats
        print_stats(stats)
        
        # Check for rapid restart loop
        if check_rapid_restarts(stats):
            extended_cooldown = COOLDOWN_SECONDS * 5
            print(f"⚠️ WARNING: Rapid restart loop detected!")
            print(f"⏸️ Extended cooldown: {extended_cooldown}s")
            time.sleep(extended_cooldown)
            # Clear old restarts
            stats['restarts'] = []
        else:
            # Normal cooldown
            print(f"⏸️ Cooldown: {COOLDOWN_SECONDS}s before restart...")
            time.sleep(COOLDOWN_SECONDS)
        
        print("\n🔄 Restarting scraper...\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Shutdown complete. Goodbye!")
        sys.exit(0)
