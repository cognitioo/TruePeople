#!/usr/bin/env python3
"""
TruePeopleSearch Scraper using Playwright Firefox
==================================================
Extracts first person's mobile number from address search results.
Uses BrightData US residential proxy with Firefox for anti-detection.
Firefox has better fingerprint resistance than Chromium.
"""

import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import gc  # For memory cleanup during long runs

import openpyxl
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Proxy Configuration (BrightData Residential)
PROXY_HOST = os.getenv('PROXY_HOST', 'brd.superproxy.io')
PROXY_PORT = os.getenv('PROXY_PORT', '33335')
PROXY_USERNAME = os.getenv('PROXY_USERNAME', 'brd-customer-hl_14bd7443-zone-residential_proxy1-country-us')
PROXY_PASSWORD = os.getenv('PROXY_PASSWORD', '45wb9gsbupfi')

# File paths
EXCEL_INPUT = 'leads.xlsx'
ERRORS_DIR = 'errors'

# Scraping settings
TARGET_URL = 'https://www.truepeoplesearch.com/'
TEST_MODE = False  # Set to False for full run
TEST_ROWS = 2     # Number of rows to test in test mode

# Batch processing (addresses per browser session)
BATCH_SIZE = 3  # Process fewer addresses per browser session (more stable)
MAX_RETRIES = 3  # Max retries per address on failure
MAX_BLOCKED_RETRIES = 3  # Retry blocked addresses with new IP

# Progress checkpoint (resume capability)
PROGRESS_FILE = 'progress.json'

# Captcha/block detection patterns
BLOCK_URL_PATTERNS = ['InternalCaptcha', 'captcha', 'blocked', 'challenge']

# Browser mode (False = visible browser, True = hidden/faster)
HEADLESS = False  # Set to True for headless mode (faster but may be more detectable)

# Parallel processing (multiple browser instances)
PARALLEL_WORKERS = 2  # Number of browser instances to run simultaneously

# Timing (human-like delays - INCREASED for stability)
DELAY_MIN = 4.0  # Increased from 2.0
DELAY_MAX = 7.0  # Increased from 5.0
TYPING_DELAY_MIN = 60   # milliseconds (increased)
TYPING_DELAY_MAX = 180  # milliseconds (increased)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def ensure_errors_dir():
    """Create errors directory if it doesn't exist."""
    Path(ERRORS_DIR).mkdir(exist_ok=True)


def cleanup_old_html_files(max_age_hours: int = 24):
    """Delete HTML debug files older than max_age_hours to save disk space."""
    try:
        errors_path = Path(ERRORS_DIR)
        if not errors_path.exists():
            return
        
        now = time.time()
        deleted_count = 0
        
        for html_file in errors_path.glob("results_*.html"):
            file_age_hours = (now - html_file.stat().st_mtime) / 3600
            if file_age_hours > max_age_hours:
                html_file.unlink()
                deleted_count += 1
        
        if deleted_count > 0:
            print(f"     🧹 Cleaned up {deleted_count} old HTML files")
    except Exception as e:
        pass  # Non-critical, ignore errors


def load_progress() -> dict:
    """Load progress from checkpoint file."""
    try:
        if Path(PROGRESS_FILE).exists():
            import json
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {'completed': [], 'failed': []}


def save_progress(progress: dict):
    """Save progress to checkpoint file. Caller must hold progress_lock."""
    import json
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)
    print(f"     💾 Progress saved: {len(progress.get('completed', []))} completed")


# Thread lock for thread-safe operations
progress_lock = threading.Lock()
excel_lock = threading.Lock()
results_lock = threading.Lock()  # Lock for results list


def is_blocked_url(url: str) -> bool:
    """Check if URL indicates captcha/block."""
    url_lower = url.lower()
    for pattern in BLOCK_URL_PATTERNS:
        if pattern.lower() in url_lower:
            return True
    return False


def get_timestamp():
    """Get current timestamp for filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def random_delay(min_sec: float = DELAY_MIN, max_sec: float = DELAY_MAX) -> float:
    """Human-like random delay between actions."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay


def human_type(page, selector: str, text: str):
    """Type text with very human-like delays - includes typos and corrections."""
    element = page.locator(selector)
    element.click()
    time.sleep(random.uniform(0.5, 1.0))  # Longer initial pause
    
    for i, char in enumerate(text):
        # Variable typing speed - faster in middle, slower at start/end
        if i < 3 or i > len(text) - 3:
            delay = random.randint(100, 200)
        else:
            delay = random.randint(50, 150)
        
        page.keyboard.type(char, delay=delay)
        
        # Occasional micro-pause (like thinking)
        if random.random() < 0.08:
            time.sleep(random.uniform(0.2, 0.6))
    
    time.sleep(random.uniform(0.3, 0.7))


