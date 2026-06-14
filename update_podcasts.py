"""
update_podcasts.py — Henter nye podcast-episoder siden forrige oppdatering.

Bruk:
  python update_podcasts.py

Skriptet:
  1. Leser Ledelsepod.csv og finner siste kjente dato per podcast.
  2. Henter RSS-feed for hver kjent podcast.
  3. Legger til nye episoder (nyere enn siste kjente dato) med Rating=0 og tomme felt.
  4. Fjerner episoder eldre enn 3 måneder fra hovedvinduet og flytter dem til Ledelsepod_arkiv.csv.
  5. Episoder eldre enn 12 måneder fjernes helt fra arkivet.
  6. Skriver oppdatert CSV og arkiv-CSV.
"""

import calendar
import csv
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import os
import sys

# Sikre UTF-8 output i alle terminaler (Windows/Mac/Linux)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CSV_PATH      = os.path.join(os.path.dirname(__file__), "Ledelsepod.csv")
ARCHIVE_PATH  = os.path.join(os.path.dirname(__file__), "Ledelsepod_arkiv.csv")
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
    "Åpen kilde":                         "https://feeds.acast.com/public/shows/apen-kilde",
}


def extract_episode_id(link):
    """Returnerer en stabil episode-token fra lenken for dedup, eller None.

    Mange plattformer legger en stabil ID inn i URL-en (numerisk eller UUID),
    etterfulgt av en slug som kan endres når tittelen oppdateres. Funksjonen
    trekker ut den stabile delen slik at episoden ikke plukkes opp på nytt
    under en ny tittel.

    Støttede mønstre:
    - UUID i URL-banen (Acast m.fl.):
        .../episodes/a1b2c3d4-…  →  "uuid:a1b2c3d4-…"
    - Numerisk ID (≥6 siffer) etterfulgt av bindestrek eller punktum (Buzzsprout m.fl.):
        .../episodes/18912349-tittelslug.mp3  →  "numid:18912349"
      Tar siste treff slik at show-IDen i URL-en ikke forveksles med episode-IDen.
    """
    if not link:
        return None
    # UUID i URL-banen
    m = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", link, re.I)
    if m:
        return f"uuid:{m.group(1).lower()}"
    # Numerisk ID (≥6 siffer) med bindestrek/punktum som avgrenser — siste forekomst
    matches = re.findall(r"(?<=[/\-])(\d{6,})(?=[\-.])", link)
    if matches:
        return f"numid:{matches[-1]}"
    return None


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


