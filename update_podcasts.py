"""
update_podcasts.py — Henter nye podcast-episoder siden forrige oppdatering.

Bruk:
  python update_podcasts.py

Skriptet:
  1. Leser Ledelsepod.csv og finner siste kjente dato per podcast.
  2. Henter RSS-feed for hver kjent podcast.
  3. Legger til nye episoder (nyere enn siste kjente dato) med Rating=0 og tomme felt.
  4. Fjerner episoder eldre enn 6 måneder fra CSV.
  5. Skriver oppdatert CSV.
"""

import csv
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import os
import sys

# Sikre UTF-8 output i alle terminaler (Windows/Mac/Linux)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CSV_PATH      = os.path.join(os.path.dirname(__file__), "Ledelsepod.csv")
REJECTED_PATH = os.path.join(os.path.dirname(__file__), "rejected_episodes.csv")

UNRATED = "0"  # Markør for episoder som mangler manuell vurdering
REVIEW_AFTER_DAYS = 2  # Antall dager før urangerte episoder flagges for vurdering

# RSS-feeds per podcast. Legg til nye her for å utvide dekningen.
FEEDS = {
    "Lederpodden":                        "https://feeds.captivate.fm/lederpodden/",
    "Lederskap (NHH)":                    "https://feeds.acast.com/public/shows/lederskap",
    "Lederliv":                           "https://feeds.acast.com/public/shows/lederliv",
    "HR-podden":                          "https://rss.buzzsprout.com/1929646.rss",
    "Topplederpodcast (MeyerHaugen)":     "https://feeds.acast.com/public/shows/633560a50d27d30012586207",
    "The Office – Ledelse, jobb og juss": "https://anchor.fm/s/110039498/podcast/rss",
    "Smidigpodden":                       "https://feeds.acast.com/public/shows/62b2e41c423bc40013892e2d",
    "Psykologkameratene":                 "https://feed.podbean.com/psykologkameratene/feed.xml",
}


def load_rejected():
    """Returnerer set av (podcast_name.lower(), title.lower()) fra rejected_episodes.csv."""
    if not os.path.exists(REJECTED_PATH):
        return set()
    with open(REJECTED_PATH, encoding="utf-8", newline="") as f:
        return {
            (r[0].strip().lower(), r[1].strip().lower())
            for r in csv.reader(f)
            if len(r) >= 2 and r[0] != "Podcast Name"
        }


def read_csv():
    if not os.path.exists(CSV_PATH):
        print(f"FEIL: Finner ikke {CSV_PATH}")
        sys.exit(1)
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        sys.exit("FEIL: CSV-filen er tom.")
    return rows[0], rows[1:]