def smooth_mouse_move(page, x: int, y: int):
    """Move mouse smoothly using bezier-like curve."""
    try:
        # Get current mouse position (approximate from center)
        steps = random.randint(20, 40)
        page.mouse.move(x, y, steps=steps)
        time.sleep(random.uniform(0.05, 0.15))
    except:
        pass


def random_scroll(page):
    """Scroll page naturally like a human."""
    try:
        # Random scroll amount
        scroll_amount = random.randint(100, 400)
        direction = random.choice([1, -1, 1])  # More likely down
        page.mouse.wheel(0, scroll_amount * direction)
        time.sleep(random.uniform(0.3, 0.8))
    except:
        pass


def random_mouse_movement(page):
    """Simulate natural mouse movements with minimal scrolling."""
    try:
        # REDUCED iterations from 3-6 to 2-3
        for _ in range(random.randint(2, 3)):
            x = random.randint(100, 1200)
            y = random.randint(100, 700)
            smooth_mouse_move(page, x, y)
            time.sleep(random.uniform(0.05, 0.15))  # Reduced from 0.1-0.3
        
        # REMOVED hover/pause - was slowing things down
        
        # Removed scroll from here - only scroll when explicitly called
    except:
        pass


def warm_up_page(page):
    """Spend time on page naturally before taking actions - REDUCED for speed."""
    print("  🔥 Warming up page...")
    try:
        # Quick scroll to simulate reading (REDUCED from 2-3 to 1 iteration)
        random_mouse_movement(page)
        random_scroll(page)
        time.sleep(random.uniform(0.3, 0.6))  # Reduced from 0.5-1.0
        
        print("     Done warming up")
    except:
        pass


def take_error_screenshot(page, error_type: str, address: str) -> str:
    """Take screenshot on error for debugging."""
    ensure_errors_dir()
    safe_address = re.sub(r'[^\w\s-]', '', address)[:30].replace(' ', '_')
    filename = f"{ERRORS_DIR}/{error_type}_{safe_address}_{get_timestamp()}.png"
    try:
        page.screenshot(path=filename)
        print(f"  📸 Screenshot saved: {filename}")
        return filename
    except Exception as e:
        print(f"  ⚠️ Could not save screenshot: {e}")
        return None


def parse_address(full_address: str) -> tuple:
    """
    Parse full address into street and city/state/zip components.
    
    Expected formats:
    - "123 Main St, Boston, MA 02101"
    - "123 Main St, Boston, MA"
    """
    if not full_address or not isinstance(full_address, str):
        return '', ''
    
    # Clean up the address
    address = full_address.strip()
    
    # Split by comma
    parts = [p.strip() for p in address.split(',')]
    
    if len(parts) >= 3:
        # Format: "Street, City, State ZIP" or "Street, City, State, ZIP"
        street = parts[0]
        city_state_zip = ', '.join(parts[1:])
        return street, city_state_zip
    elif len(parts) == 2:
        # Format: "Street, City State ZIP" (all in second part)
        street = parts[0]
        city_state_zip = parts[1]
        return street, city_state_zip
    else:
        # Single part - try to split by last number group (zip code)
        match = re.match(r'^(.+?),?\s*(\w+,?\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?)$', address)
        if match:
            return match.group(1), match.group(2)
        return address, ''


def extract_phone_from_text(text: str) -> str:
    """Extract first phone number from text."""
    # Common phone patterns
    patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890 or 123-456-7890
        r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',           # 123 456 7890
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]
    return ''


# ============================================================================
# EXCEL OPERATIONS
# ============================================================================

def read_excel_addresses(file_path: str) -> list:
    """Read addresses from Excel file."""
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    
    # Get headers
    headers = [cell.value for cell in ws[1]]
    
    # Find Address column
    address_col = None
    for idx, header in enumerate(headers):
        if header and 'address' in str(header).lower():
            address_col = idx
            break
    
    if address_col is None:
        raise ValueError("Could not find 'Address' column in Excel file")
    
    # Read data
    data = []
    for row in ws.iter_rows(min_row=2):
        address = row[address_col].value
        if address:
            data.append({
                'address': str(address).strip(),
                'row_num': row[0].row
            })
    
    return data



