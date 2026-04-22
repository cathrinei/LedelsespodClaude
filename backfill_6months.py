"""
backfill_6months.py — Éngangsscript for å hente episoder fra de siste 6 månedene.

Ignorerer eksisterende datoer i CSV og bruker "today - 6 måneder" som cutoff
for alle podcaster — slik at episoder fra før januar 2026 som er innenfor
6-månedersvinduet også hentes inn.

Kjøres én gang, deretter slettes dette skriptet.
"""

import csv
import os
import sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Importer logikk fra update_podcasts
from update_podcasts import (
    CSV_PATH, REJECTED_PATH, FEEDS, UNRATED,
    load_rejected, read_csv, fetch_new_episodes, pending_review
)

def main():
    header, existing_rows = read_csv()
    rejected      = load_rejected()
    existing_keys = {(r[0].strip().lower(), r[1].strip().lower()) for r in existing_rows if len(r) >= 2}

    # Rullerende 6-månedersvindu — brukes for ALLE podcaster (ignorerer eksisterende datoer)
    now = datetime.now(timezone.utc)
    month = now.month - 6
    year = now.year + (month - 1) // 12
    month = ((month - 1) % 12) + 1
    cutoff = now.replace(year=year, month=month)

    print(f"\nBackfill: henter episoder etter {cutoff.strftime('%Y-%m-%d')} for alle podcaster...\n")

    all_new = []
    for podcast_name, feed_url in FEEDS.items():
        print(f"  {podcast_name[:45]:<45} (etter {cutoff.strftime('%Y-%m-%d')}) ", end="", flush=True)

        episodes, error = fetch_new_episodes(podcast_name, feed_url, cutoff)

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

    if not all_new:
        print("\nIngen nye episoder funnet — alt er allerede i CSV.\n")
    else:
        with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows([header] + existing_rows + all_new)
        print(f"\n{len(all_new)} nye episode(r) lagt til i CSV.")
        print("Kjør deretter: python auto_rate.py && python embed_csv.py\n")

if __name__ == "__main__":
    main()