def latest_date_per_podcast(rows):
    """Returnerer {podcast_name: datetime} med siste kjente dato per podcast."""
    latest = {}
    for row in rows:
        if len(row) < 4:
            continue
        name = row[0].strip()
        try:
            dt = datetime.strptime(row[3].strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if name not in latest or dt > latest[name]:
            latest[name] = dt
    return latest


def fetch_feed(url):
    req = urllib.request.Request(url, headers={"User-Agent": "LedelsepodCrawler/1.0 (privat bruk)"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read(), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return None, str(e.reason)


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str).astimezone(timezone.utc)
    except Exception:
        return None


def fetch_new_episodes(podcast_name, feed_url, after_dt):
    """Returnerer (episoder, feilmelding). Episoder er None ved feil, [] hvis ingen nye."""
    raw, error = fetch_feed(feed_url)
    if raw is None:
        return None, error

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        return None, f"XML-feil: {e}"

    channel = root.find("channel")
    if channel is None:
        return None, "Ugyldig RSS-format (mangler <channel>)"

    new_eps = []
    for item in channel.findall("item"):
        title_el = item.find("title")
        title = title_el.text.strip() if title_el is not None else ""

        pub_el = item.find("pubDate")
        pub_dt = parse_date(pub_el.text if pub_el is not None else None)
        if pub_dt is None or pub_dt <= after_dt:
            continue

        link_el = item.find("link")
        link = link_el.text.strip() if link_el is not None and link_el.text else ""
        if not link:
            enclosure = item.find("enclosure")
            link = enclosure.attrib.get("url", "") if enclosure is not None else ""

        new_eps.append([
            podcast_name,
            title,
            "Norwegian",
            pub_dt.strftime("%Y-%m-%d"),
            "",        # Host(s)
            "",        # Guest(s)
            "",        # Main Topic(s)
            UNRATED,   # Rating — krever manuell vurdering
            "Ny episode — ikke vurdert ennå",
            "",        # Tags
            link,
        ])

    new_eps.sort(key=lambda r: r[3])
    return new_eps, None


def pending_review(rows):
    """Returnerer urangerte episoder publisert for mer enn REVIEW_AFTER_DAYS siden."""
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=REVIEW_AFTER_DAYS)
    pending = []
    for row in rows:
        if len(row) < 8:
            continue
        if row[7].strip() != UNRATED:
            continue
        try:
            pub = datetime.strptime(row[3].strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if pub <= cutoff:
            pending.append(row)
    return pending


def main():
    header, existing_rows = read_csv()
    rejected      = load_rejected()
    existing_keys = {(r[0].strip().lower(), r[1].strip().lower()) for r in existing_rows if len(r) >= 2}
    latest        = latest_date_per_podcast(existing_rows)
    # Rullerende 6-månedersvindu — henter ikke episoder eldre enn dette
    now = datetime.now(timezone.utc)
    month = now.month - 6
    year = now.year + (month - 1) // 12
    month = ((month - 1) % 12) + 1
    default_from  = now.replace(year=year, month=month)

    all_new = []
    print(f"\nSjekker {len(FEEDS)} podcast-feeder...\n")

    for podcast_name, feed_url in FEEDS.items():
        after_dt = latest.get(podcast_name, default_from)
        print(f"  {podcast_name[:45]:<45} (etter {after_dt.strftime('%Y-%m-%d')}) ", end="", flush=True)

        episodes, error = fetch_new_episodes(podcast_name, feed_url, after_dt)

        if episodes is None:
            print(f"! Feil: {error}")
            continue

        ep_keys    = [(ep, (ep[0].lower(), ep[1].lower())) for ep in episodes]
        filtered   = [ep for ep, k in ep_keys if k not in rejected and k not in existing_keys]
        n_rejected = sum(1 for _, k in ep_keys if k in rejected)
        n_dup      = len(episodes) - len(filtered) - n_rejected

        parts = []
        if filtered:   parts.append(f"+ {len(filtered)} ny(e)")
        if n_rejected: parts.append(f"{n_rejected} hoppet over (forkastet)")
        if n_dup:      parts.append(f"{n_dup} duplikat(er)")
        if not parts:  parts.append("– ingen nye")
        print(", ".join(parts))

        all_new.extend(filtered)

    # Beskjær til siste 6 måneder
    all_rows = existing_rows + all_new
    pruned = [r for r in all_rows if len(r) >= 4 and r[3].strip() >= default_from.strftime("%Y-%m-%d")]
    n_pruned = len(all_rows) - len(pruned)

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows([header] + pruned)

    if not all_new:
        print("\nIngen nye episoder funnet.")
    else:
        print(f"\n{len(all_new)} nye episode(r) lagt til i CSV.")
        print(f"NB: Nye episoder har Rating={UNRATED} og vurderes automatisk av auto_rate.py.")

    if n_pruned:
        print(f"{n_pruned} episode(r) eldre enn 6 måneder fjernet fra CSV.")
    print()

    pending = pending_review(pruned)
    if pending:
        print(f"⚠  {len(pending)} episode(r) ikke vurdert etter {REVIEW_AFTER_DAYS}+ dager:\n")
        for row in pending:
            print(f"  [{row[3]}] {row[0][:30]:<30} – {row[1][:55]}")
        print()


if __name__ == "__main__":
    main()