def update_input_excel(file_path: str, row_num: int, phone: str):
    """Update the input Excel file with extracted phone number (column 3)."""
    try:
        with excel_lock:
            wb = openpyxl.load_workbook(file_path)
            ws = wb.active
            
            # Column 3 is where we write the phone number (replace N/A)
            ws.cell(row=row_num, column=3, value=phone)
            
            wb.save(file_path)
        print(f"     📝 Updated {file_path} row {row_num} with phone: {phone}")
    except Exception as e:
        print(f"     ⚠️ Could not update input Excel: {e}")


# ============================================================================
# CLOUDFLARE / PROTECTION HANDLING
# ============================================================================

def wait_for_cloudflare(page, max_wait: int = 90) -> bool:
    """
    Wait for Cloudflare/DataDome challenge to resolve.
    Returns True if page is accessible, False if blocked.
    Increased wait time for stability.
    """
    print("  🛡️ Checking for Cloudflare/DataDome...")
    
    start_time = time.time()
    
    while (time.time() - start_time) < max_wait:
        try:
            title = page.title()
            html = page.content()
            
            # Check for blocking indicators (Cloudflare + DataDome)
            is_blocked = (
                # Cloudflare patterns
                "Just a moment" in title or
                "Access denied" in title or
                "Attention Required" in title or
                "challenge-running" in html[:10000] or
                "cf-challenge" in html[:10000] or
                # DataDome patterns
                "captcha-delivery" in html[:10000] or
                "datadome" in html[:10000].lower() or
                "geo.captcha-delivery.com" in html[:10000] or
                "Device Check" in title
            )
            
            if is_blocked:
                print(f"  ⏳ Challenge in progress... (waiting)")
                random_mouse_movement(page)
                time.sleep(8)  # Increased wait for challenge
            else:
                # Extra check: make sure we have actual content
                if len(html) > 5000 and "truepeoplesearch" in html.lower():
                    # Wait a bit more for page to fully stabilize
                    time.sleep(2)
                    print("  ✅ Page accessible!")
                    return True
                else:
                    print("  ⏳ Waiting for content...")
                    time.sleep(4)  # Increased wait for content
                
        except Exception as e:
            print(f"  ⚠️ Error checking page: {e}")
            time.sleep(3)
    
    print("  ❌ Timeout waiting for challenge to resolve")
    return False


# ============================================================================
# MAIN SCRAPING LOGIC
# ============================================================================

