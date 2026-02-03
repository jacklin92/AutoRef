import os
import time
import re
import glob
import base64
import random
from urllib.parse import urljoin

# Selenium & Undetected Chromedriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# ================= Configuration =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "list.txt")
OUTPUT_DIR = os.path.join(BASE_DIR, "downloaded_docs")
FAILED_LOG = os.path.join(BASE_DIR, "failed_urls.txt")

# ================= 1. Driver Setup =================

def get_chrome_options(download_dir):
    """
    Generates a fresh ChromeOptions object.
    Must be called for every driver initialization attempt.
    """
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument("--window-size=1280,720")

    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "safebrowsing.enabled": True,
        "profile.default_content_settings.popups": 0
    }
    options.add_experimental_option("prefs", prefs)
    return options

def setup_driver(download_dir):
    print("Starting Chrome (Auto-detect version)...")
    
    try:
        # First attempt: Auto-match version with fresh options
        driver = uc.Chrome(
            options=get_chrome_options(download_dir), 
            headless=False, 
            use_subprocess=True
        )
    except Exception as e:
        print(f"Auto-start failed ({str(e)[:50]}...), trying version 144...")
        
        # Second attempt: Force version 144 with FRESH options
        driver = uc.Chrome(
            options=get_chrome_options(download_dir), 
            headless=False, 
            use_subprocess=True, 
            version_main=144 
        )
    
    driver.set_page_load_timeout(60)
    return driver

# ================= 2. Helper Tools =================

def human_click(driver, element):
    """Simulate human interaction: Move -> Hover -> Click"""
    try:
        ActionChains(driver).move_to_element(element).pause(random.uniform(0.2, 0.5)).click().perform()
    except:
        # Fallback to JS click if ActionChains fails
        driver.execute_script("arguments[0].click();", element)

def bypass_cloudflare(driver):
    """Handle Cloudflare checks, including iframe switching."""
    try:
        page_source = driver.page_source.lower()
        if "security check" in page_source or "verify you are human" in page_source or "challenges.cloudflare.com" in page_source:
            print("Cloudflare detected, attempting bypass...", end=" ", flush=True)
            time.sleep(2)
            
            # Try switching to iframe to click
            try:
                frames = driver.find_elements(By.XPATH, "//iframe[starts-with(@src, 'https://challenges.cloudflare.com')]")
                if frames:
                    driver.switch_to.frame(frames[0])
                    time.sleep(0.5)
                    checkbox = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                    if checkbox: human_click(driver, checkbox[0])
                    else: driver.find_element(By.TAG_NAME, "body").click()
                    driver.switch_to.default_content()
            except:
                driver.switch_to.default_content()

            # Wait for pass
            wait_start = time.time()
            while time.time() - wait_start < 20:
                if "security check" not in driver.page_source.lower():
                    print("Passed!")
                    return True
                time.sleep(1)
            print("Verification Timeout")
    except: pass
    return True

def clean_filename(title):
    if not title: return "Untitled"
    safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)
    return re.sub(r'\s+', ' ', safe_title).strip()[:100]

def extract_url(line):
    match = re.search(r'\[(https?://[^\]]+)\]', line)
    if match: return match.group(1)
    match = re.search(r'(https?://\S+)', line)
    if match: return match.group(1).rstrip(')')
    return None

def wait_for_new_file(folder, existing_files, timeout=30):
    end_time = time.time() + timeout
    while time.time() < end_time:
        current_files = set(glob.glob(os.path.join(folder, "*.pdf")))
        new_files = current_files - existing_files
        temp_files = glob.glob(os.path.join(folder, "*.crdownload"))
        if new_files and not temp_files:
            return max(list(new_files), key=os.path.getctime)
        time.sleep(1)
    return None

def save_webpage_as_pdf(driver, output_path):
    try:
        result = driver.execute_cdp_cmd("Page.printToPDF", {
            'landscape': False, 'displayHeaderFooter': False,
            'printBackground': True, 'preferCSSPageSize': True,
        })
        with open(output_path, 'wb') as f:
            f.write(base64.b64decode(result['data']))
        return True
    except: return False

# ================= 3. Site Handlers =================

def handle_ieee(driver, url):
    match = re.search(r'document/(\d+)', url)
    if match:
        driver.get(f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={match.group(1)}")
        return True
    return False

def handle_pubmed(driver, url):
    driver.get(url)
    bypass_cloudflare(driver)
    try:
        pmc_link = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.link-item.pmc"))
        )
        driver.get(pmc_link.get_attribute("href"))
        bypass_cloudflare(driver)
        WebDriverWait(driver, 10).until(lambda d: d.title != "")
        return True
    except: return False