def read_archive():
    """Returnerer (header, rows) for arkivfilen, eller (None, []) hvis den ikke finnes."""
    if not os.path.exists(ARCHIVE_PATH):
        return None, []
    with open(ARCHIVE_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return None, []
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


ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
DC_NS     = "http://purl.org/dc/elements/1.1/"

# Manuell overstyring for podcaster der RSS-feeden kun inneholder organisasjonsnavn
HOST_OVERRIDES = {
    "lederskap (nhh)": "Therese Egeland, Joel W. Berge",
    "lederliv":        "Ole Christian Apeland",
}


def _extract_host(podcast_name, item, channel):
    """Prøver å hente vertsnavn fra RSS-item, faller tilbake til HOST_OVERRIDES og channel-nivå."""
    # 1. Item-nivå (mest spesifikt)
    for el in [
        item.find(f"{{{ITUNES_NS}}}author"),
        item.find(f"{{{DC_NS}}}creator"),
    ]:
        if el is not None and el.text and el.text.strip():
            return el.text.strip()
    # 2. Kjent overstyring for denne podcasten
    override = HOST_OVERRIDES.get(podcast_name.strip().lower())
    if override:
        return override
    # 3. Channel-nivå fallback
    for el in [
        channel.find(f"{{{ITUNES_NS}}}author"),
        channel.find("managingEditor"),
    ]:
        if el is not None and el.text and el.text.strip():
            return el.text.strip()
    return ""


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
            # Enclosure-URL er mest stabil (inneholder alltid episode-ID i filnavnet).
            # <guid> kan variere mellom kjøringer (f.eks. "Buzzsprout-19196600" vs full URL) → sjekkes sist.
            enclosure = item.find("enclosure")
            link = enclosure.attrib.get("url", "") if enclosure is not None else ""
        if not link:
            guid_el = item.find("guid")
            link = guid_el.text.strip() if guid_el is not None and guid_el.text else ""

        host = _extract_host(podcast_name, item, channel)

        new_eps.append([
            podcast_name,
            title,
            "Norwegian",
            pub_dt.strftime("%Y-%m-%d"),
            host,      # Host(s) — fra RSS
            "",        # Guest(s)
            "",        # Main Topic(s)
            UNRATED,   # Rating — krever manuell vurdering
            "Ny episode — ikke vurdert ennå",
            "",        # Tags
            link,
        ])

    new_eps.sort(key=lambda r: r[3])
    return new_eps, None


def months_ago(n):
    """Returnerer dato-til-dato n måneder tilbake (samme dag, forrige måned(er))."""
    now = datetime.now(timezone.utc)
    month = now.month - n
    year  = now.year + (month - 1) // 12
    month = ((month - 1) % 12) + 1
    day = min(now.day, calendar.monthrange(year, month)[1])
    return now.replace(year=year, month=month, day=day, hour=0, minute=0, second=0, microsecond=0)


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
    arch_header, arch_existing = read_archive()
    rejected      = load_rejected()
    existing_keys = {(r[0].strip().lower(), r[1].strip().lower()) for r in existing_rows if len(r) >= 2}
    # Lenke-basert dedup: fanger opp episoder der utgiver har endret tittel mellom to hentinger.
    # Kun unike lenker (én forekomst) brukes — generiske show-URLer som deles av mange episoder
    # (f.eks. https://meyerhaugen.no/topplederpodcast/) ekskluderes for å unngå at nye episoder
    # stille droppes som duplikater.
    all_links = [
        r[10].strip().lower()
        for r in existing_rows + arch_existing
        if len(r) >= 11 and r[10].strip()
    ]
    link_counts = Counter(all_links)
    existing_links = {link for link, count in link_counts.items() if count == 1}
    # Plattform-ID-basert dedup: fanger opp tittelendringer der URL-sluggen endres men
    # episode-IDen er stabil (f.eks. Buzzsprout). Motvirker at samme episode hentes på nytt
    # med oppdatert tittel og ny slug.
    existing_episode_ids = {
        ep_id
        for r in existing_rows + arch_existing
        if len(r) >= 11
        for ep_id in [extract_episode_id(r[10])]
        if ep_id
    }
    # Dato-basert dedup: fanger opp resterende tilfeller der tittel, lenke og plattform-ID
    # alle er ulike, men dato er identisk — nesten alltid samme episode med ny tittel.
    existing_podcast_dates = {
        (r[0].strip().lower(), r[3].strip())
        for r in existing_rows + arch_existing
        if len(r) >= 4 and r[3].strip()
    }
    latest        = latest_date_per_podcast(existing_rows)

    # Rullerende 3-månedersvindu — henter ikke episoder eldre enn dette
    default_from   = months_ago(3)
    # 12-månedersgrense — episoder eldre enn dette fjernes fra arkivet
    archive_cutoff = months_ago(12)

    if arch_header is None:
        arch_header = header

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
        filtered   = [
            ep for ep, k in ep_keys
            if k not in rejected
            and k not in existing_keys
            and ep[10].lower() not in existing_links                     # lenke-basert dedup
            and extract_episode_id(ep[10]) not in existing_episode_ids  # plattform-ID-dedup
            and (ep[0].lower(), ep[3]) not in existing_podcast_dates    # dato-basert dedup
        ]
        n_rejected = sum(1 for _, k in ep_keys if k in rejected)
        n_date_dup = sum(
            1 for ep, k in ep_keys
            if k not in rejected and k not in existing_keys
            and ep[10].lower() not in existing_links
            and extract_episode_id(ep[10]) not in existing_episode_ids
            and (ep[0].lower(), ep[3]) in existing_podcast_dates
        )
        n_dup      = len(episodes) - len(filtered) - n_rejected - n_date_dup

        parts = []
        if filtered:    parts.append(f"+ {len(filtered)} ny(e)")
        if n_rejected:  parts.append(f"{n_rejected} hoppet over (forkastet)")
        if n_dup:       parts.append(f"{n_dup} duplikat(er)")
        if n_date_dup:  parts.append(f"{n_date_dup} dato-duplikat(er)")
        if not parts:   parts.append("– ingen nye")
        print(", ".join(parts))

        all_new.extend(filtered)

    all_rows = existing_rows + all_new
    cutoff_str  = default_from.strftime("%Y-%m-%d")
    archive_str = archive_cutoff.strftime("%Y-%m-%d")

    # Hovedvindu: kun episoder innen siste 3 måneder
    main_rows  = [r for r in all_rows if len(r) >= 4 and r[3].strip() >= cutoff_str]

    # Episoder 3–12 måneder gamle flyttes til arkiv
    moved_rows = [r for r in all_rows
                  if len(r) >= 4 and archive_str <= r[3].strip() < cutoff_str]

    # Slå sammen med eksisterende arkiv (deduplisering på podcast+tittel)
    arch_keys = {(r[0].strip().lower(), r[1].strip().lower())
                 for r in arch_existing if len(r) >= 2}
    new_to_archive = [r for r in moved_rows
                      if (r[0].strip().lower(), r[1].strip().lower()) not in arch_keys]
    arch_all  = arch_existing + new_to_archive

    # Beskjær arkivet: fjern episoder eldre enn 12 måneder
    arch_kept = [r for r in arch_all if len(r) >= 4 and r[3].strip() >= archive_str]
    n_arch_pruned = len(arch_all) - len(arch_kept)

    # Skriv begge filer
    n_pruned = len(all_rows) - len(main_rows)
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows([header] + main_rows)
    with open(ARCHIVE_PATH, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows([arch_header] + arch_kept)

    if not all_new:
        print("\nIngen nye episoder funnet.")
    else:
        print(f"\n{len(all_new)} nye episode(r) lagt til i CSV.")
        print(f"NB: Nye episoder har Rating={UNRATED} og vurderes automatisk av auto_rate.py.")

    if n_pruned:
        print(f"{n_pruned} episode(r) eldre enn 3 måneder flyttet til arkiv.")
    if new_to_archive:
        print(f"{len(new_to_archive)} episode(r) lagt til i Ledelsepod_arkiv.csv.")
    if n_arch_pruned:
        print(f"{n_arch_pruned} arkiverte episode(r) eldre enn 12 måneder fjernet helt.")
    print()

    pending = pending_review(main_rows)
    if pending:
        print(f"⚠  {len(pending)} episode(r) ikke vurdert etter {REVIEW_AFTER_DAYS}+ dager:\n")
        for row in pending:
            print(f"  [{row[3]}] {row[0][:30]:<30} – {row[1][:55]}")
        print()


if __name__ == "__main__":
    main()