def scrape_address(page, address: str, row_num: int = 0, is_first_in_batch: bool = True) -> dict:
    """
    Scrape TruePeopleSearch for a single address.
    Returns dict with extracted data or error info.
    row_num is the Excel row to update with phone number.
    is_first_in_batch: if True (first address), skip warm-up; if False, do warm-up.
    """
    result = {
        'address': address,
        'name': '',
        'age': '',
        'phone': '',
        'profile_url': '',
        'status': 'ERROR',
        'error': ''
    }
    
    street, city_state_zip = parse_address(address)
    print(f"\n{'='*60}")
    print(f"📍 Searching: {address}")
    print(f"   Street: {street}")
    print(f"   City/State/Zip: {city_state_zip}")
    print(f"{'='*60}")
    
    if not street:
        result['error'] = 'Invalid address format'
        take_error_screenshot(page, 'invalid_address', address)
        return result
    
    try:
        # Step 1: Navigate to homepage
        print("  1. Navigating to TruePeopleSearch...")
        page.goto(TARGET_URL, timeout=60000, wait_until='domcontentloaded')
        random_delay(4, 6)  # Increased for stability
        
        # Step 2: Wait for Cloudflare
        if not wait_for_cloudflare(page):
            result['error'] = 'Blocked by Cloudflare'
            take_error_screenshot(page, 'cloudflare_blocked', address)
            return result
        
        # Step 2.5: Warm up the page (skip for first address, do for subsequent)
        if not is_first_in_batch:
            # Subsequent addresses - SKIP warm-up, just a brief pause
            # (Warm-up was causing hangs and is unnecessary after first address)
            print("     ⏸️ Brief pause...")
            random_delay(1, 2)
        else:
            # First address - fresh session, wait for page to be fully ready
            print("     ⏳ Waiting for page to fully load...")
            try:
                page.wait_for_load_state('networkidle', timeout=20000)
            except:
                pass
            random_delay(2, 3)
        
        # Step 3: Fill main address input (direct approach - no tab clicking needed)
        print("  2. Filling main address input...")
        # Use full address in the main input: "street, city, state zip"
        full_address = f"{street}, {city_state_zip}" if city_state_zip else street
        
        try:
            # Wait for page to be fully loaded first
            page.wait_for_load_state('networkidle', timeout=15000)
            
            # Try multiple selectors for the address input
            selectors = ['#id-d-n', 'input[name="StreetAddress"]', 'input[placeholder*="Address"]']
            address_input = None
            
            for selector in selectors:
                try:
                    loc = page.locator(selector)
                    if loc.count() > 0 and loc.is_visible():
                        address_input = loc
                        break
                except:
                    continue
            
            if address_input is None:
                # Last resort - wait a bit more and try main selector
                random_delay(1, 2)
                address_input = page.locator('#id-d-n')
            
            # Multiple click attempts with fallbacks
            clicked = False
            for attempt_num, method in enumerate(['normal', 'force', 'js'], 1):
                try:
                    if method == 'normal':
                        address_input.click(timeout=5000)
                    elif method == 'force':
                        address_input.click(timeout=5000, force=True)
                    else:  # js
                        handle = address_input.element_handle(timeout=5000)
                        if handle:
                            page.evaluate("el => el.click()", handle)
                    clicked = True
                    break
                except Exception as click_err:
                    if attempt_num < 3:
                        print(f"     ⚠️ Click attempt {attempt_num} ({method}) failed, trying next...")
                        random_delay(0.5, 1)
            
            if not clicked:
                raise Exception("All click attempts failed")
            
            time.sleep(random.uniform(0.3, 0.6))
            
            # Type with human-like delays
            for char in full_address:
                page.keyboard.type(char, delay=random.randint(TYPING_DELAY_MIN, TYPING_DELAY_MAX))
                if random.random() < 0.05:  # Occasional pause
                    time.sleep(random.uniform(0.1, 0.3))
            print(f"     ✅ Typed: {full_address}")
            
        except Exception as e:
            result['error'] = f'Address input error: {str(e)[:30]}'
            take_error_screenshot(page, 'address_input_error', address)
            return result
        
        random_delay(1, 2)
        
        # Step 3: Fill city/state/zip input
        print("  3. Filling city/state/zip...")
        try:
            city_input = page.locator('#id-d-loc-name')
            
            # Multiple click attempts with fallbacks (same as address)
            clicked = False
            for attempt_num, method in enumerate(['normal', 'force', 'js'], 1):
                try:
                    if method == 'normal':
                        city_input.click(timeout=5000)
                    elif method == 'force':
                        city_input.click(timeout=5000, force=True)
                    else:  # js
                        handle = city_input.element_handle(timeout=5000)
                        if handle:
                            page.evaluate("el => el.click()", handle)
                    clicked = True
                    break
                except:
                    if attempt_num < 3:
                        random_delay(0.5, 1)
            
            if clicked:
                time.sleep(random.uniform(0.3, 0.6))
                for char in city_state_zip:
                    page.keyboard.type(char, delay=random.randint(TYPING_DELAY_MIN, TYPING_DELAY_MAX))
                print(f"     ✅ Typed: {city_state_zip}")
            else:
                print("     ⚠️ City input click failed, continuing...")
        except Exception as e:
            print(f"     ⚠️ City input error: {str(e)[:30]}")
        
        random_delay(2, 3)  # CRITICAL: Wait for typing to complete before submitting
        random_mouse_movement(page)
        
        # Step 6: Submit search
        print("  5. Submitting search...")
        submit_selectors = [
            'button[type="submit"]',
            'button.btn-primary',
            'input[type="submit"]',
            'button:has-text("Search")'
        ]
        
        submitted = False
        for selector in submit_selectors:
            try:
                btn = page.locator(selector).first
                if btn.count() > 0:
                    btn.click(timeout=10000)
                    print("     ✅ Search submitted")
                    submitted = True
                    break
            except Exception:
                continue
        
        if not submitted:
            # Fallback: press Enter
            page.keyboard.press('Enter')
            print("     ✅ Search submitted (Enter key)")
        
        # Step 7: Wait for results
        print("  6. Waiting for results...")
        page.wait_for_load_state('domcontentloaded', timeout=30000)
        random_delay(3, 5)
        
        # Print current URL for reference
        current_url = page.url
        print(f"     URL: {current_url[:80]}...")
        
        # Check for captcha/block
        if is_blocked_url(current_url):
            result['status'] = 'BLOCKED'
            result['error'] = 'Captcha/block detected'
            take_error_screenshot(page, 'captcha_blocked', address)
            print(f"     ⚠️ BLOCKED: Captcha detected, needs IP rotation")
            return result
        
        # Save the page HTML for debugging
        ensure_errors_dir()
        html = page.content()
        html_file = f"{ERRORS_DIR}/results_{get_timestamp()}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"     📄 HTML saved: {html_file}")
        
        # Selectors confirmed - continuing with scrape
        
        # Step 8: Check for results
        print("  7. Looking for results...")
        html = page.content()
        
        # Check for "no results" message
        no_results_patterns = [
            'no results',
            'not found',
            'no records',
            'no people found',
            '0 results'
        ]
        
        if any(pattern in html.lower() for pattern in no_results_patterns):
            result['status'] = 'NOT_FOUND'
            result['error'] = 'No results found for this address'
            take_error_screenshot(page, 'no_results', address)
            return result
        
        # Step 9: Find and click first person's "View Details" button
        print("  8. Looking for View Details button...")
        # Prioritize href-based selectors since CSS may not load
        profile_selectors = [
            'a[href*="/find/person/"]',  # Most reliable - works without CSS
            'a:has-text("View Details")',  # Text-based
            'a.detail-link',  # CSS class (backup)
            'a.btn.btn-success.btn-lg.detail-link',  # Full CSS selector
        ]
        
        profile_link = None
        for selector in profile_selectors:
            try:
                links = page.locator(selector)
                if links.count() > 0:
                    profile_link = links.first
                    break
            except Exception:
                continue
        
        if profile_link:
            # Get profile URL before clicking
            href = profile_link.get_attribute('href')
            if href:
                if href.startswith('/'):
                    result['profile_url'] = f"https://www.truepeoplesearch.com{href}"
                else:
                    result['profile_url'] = href
            
            # Try to extract name from the card
            try:
                card = page.locator('.card').first
                card_text = card.inner_text()
                
                # Extract name (usually first line or in h2/h3)
                lines = [l.strip() for l in card_text.split('\n') if l.strip()]
                if lines:
                    result['name'] = lines[0]
                
                # Extract age
                age_match = re.search(r'Age[:\s]*(\d+)', card_text, re.IGNORECASE)
                if age_match:
                    result['age'] = age_match.group(1)
                
            except Exception:
                pass
            
            # Click to go to profile details - use JS click to bypass overlays
            print("  9. Clicking first profile...")
            original_url = page.url
            
            # Try clicking up to 3 times if URL doesn't change
            for click_attempt in range(1, 4):
                try:
                    if click_attempt == 1:
                        profile_link.click(timeout=15000, force=True)
                    elif click_attempt == 2:
                        print("     🔄 Retry click with JS...")
                        page.evaluate("el => el.click()", profile_link.element_handle())
                    else:
                        print("     🔄 Retry click with navigation...")
                        href = profile_link.get_attribute('href')
                        if href:
                            full_url = f"https://www.truepeoplesearch.com{href}" if href.startswith('/') else href
                            page.goto(full_url, timeout=30000, wait_until='domcontentloaded')
                except:
                    print(f"     ⚠️ Click attempt {click_attempt} failed")
                
                # Wait for navigation
                try:
                    page.wait_for_load_state('domcontentloaded', timeout=30000)
                except:
                    pass
                random_delay(3, 4)
                
                # Check if URL changed
                current_url = page.url
                if '/find/person/' in current_url or original_url != current_url:
                    print(f"     ✅ Navigated to profile page (attempt {click_attempt})")
                    break
                
                if click_attempt == 3:
                    print("     ❌ All click attempts failed, URL didn't change")
                    result['status'] = 'ERROR'
                    result['error'] = 'Click navigation failed'
                    take_error_screenshot(page, 'click_failed', address)
                    return result
            
            # Quick cloudflare check - just make sure we have content
            page_text = ""
            try:
                random_delay(2, 3)  # Brief wait for content
                page_text = page.inner_text('body') if page.locator('body').count() > 0 else ""
                
                # If page has our content, we're good
                if "truepeoplesearch" not in page_text.lower() and len(page_text) < 1000:
                    print("     ⚠️ Page may be blocked, waiting...")
                    random_delay(3, 5)
                    page_text = page.inner_text('body') if page.locator('body').count() > 0 else ""
            except:
                pass
            
            # Step 10: Extract phone number IMMEDIATELY
            print("  10. Extracting phone number...")
            
            # Get page content for extraction
            page_content = page.content()
            page_text = page.inner_text('body') if page.locator('body').count() > 0 else ""
            
            # Look for Wireless/Mobile numbers first
            wireless_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\s*-\s*Wireless', page_text)
            if wireless_match:
                # Extract just the phone number part
                phone_raw = wireless_match.group(0)
                phone = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', phone_raw)
                if phone:
                    result['phone'] = phone.group(0)
                    print(f"     ✅ Found mobile: {result['phone']}")
            
            # Fallback to any phone number
            if not result['phone']:
                phone = extract_phone_from_text(page_text)
                if phone:
                    result['phone'] = phone
                    print(f"     ✅ Found phone: {result['phone']}")
            
            # Extract name from page if not already set
            if not result['name']:
                try:
                    h1 = page.locator('h1').first
                    if h1.count() > 0:
                        result['name'] = h1.inner_text().strip()
                except:
                    pass
            
            # Extract age
            if not result['age']:
                age_match = re.search(r'Age\s*(\d+)', page_text)
                if age_match:
                    result['age'] = age_match.group(1)
            
            if result['phone']:
                result['status'] = 'FOUND'
                print(f"\n  ✅ SUCCESS!")
                print(f"     Name: {result['name']}")
                print(f"     Age: {result['age']}")
                print(f"     Phone: {result['phone']}")
                
                # Update input Excel with phone number
                print(f"     📍 row_num={row_num}, attempting Excel update...")
                if row_num > 0:
                    update_input_excel(EXCEL_INPUT, row_num, result['phone'])
                else:
                    print(f"     ⚠️ row_num is 0, skipping Excel update")
            else:
                result['status'] = 'NO_PHONE'
                result['error'] = 'Profile found but no phone number'
                take_error_screenshot(page, 'no_phone', address)
        else:
            result['status'] = 'NO_PROFILES'
            result['error'] = 'No profile links found'
            take_error_screenshot(page, 'no_profiles', address)
        
        return result
        
    except Exception as e:
        result['error'] = str(e)[:100]
        take_error_screenshot(page, 'exception', address)
        print(f"  ❌ Error: {e}")
        return result

