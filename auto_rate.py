"""
auto_rate.py — Automatisk vurdering av uraterte episoder (Rating=0) via GitHub Models.

Bruk:
  python auto_rate.py

Krever:
  pip install openai
  Miljøvariabel GITHUB_TOKEN satt (tilgjengelig automatisk i GitHub Actions)

Hva skriptet gjør:
  1. Leser Ledelsepod.csv og finner episoder med Rating=0
  2. Kaller gpt-4o-mini via GitHub Models for å vurdere hver episode
  3. Episoder med rating 4-6 beholdes i CSV med utfylte felt
  4. Episoder med rating 1-3 fjernes fra CSV og skrives til rejected_episodes.csv
"""

import csv
import json
import os
import sys

from openai import OpenAI

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CSV_PATH      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Ledelsepod.csv")
REJECTED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rejected_episodes.csv")

SYSTEM_PROMPT = """Du er en ekspert på norske ledelsespodcaster. Din oppgave er å vurdere om en podkastepisode er relevant for temaene **teamledelse** eller **personalledelse**, og gi den en rating.

## Vurderingsskala (1–6)

| Score | Betydning |
|---|---|
| 6 | Eksepsjonell — Dyp ledelsesfaglig innsikt, ekspert-gjester/-verter, høy praktisk eller forskningsmessig verdi |
| 5 | Svært nyttig — Solid innhold om ledelse, tydelig fokus, pålitelig og informativt |
| 4 | Nyttig — Relevant ledelsesstoff; kan være overflatenivå eller ledelse er ett av flere temaer |
| 3 | Delvis relevant — Berører ledelse, men ikke primærfokus |
| 2 | Marginal — Svak kobling til ledelse |
| 1 | Ikke relevant — Handler ikke om ledelse |

## Taggsystem

Du skal alltid inkludere én kategorietag og eventuelt relevante tematagger.

**Kategorietagger (velg én):**
- `teamledelse` — Episoden handler primært om å lede team, teamdynamikk, samarbeid, kollektiv prestasjon
- `personalledelse` — Episoden handler primært om personalarbeid, HR, individuell medarbeiderutvikling, ansettelse

**Tematagger (valgfrie, ved sterk tilknytning):**
- `feedback` — Feedback-kultur, tilbakemeldingssamtaler, åpenhet
- `kultur` — Organisasjonskultur, verdier, psykologisk trygghet
- `rekruttering` — Ansettelse, onboarding, talentutvikling
- `motivasjon` — Motivasjon, engasjement, trivsel
- `coaching` — Coaching, mentoring, individuelle utviklingssamtaler

## Svarformat

Svar alltid med gyldig JSON og ingen annen tekst:

{
  "host": "vertsnavn eller tom streng hvis ukjent",
  "guest": "gjestenavn eller tom streng hvis ingen gjest",
  "main_topics": "korte emneord, kommaseparert",
  "rating": <heltall 1-6>,
  "rating_notes": "1–2 setninger på norsk som begrunner ratingen",
  "tags": "kommaseparerte tagger, f.eks. teamledelse,feedback"
}"""


def normalize(s: str) -> str:
    return s.strip().lower()


def append_rejected(removed_rows: list[list]) -> None:
    """Legger forkastede episoder til rejected_episodes.csv (unngår duplikater)."""
    existing: set[tuple[str, str]] = set()
    file_exists = os.path.exists(REJECTED_PATH)
    if file_exists:
        with open(REJECTED_PATH, encoding="utf-8", newline="") as f:
            for r in csv.reader(f):
                if len(r) >= 2 and r[0] != "Podcast Name":
                    existing.add((normalize(r[0]), normalize(r[1])))

    write_header = not file_exists or os.path.getsize(REJECTED_PATH) == 0
    new_entries = [r for r in removed_rows
                   if (normalize(r[0]), normalize(r[1])) not in existing]
    if not new_entries:
        return

    with open(REJECTED_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["Podcast Name", "Episode Title"])
        for row in new_entries:
            w.writerow([row[0], row[1]])


def rate_episode(client: OpenAI, podcast: str, title: str,
                 pub_date: str, link: str) -> dict | None:
    """Kaller GitHub Models og returnerer ratingdata som dict, eller None ved feil."""
    user_msg = (
        f"Podcast: {podcast}\n"
        f"Tittel: {title}\n"
        f"Publisert: {pub_date}\n"
        f"Lenke: {link}\n\n"
        "Vurder denne episoden og svar med JSON som beskrevet i systemprompten."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=512,
        )
        text = response.choices[0].message.content or ""
        # Strip markdown code fences if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"WARN JSON-feil for '{title[:60]}': {e}")
        return None
    except Exception as e:
        print(f"WARN API-feil for '{title[:60]}': {e}")
        return None


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("FEIL: Miljøvariabel GITHUB_TOKEN er ikke satt.")
        sys.exit(1)

    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=token,
    )

    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    unrated = [(i, r) for i, r in enumerate(rows)
               if len(r) > 7 and r[7].strip() == "0"]

    if not unrated:
        print("OK Ingen uraterte episoder funnet.")
        return

    print(f"OK Fant {len(unrated)} uraterte episode(r) — starter vurdering...\n")

    updated = 0
    removed_rows = []
    rows_to_remove = set()

    for i, row in unrated:
        while len(row) < 11:
            row.append("")

        podcast  = row[0]
        title    = row[1]
        pub_date = row[3]
        link     = row[10]

        print(f"  → [{pub_date}] {podcast[:30]} — {title[:60]}")

        result = rate_episode(client, podcast, title, pub_date, link)
        if result is None:
            print(f"    WARN Hopper over (ingen gyldig respons)\n")
            continue

        rating = int(result.get("rating", 0))

        if rating <= 0 or rating > 6:
            print(f"    WARN Ugyldig rating ({rating}) — hopper over\n")
            continue

        if rating <= 3:
            print(f"    FJERNES  Rating {rating} — {result.get('rating_notes', '')[:80]}")
            removed_rows.append(row)
            rows_to_remove.add(i)
        else:
            row[4] = row[4] or result.get("host", "") or ""
            row[5] = result.get("guest", row[5]) or row[5]
            row[6] = result.get("main_topics", row[6]) or row[6]
            row[7] = str(rating)
            row[8] = result.get("rating_notes", "")
            row[9] = result.get("tags", "")
            rows[i] = row
            updated += 1
            print(f"    OK  Rating {rating} — {result.get('rating_notes', '')[:80]}")

        print()

    kept = [r for i, r in enumerate(rows) if i not in rows_to_remove]

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows([header] + kept)

    if removed_rows:
        append_rejected(removed_rows)

    print(f"OK {updated} episoder vurdert og beholdt (rating 4–6)")
    print(f"OK {len(removed_rows)} episoder fjernet (rating 1–3) og lagt til rejected_episodes.csv")
    print(f"OK {len(kept)} episoder totalt i CSV")


if __name__ == "__main__":
    main()
