"""
rate_runner.py — Stabil kjørelogikk for episodeevaluering.

Ikke ment å kjøres direkte. Importeres av rate_episodes.py som kun
inneholder UPDATES og REMOVE_KEYWORDS, kjøres én gang, og slettes.
"""

import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CSV_PATH      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Ledelsepod.csv")
REJECTED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rejected_episodes.csv")


def normalize(s):
    return s.strip().lower()


def _find_update(updates, podcast, title):
    p, t = normalize(podcast), normalize(title)
    for (kpod, kword), val in updates.items():
        if p == kpod and kword in t:
            return val
    return None


def _should_remove(remove_keywords, podcast, title):
    p, t = normalize(podcast), normalize(title)
    return any(p == kpod and kword in t for kpod, kword in remove_keywords)


def append_rejected(removed_rows):
    """Skriver forkastede episoder til rejected_episodes.csv (unngår duplikater)."""
    existing = set()
    if os.path.exists(REJECTED_PATH):
        with open(REJECTED_PATH, encoding="utf-8", newline="") as f:
            for r in csv.reader(f):
                if len(r) >= 2 and r[0] != "Podcast Name":
                    existing.add((normalize(r[0]), normalize(r[1])))

    new_entries = [r for r in removed_rows
                   if (normalize(r[0]), normalize(r[1])) not in existing]
    if not new_entries:
        return

    with open(REJECTED_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if not existing:
            w.writerow(["Podcast Name", "Episode Title"])
        for row in new_entries:
            w.writerow([row[0], row[1]])


def run(updates, remove_keywords):
    """Kjør raterunde med gitt UPDATES-dict og REMOVE_KEYWORDS-liste."""
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    updated = 0
    removed_rows = []
    unmatched = []
    kept = []

    for row in rows:
        if len(row) < 11:
            row += [""] * (11 - len(row))

        podcast, title = row[0], row[1]

        if _should_remove(remove_keywords, podcast, title):
            removed_rows.append(row)
            continue

        match = _find_update(updates, podcast, title)
        if match:
            host, guest, topics, rating, notes, tags = match
            row[4] = host
            row[5] = guest
            row[6] = topics
            row[7] = str(rating)
            row[8] = notes
            row[9] = tags
            updated += 1
        elif row[7].strip() == "0":
            unmatched.append(f"  [{row[3]}] {podcast[:30]} — {title[:60]}")

        kept.append(row)

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows([header] + kept)

    if removed_rows:
        append_rejected(removed_rows)

    print(f"\nOK {updated} episoder oppdatert med rating/noter/tags")
    print(f"OK {len(removed_rows)} episoder fjernet (rating 1-3) og lagt til rejected_episodes.csv")
    print(f"OK {len(kept)} episoder beholdt i CSV")

    if unmatched:
        print(f"\nWARN {len(unmatched)} episoder uten treff i UPDATES (beholdt med Rating=0):")
        for u in unmatched:
            print(u)