def scrape_single_address(playwright, address: str, row_num: int, session_id: str):
    """
    Scrape a single address with a fresh browser session for proxy rotation.
    Returns the result dict.
    """
    # Generate unique session ID for proxy rotation (new IP)
    proxy_config = {
        'server': f'http://{PROXY_HOST}:{PROXY_PORT}',
        'username': f'{PROXY_USERNAME}-session-{session_id}',
        'password': PROXY_PASSWORD
    }
    
    result = {
        'address': address,
        'name': '',
        'age': '',
        'phone': '',
        'profile_url': '',
        'status': 'ERROR',
        'error': ''
    }
    
    browser = None
    try:
        browser = playwright.firefox.launch(
            headless=HEADLESS,
            firefox_user_prefs={
                'toolkit.telemetry.enabled': False,
                'security.cert_pinning.enforcement_level': 0,
                'network.stricttransportsecurity.preloadlist': False,
            }
        )
        
        context = browser.new_context(
            proxy=proxy_config,
            locale='en-US',
            timezone_id='America/Chicago',
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            ignore_https_errors=True,
        )
        context.set_default_timeout(60000)
        
        page = context.new_page()
        result = scrape_address(page, address, row_num=row_num)
        
        page.close()
        context.close()
        
    except Exception as e:
        result['error'] = str(e)[:100]
        print(f"     ❌ Browser error: {e}")
    finally:
        if browser:
            try:
                browser.close()
            except:
                pass

    return result