def find_pdf_element(driver):
    """Strategy to find PDF download elements across different sites."""
    # 1. ResearchGate
    if "researchgate.net" in driver.current_url:
        try: return driver.find_element(By.XPATH, "//a[contains(translate(., 'DOWNLOAD', 'download'), 'download full-text pdf')]")
        except:
            try: return driver.find_element(By.CSS_SELECTOR, "a.nova-legacy-c-button--theme-brand-primary")
            except: pass

    # 2. PMC
    elif "pmc.ncbi.nlm.nih.gov" in driver.current_url:
        try: return driver.find_element(By.CSS_SELECTOR, ".int-view")
        except: pass

    # 3. Generic (Meta Tag)
    try:
        meta = driver.find_element(By.CSS_SELECTOR, "meta[name='citation_pdf_url']")
        return meta
    except: pass

    # 4. Generic (Button Scan)
    try:
        links = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf') or contains(@href, '/pdf')]")
        for link in links:
            if link.get_attribute("href") and "javascript" not in link.get_attribute("href"):
                text = link.text.lower()
                if "download" in text or "pdf" in text:
                    return link
    except: pass
    
    return None

# ================= 4. Main Process =================

def process_single_url(driver, seq, url):
    print(f"[{seq}] {url[-30:]} ...", end=" ", flush=True)
    
    try:
        existing_pdfs = set(glob.glob(os.path.join(OUTPUT_DIR, "*.pdf")))
        
        # --- Navigation ---
        if "ieeexplore.ieee.org" in url and "document" in url:
            handle_ieee(driver, url)
        elif "pubmed.ncbi.nlm.nih.gov" in url:
            handle_pubmed(driver, url)
        else:
            driver.get(url)
            bypass_cloudflare(driver)

        # Wait for load
        try: WebDriverWait(driver, 10).until(lambda d: d.title != "")
        except: pass

        # --- Detection & Action ---
        page_title = clean_filename(driver.title) or "Document"
        final_filename = f"{seq}_{page_title}.pdf"
        target_path = os.path.join(OUTPUT_DIR, final_filename)
        if os.path.exists(target_path): os.remove(target_path)

        element = find_pdf_element(driver)
        pdf_triggered = False

        if element:
            if element.tag_name == 'meta':
                driver.get(element.get_attribute("content"))
                bypass_cloudflare(driver)
                pdf_triggered = True
            else:
                try:
                    print("Clicking", end=" ")
                    human_click(driver, element)
                    bypass_cloudflare(driver)
                    pdf_triggered = True
                except:
                    # Fallback to direct href navigation
                    href = element.get_attribute("href")
                    if href:
                        driver.get(href)
                        bypass_cloudflare(driver)
                        pdf_triggered = True

        # --- Validation & Printing ---
        download_success = False
        if pdf_triggered or "ieeexplore" in url:
            new_file = wait_for_new_file(OUTPUT_DIR, existing_pdfs, timeout=30)
            if new_file:
                try:
                    for _ in range(3):
                        # Removed specific OSError catch
                        try:
                            os.rename(new_file, target_path)
                            download_success = True
                            print("PDF Downloaded")
                            return "PDF", None
                        except Exception: 
                            time.sleep(1)
                except: pass

        if not download_success:
            if "security check" in driver.page_source.lower():
                 print("Blocked")
                 return "FAIL", "Blocked"
            
            # If URL ends in PDF but no file, browser might be previewing it.
            if driver.current_url.endswith(".pdf"):
                pass 
            elif len(driver.page_source) < 500:
                try: driver.back()
                except: driver.get(url)
            
            print("WebPrint", end=" ")
            if save_webpage_as_pdf(driver, target_path):
                print("OK")
                return "WebPrint", None
            else:
                print("Fail")
                return "FAIL", "Print Failed"

    except Exception as e:
        return "FAIL", str(e)

def main():
    print(f"Working Directory: {BASE_DIR}")
    if not os.path.exists(INPUT_FILE):
        print("Error: list.txt not found")
        return
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    
    # Clean temp files
    for tmp in glob.glob(os.path.join(OUTPUT_DIR, "*.crdownload")):
        try: os.remove(tmp)
        except: pass

    tasks = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            u = extract_url(line)
            if u: tasks.append((f"{i+1:02d}", u))

    print(f"Starting Optimized Script | Tasks: {len(tasks)}")
    
    driver = setup_driver(OUTPUT_DIR)
    
    stats = {"PDF": 0, "WebPrint": 0, "FAIL": 0}
    failed_list = []

    try:
        for seq, url in tasks:
            result, msg = process_single_url(driver, seq, url)
            stats[result] += 1
            if result == "FAIL":
                failed_list.append(f"{seq} | {url} | {msg}")
            
            time.sleep(random.uniform(2, 4))

    except KeyboardInterrupt:
        print("\nInterrupted...")
    finally:
        try:
            if driver:
                driver.quit()
                driver.service.process.kill()
        except: pass

    if failed_list:
        with open(FAILED_LOG, 'w', encoding='utf-8') as f:
            for item in failed_list:
                f.write(item + '\n')

    print(f"\nPDF: {stats['PDF']} | Print: {stats['WebPrint']} | Fail: {stats['FAIL']}")

if __name__ == "__main__":
    main()