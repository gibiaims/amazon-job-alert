import os
import json
import requests
from bs4 import BeautifulSoup

print("SCRIPT STARTED")

SEARCH_URL = os.environ.get("SEARCH_URL")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

print("SEARCH_URL:", SEARCH_URL)
print("TOKEN PRESENT:", TELEGRAM_TOKEN is not None)
print("CHAT ID:", TELEGRAM_CHAT_ID)

CACHE_FILE = "seen_jobs.json"

if not SEARCH_URL:
    raise Exception("SEARCH_URL secret missing")

def fetch_jobs():
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-GB,en;q=0.9",
    "Referer": "https://www.google.com/"
}

r = requests.get(SEARCH_URL, headers=headers)
    print("HTTP STATUS:", r.status_code)

    soup = BeautifulSoup(r.text, "html.parser")
    jobs = []

    for a in soup.select("a[href*='/job/']"):
        title = a.get_text(strip=True)
        link = a.get("href")

        if link.startswith("/"):
            link = "https://www.amazon.jobs" + link

        job_id = link.split("/")[-1]

        jobs.append({
            "id": job_id,
            "title": title,
            "link": link
        })

    print("JOBS FOUND:", len(jobs))
    return jobs

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    })

jobs = fetch_jobs()

for job in jobs[:1]:
    send_telegram(f"TEST JOB FOUND\n{job['title']}")

print("SCRIPT FINISHED")