def process_batch_worker(worker_id: int, batch: list, progress: dict, completed_addresses: set, results: list):
    """
    Worker function for parallel processing.
    Each worker processes a batch of addresses with its own browser.
    """
    from playwright.sync_api import sync_playwright
    
    # Staggered start - Worker 2+ waits before starting to avoid simultaneous requests
    if worker_id > 1:
        stagger_delay = (worker_id - 1) * random.uniform(8, 15)
        print(f"\n⏳ [Worker {worker_id}] Waiting {stagger_delay:.1f}s before starting (staggered)...")
        time.sleep(stagger_delay)
    
    session_id = f"{int(time.time())}_{random.randint(1000, 9999)}_{worker_id}"
    
    # Different user agents for each worker to avoid fingerprinting
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.0; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]
    user_agent = USER_AGENTS[(worker_id - 1) % len(USER_AGENTS)]
    
    print(f"\n🦊 [Worker {worker_id}] Starting browser session: {session_id[:15]}...")
    print(f"   Processing {len(batch)} addresses...")
    print(f"   User-Agent: ...{user_agent[-30:]}")
    
    # Create browser for this worker
    proxy_config = {
        'server': f'http://{PROXY_HOST}:{PROXY_PORT}',
        'username': f'{PROXY_USERNAME}-session-{session_id}',
        'password': PROXY_PASSWORD
    }
    
    with sync_playwright() as playwright:
        browser = None
        try:
            browser = playwright.firefox.launch(
                headless=HEADLESS,
                firefox_user_prefs={
                    'toolkit.telemetry.enabled': False,
                    'security.cert_pinning.enforcement_level': 0,
                    'network.stricttransportsecurity.preloadlist': False,
                }
            )
            
            context = browser.new_context(
                proxy=proxy_config,
                locale='en-US',
                timezone_id='America/Chicago',
                viewport={'width': 1920, 'height': 1080},
                user_agent=user_agent,
                ignore_https_errors=True,
            )
            context.set_default_timeout(60000)
            
            page = context.new_page()
            
            # 💰 COST OPTIMIZATION: Block heavy resources to save 40% bandwidth
            # Only need HTML/text for phone number extraction
            def block_heavy_resources(route):
                """Block images, fonts, CSS to reduce proxy costs"""
                resource_type = route.request.resource_type
                url = route.request.url
                
                # Block images
                if resource_type in ['image', 'media', 'font']:
                    route.abort()
                # Block CSS files (we don't need styling)
                elif url.endswith(('.css', '.woff', '.woff2', '.ttf', '.otf')):
                    route.abort()
                else:
                    route.continue_()
            
            page.route("**/*", block_heavy_resources)
            print(f"   💰 Resource blocking enabled (saves ~40% bandwidth)")

            
            for j, addr_data in enumerate(batch):
                address = addr_data['address']
                row_num = addr_data.get('row_num', 0)
                
                print(f"\n[Worker {worker_id}] Address: {address[:40]}...")
                
                result = scrape_address(page, address, row_num=row_num, is_first_in_batch=(j == 0))
                
                # Track if we should skip the default append (for BLOCKED cases that already appended)
                skip_append = False
                should_break = False
                
                if result['status'] == 'FOUND':
                    print(f"   [W{worker_id}] ✅ SUCCESS: {result['phone']}")
                    with progress_lock:
                        completed_addresses.add(address)
                        progress['completed'] = list(completed_addresses)
                        save_progress(progress)
                elif result['status'] == 'BLOCKED':
                    print(f"   [W{worker_id}] ⛔ BLOCKED - waiting for cooldown...")
                    # Don't immediately break - wait and try to recover
                    random_delay(30, 45)  # Long cooldown wait
                    print(f"   [W{worker_id}] 🔄 Attempting recovery after cooldown...")
                    try:
                        page.goto('about:blank', timeout=10000)
                        random_delay(5, 8)
                        page.goto(TARGET_URL, timeout=60000, wait_until='domcontentloaded')
                        random_delay(5, 8)
                        if wait_for_cloudflare(page):
                            print(f"   [W{worker_id}] ✅ Recovered! Continuing batch...")
                            # Recovery successful - still append the BLOCKED result but continue
                        else:
                            print(f"   [W{worker_id}] ❌ Still blocked, ending batch")
                            should_break = True
                    except Exception as e:
                        print(f"   [W{worker_id}] ❌ Recovery failed: {str(e)[:20]}, ending batch")
                        should_break = True
                elif result['status'] in ['NO_PROFILES', 'NO_PHONE']:
                    print(f"   [W{worker_id}] ℹ️ {result['status']}")
                    with progress_lock:
                        completed_addresses.add(address)
                        progress['completed'] = list(completed_addresses)
                        save_progress(progress)
                else:  # ERROR status
                    print(f"   [W{worker_id}] ⚠️ Error: {result.get('error', 'Unknown')[:30]}")
                    # Navigate to homepage to recover (safer than reload)
                    print(f"   [W{worker_id}] 🔄 Navigating to homepage to recover...")
                    try:
                        page.goto(TARGET_URL, timeout=30000, wait_until='domcontentloaded')
                        random_delay(2, 3)
                    except Exception as nav_err:
                        print(f"   [W{worker_id}] ⚠️ Recovery failed: {str(nav_err)[:20]}")
                        # Check if page/browser is dead
                        try:
                            page.url  # This will fail if page is closed
                        except:
                            print(f"   [W{worker_id}] ❌ Page closed, ending this batch")
                            should_break = True
                
                # Always append result (once!) unless we already did in a break case
                with results_lock:
                    results.append(result)
                
                # Break after appending if needed
                if should_break:
                    break
                
                # Delay between addresses (INCREASED for stability)
                if j < len(batch) - 1:
                    random_delay(5, 8)  # Increased from 3-5
                
                # Memory cleanup every 10 addresses (prevents memory growth)
                if (j + 1) % 10 == 0:
                    gc.collect()
                    print(f"   [W{worker_id}] 🧹 Memory cleanup (address #{j+1})")
            
            # Cleanup page and context (moved inside try for proper cleanup)
            try:
                page.close()
            except:
                pass
            try:
                context.close()
            except:
                pass
            
        except Exception as e:
            print(f"   [W{worker_id}] ❌ Browser error: {e}")
        finally:
            if browser:
                try:
                    browser.close()
                except:
                    pass
    
    print(f"\n🦊 [Worker {worker_id}] Finished batch")


