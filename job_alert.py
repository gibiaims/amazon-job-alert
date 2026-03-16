import os, json, requests
from bs4 import BeautifulSoup

SEARCH_URL = os.environ.get("SEARCH_URL")
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
CACHE_FILE = "seen_jobs.json"

def fetch_jobs():
    r = requests.get(SEARCH_URL, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    jobs = []
    for a in soup.select("a[href*='/job/'], a[href*='/jobs/']"):
        title = a.get_text(strip=True)
        link = a.get("href")
        if not link: continue
        if link.startswith("/"): link = "https://www.amazon.jobs" + link
        job_id = link.split("/")[-1]
        jobs.append({"id": job_id, "title": title, "link": link})
    return jobs

def load_seen():
    try:
        with open(CACHE_FILE) as f:
            return set(json.load(f))
    except:
        return set()

def save_seen(s):
    with open(CACHE_FILE, "w") as f:
        json.dump(list(s), f)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)

def main():
    if not SEARCH_URL:
        print("SEARCH_URL missing")
        return
    seen = load_seen()
    jobs = fetch_jobs()
    new = [j for j in jobs if j["id"] not in seen]
    for j in new[:10]:
        send_telegram(f"🚨 NEW AMAZON JOB\n\n{j['title']}\n{j['link']}")
    if new:
        seen.update(j["id"] for j in new)
        save_seen(seen)

if __name__ == "__main__":
    main()
