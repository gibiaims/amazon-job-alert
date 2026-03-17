# job_alert.py
# Amazon job checker -> Telegram notifier
# Paste this file exactly as-is into your repository.

import os
import json
import requests
from bs4 import BeautifulSoup

# Config from GitHub Actions secrets
SEARCH_URL = os.environ.get("SEARCH_URL")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

CACHE_FILE = "seen_jobs.json"
REQUEST_TIMEOUT = 15

def debug_print(*args):
    print(*args, flush=True)

def load_seen():
    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
            return set(data)
    except Exception:
        return set()

def save_seen(seen_set):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(list(seen_set), f)
    except Exception as e:
        debug_print("Warning: could not save seen file:", e)

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        debug_print("Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID; cannot send message.")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
        try:
            result = resp.json()
        except Exception:
            result = {"status_code": resp.status_code, "text": resp.text[:200]}
        if resp.status_code != 200:
            debug_print("Telegram API returned non-200:", resp.status_code, result)
            return False
        return True
    except Exception as e:
        debug_print("Error sending Telegram message:", e)
        return False

def fetch_jobs():
    if not SEARCH_URL:
        raise Exception("SEARCH_URL environment variable is missing or empty.")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Language": "en-GB,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    debug_print("Requesting:", SEARCH_URL)
    r = requests.get(SEARCH_URL, headers=headers, timeout=REQUEST_TIMEOUT)
    debug_print("HTTP STATUS:", r.status_code)
    if r.status_code != 200:
        raise Exception(f"HTTP request failed with status {r.status_code}")
    soup = BeautifulSoup(r.text, "html.parser")

    jobs = []
    # A few selectors to try — covers common Amazon job link patterns
    selectors = [
        "a[href*='/job/']",    # common job link
        "a[href*='/jobs/']",
        "div.job-tile a",      # site-specific card
        "li.job a"
    ]
    seen_links = set()
    for sel in selectors:
        for a in soup.select(sel):
            title = a.get_text(strip=True)
            link = a.get("href")
            if not link or not title:
                continue
            # Normalize relative links
            if link.startswith("/"):
                link = "https://www.amazon.jobs" + link
            # Avoid duplicates from multiple selectors
            if link in seen_links:
                continue
            seen_links.add(link)
            # Derive job id from link (last path piece) if possible
            job_id = link.rstrip("/").split("/")[-1]
            jobs.append({"id": job_id, "title": title, "link": link})
    return jobs

def main():
    debug_print("SCRIPT STARTED")
    debug_print("SEARCH_URL present:", bool(SEARCH_URL))
    debug_print("TELEGRAM_TOKEN present:", bool(TELEGRAM_TOKEN))
    debug_print("TELEGRAM_CHAT_ID present:", bool(TELEGRAM_CHAT_ID))

    try:
        seen = load_seen()
        debug_print("Loaded seen jobs:", len(seen))
        jobs = fetch_jobs()
        debug_print("Jobs found on page:", len(jobs))
    except Exception as e:
        debug_print("Fatal error while fetching jobs:", e)
        return

    new_jobs = [j for j in jobs if j["id"] not in seen]
    debug_print("New jobs (not seen before):", len(new_jobs))

    if not new_jobs:
        debug_print("No new jobs to notify.")
    else:
        for j in new_jobs[:10]:
            text = f"🚨 NEW AMAZON JOB\n\n{j['title']}\n{j['link']}"
            ok = send_telegram(text)
            debug_print("Sent?", ok, "|", j["title"])
        # Update seen set and save
        seen.update(j["id"] for j in new_jobs)
        save_seen(seen)
        debug_print("Updated seen jobs count:", len(seen))

    debug_print("SCRIPT FINISHED")

if __name__ == "__main__":
    main()
