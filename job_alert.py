# job_alert.py  (Playwright edition)
# Uses Playwright to fetch the page (avoids 403), then parses job links and notifies Telegram.

import os
import json
import time
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

SEARCH_URL = os.environ.get("SEARCH_URL")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

CACHE_FILE = "seen_jobs.json"
REQUEST_TIMEOUT = 30

def debug(*args):
    print(*args, flush=True)

def load_seen():
    try:
        with open(CACHE_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_seen(s):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(list(s), f)
    except Exception as e:
        debug("Failed to save seen file:", e)

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        debug("Missing Telegram token/chat id.")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
        debug("Telegram status:", r.status_code)
        return r.status_code == 200
    except Exception as e:
        debug("Telegram send error:", e)
        return False

def fetch_html_with_playwright(url):
    debug("Starting Playwright to fetch:", url)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page()
        # set viewport & user-agent just in case
        page.set_viewport_size({"width": 1280, "height": 800})
        page.set_extra_http_headers({"Accept-Language": "en-GB,en;q=0.9"})
        try:
            page.goto(url, wait_until="networkidle", timeout=REQUEST_TIMEOUT * 1000)
            # optional: wait for a known element or small delay
            time.sleep(1)
            html = page.content()
            return html
        finally:
            try:
                browser.close()
            except:
                pass

def parse_jobs_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    seen_links = set()
    selectors = [
        "a[href*='/job/']",
        "a[href*='/jobs/']",
        "div.job-tile a",
        "li.job a"
    ]
    for sel in selectors:
        for a in soup.select(sel):
            title = a.get_text(strip=True)
            link = a.get("href")
            if not link or not title:
                continue
            if link.startswith("/"):
                link = "https://www.amazon.jobs" + link
            if link in seen_links:
                continue
            seen_links.add(link)
            job_id = link.rstrip("/").split("/")[-1]
            jobs.append({"id": job_id, "title": title, "link": link})
    return jobs

def main():
    debug("SCRIPT STARTED")
    debug("SEARCH_URL present:", bool(SEARCH_URL))
    debug("TELEGRAM token present:", bool(TELEGRAM_TOKEN))
    debug("TELEGRAM chat id present:", bool(TELEGRAM_CHAT_ID))

    if not SEARCH_URL:
        debug("ERROR: SEARCH_URL missing")
        return

    seen = load_seen()
    debug("Seen jobs loaded:", len(seen))

    try:
        html = fetch_html_with_playwright(SEARCH_URL)
    except Exception as e:
        debug("Playwright fetch error:", e)
        return

    jobs = parse_jobs_from_html(html)
    debug("Jobs parsed:", len(jobs))

    new = [j for j in jobs if j["id"] not in seen]
    debug("New jobs:", len(new))

    if new:
        for j in new[:10]:
            text = f"🚨 NEW AMAZON JOB\n\n{j['title']}\n{j['link']}"
            ok = send_telegram(text)
            debug("Sent?", ok, "|", j["title"])
        seen.update(j["id"] for j in new)
        save_seen(seen)
    else:
        debug("No new jobs to notify.")

    debug("SCRIPT FINISHED")

if __name__ == "__main__":
    main()