def main():
    """Main entry point with parallel batch processing."""
    print("=" * 70)
    print("🔍 TruePeopleSearch Scraper - Parallel Mode")
    print("=" * 70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Input file: {EXCEL_INPUT}")
    print(f"📂 Output file: {EXCEL_OUTPUT}")
    print(f"📦 Batch size: {BATCH_SIZE} addresses per session")
    print(f"🚀 Parallel workers: {PARALLEL_WORKERS} browsers")
    print(f"🧪 Test mode: {TEST_MODE} (rows: {TEST_ROWS})")
    print("=" * 70)
    
    if not PROXY_USERNAME or not PROXY_PASSWORD:
        print("❌ Error: Missing proxy credentials in .env file")
        return
    
    ensure_errors_dir()
    cleanup_old_html_files()  # Clean up old HTML debug files to save disk space
    
    # Load progress checkpoint
    progress = load_progress()
    completed_addresses = set(progress.get('completed', []))
    print(f"\n📋 Loaded progress: {len(completed_addresses)} already completed")
    
    try:
        addresses = read_excel_addresses(EXCEL_INPUT)
        print(f"📋 Found {len(addresses)} addresses in Excel")
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return
    
    if TEST_MODE:
        addresses = addresses[:TEST_ROWS]
        print(f"🧪 Test mode: Processing only {len(addresses)} addresses")
    
    # Filter out already completed addresses
    pending = [a for a in addresses if a['address'] not in completed_addresses]
    print(f"📋 Pending: {len(pending)} addresses to process")
    
    if not pending:
        print("✅ All addresses already processed!")
        return
    
    results = []
    
    print(f"\n🌐 Proxy: {PROXY_HOST}:{PROXY_PORT}")
    print(f"🚀 Parallel mode: {PARALLEL_WORKERS} browser workers")
    
    # Split pending addresses into INTERLEAVED chunks for parallel workers
    # Worker 1 gets: 1, 3, 5, 7... (odd indices)
    # Worker 2 gets: 2, 4, 6, 8... (even indices)
    # This way both workers process adjacent rows
    chunks = [[] for _ in range(PARALLEL_WORKERS)]
    for i, addr in enumerate(pending):
        worker_idx = i % PARALLEL_WORKERS
        chunks[worker_idx].append(addr)
    
    # Remove empty chunks if any
    chunks = [c for c in chunks if c]
    
    print(f"\n📦 Split into {len(chunks)} worker chunks")
    for idx, chunk in enumerate(chunks):
        print(f"   Worker {idx+1}: {len(chunk)} addresses")
    
    # Run workers in parallel
    print(f"\n🚀 Starting {len(chunks)} parallel workers...")
    
    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        futures = []
        for idx, chunk in enumerate(chunks):
            future = executor.submit(
                process_batch_worker,
                idx + 1,
                chunk,
                progress,
                completed_addresses,
                results
            )
            futures.append(future)
        
        # Wait for all workers to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"❌ Worker error: {e}")
    
    # Print summary
    if results:
        print("\n" + "=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)
        found = sum(1 for r in results if r['status'] == 'FOUND')
        blocked = sum(1 for r in results if r['status'] == 'BLOCKED')
        partial = sum(1 for r in results if r['status'] in ['NO_PROFILES', 'NO_PHONE'])
        errors = sum(1 for r in results if r['status'] == 'ERROR')
        print(f"   Total processed: {len(results)}")
        print(f"   ✅ Found: {found}")
        print(f"   ⛔ Blocked: {blocked}")
        print(f"   ℹ️ No data: {partial}")
        print(f"   ❌ Errors: {errors}")
        print(f"\n   📁 Results saved to: {EXCEL_INPUT} (Column C)")
    
    print(f"\n⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)


if __name__ == '__main__':
    main()
