import os
import json
import time
import re
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SEEN_PATH = "seen.json"

# URLs do Kleinanzeigen (suas buscas)
KLEIN_URLS = [
    "https://www.kleinanzeigen.de/s-tuba/k0",
    "https://www.kleinanzeigen.de/s-f-tuba/k0",
    "https://www.kleinanzeigen.de/s-alte-tuba/k0",
    "https://www.kleinanzeigen.de/s-deko-tuba/k0",
    "https://www.kleinanzeigen.de/s-eb-tuba/k0",
    "https://www.kleinanzeigen.de/s-es-tuba/k0",
    "https://www.kleinanzeigen.de/s-kaiser-tuba/k0",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TubaRadar/1.0)",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8,pt-BR;q=0.7",
}

def tg_send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": text,
            "disable_web_page_preview": False
        },
        timeout=20
    )

def load_seen():
    try:
        with open(SEEN_PATH, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_seen(seen):
    with open(SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(list(seen)), f, ensure_ascii=False, indent=2)

def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()

def scan_kleinanzeigen(url, limit=20):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    local_seen = set()

    for a in soup.select('a[href*="/s-anzeige/"]'):
        href = a.get("href")
        if not href:
            continue

        if href.startswith("/"):
            link = "https://www.kleinanzeigen.de" + href
        else:
            link = href

        if link in local_seen:
            continue
        local_seen.add(link)

        title = clean_text(a.get_text(" ", strip=True))
        if len(title) < 6:
            continue

        results.append({
            "id": link,
            "title": title,
            "link": link
        })

        if len(results) >= limit:
            break

    return results

def main():
    seen = load_seen()
    new_items = []

    for url in KLEIN_URLS:
        try:
            items = scan_kleinanzeigen(url)
        except Exception as e:
            tg_send(f"⚠️ Erro ao acessar Kleinanzeigen:\n{url}\n{e}")
            continue

        for item in items:
            if item["id"] in seen:
                continue
            seen.add(item["id"])
            new_items.append((url, item))

    if new_items:
        tg_send(f"🎺 Kleinanzeigen: {len(new_items)} anúncio(s) novo(s).")
        for i, (src, item) in enumerate(new_items[:12], start=1):
            tg_send(
                f"🔔 NOVO ({i}/{min(len(new_items),12)})\n"
                f"{item['title']}\n"
                f"{item['link']}\n"
                f"Busca: {src}"
            )
            time.sleep(1.1)

        save_seen(seen)
    else:
        print("Nada novo.")

if __name__ == "__main__":
    main()
