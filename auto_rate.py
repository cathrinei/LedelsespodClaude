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
  5. Episoder uten gyldig respons telles i failed_attempts.csv;
     etter MAX_ATTEMPTS mislykkede forsøk sendes de til rejected_episodes.csv
"""

import csv
import json
import os
import sys

from openai import OpenAI
from rate_runner import append_rejected, normalize

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CSV_PATH    = os.path.join(BASE_DIR, "Ledelsepod.csv")
FAILED_PATH = os.path.join(BASE_DIR, "failed_attempts.csv")
MAX_ATTEMPTS = 3

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


def load_failed_attempts() -> dict[tuple[str, str], int]:
    """Leser failed_attempts.csv og returnerer {(podcast_lower, title_lower): attempts}."""
    if not os.path.exists(FAILED_PATH):
        return {}
    result: dict[tuple[str, str], int] = {}
    with open(FAILED_PATH, encoding="utf-8", newline="") as f:
        for r in csv.reader(f):
            if len(r) >= 3 and r[0] != "Podcast Name":
                try:
                    result[(normalize(r[0]), normalize(r[1]))] = int(r[2])
                except ValueError:
                    pass
    return result


def save_failed_attempts(attempts: dict[tuple[str, str], int]) -> None:
    """Skriver failed_attempts.csv fra dict."""
    with open(FAILED_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Podcast Name", "Episode Title", "Attempts"])
        for (podcast, title), count in attempts.items():
            w.writerow([podcast, title, count])


def _handle_failure(
    failed_attempts: dict, key: tuple, row: list, i: int,
    reason: str, removed_rows: list, rows_to_remove: set
) -> bool:
    """Teller opp feil for en episode. Returnerer True hvis episoden nå auto-forkastes."""
    attempts = failed_attempts.get(key, 0) + 1
    if attempts >= MAX_ATTEMPTS:
        print(f"    FORKASTES  {reason}, {attempts} forsøk — sendes til rejected_episodes.csv\n")
        removed_rows.append(row)
        rows_to_remove.add(i)
        failed_attempts.pop(key, None)
        return True
    print(f"    FJERNES  {reason} — forsøk {attempts}/{MAX_ATTEMPTS}, re-prøves neste kjøring\n")
    rows_to_remove.add(i)
    failed_attempts[key] = attempts
    return False


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
    failed_attempts = load_failed_attempts()
    failed_attempts_initial = dict(failed_attempts)
    auto_rejected = 0

    for i, row in unrated:
        while len(row) < 11:
            row.append("")

        podcast  = row[0]
        title    = row[1]
        pub_date = row[3]
        link     = row[10]
        key      = (normalize(podcast), normalize(title))

        print(f"  → [{pub_date}] {podcast[:30]} — {title[:60]}")

        result = rate_episode(client, podcast, title, pub_date, link)
        if result is None:
            if _handle_failure(failed_attempts, key, row, i, "Ingen gyldig respons", removed_rows, rows_to_remove):
                auto_rejected += 1
            continue

        rating_raw = result.get("rating", 0)
        try:
            rating = int(rating_raw)
        except (ValueError, TypeError):
            rating = 0

        if rating <= 0 or rating > 6:
            if _handle_failure(failed_attempts, key, row, i, f"Ugyldig rating ({rating_raw})", removed_rows, rows_to_remove):
                auto_rejected += 1
            continue

        failed_attempts.pop(key, None)

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

    if failed_attempts != failed_attempts_initial:
        save_failed_attempts(failed_attempts)

    if removed_rows:
        append_rejected(removed_rows)

    print(f"OK {updated} episoder vurdert og beholdt (rating 4–6)")
    print(f"OK {len(removed_rows) - auto_rejected} episoder fjernet (rating 1–3) og lagt til rejected_episodes.csv")
    if auto_rejected:
        print(f"OK {auto_rejected} episoder forkastet etter {MAX_ATTEMPTS} mislykkede forsøk")
    print(f"OK {len(kept)} episoder totalt i CSV")


if __name__ == "__main__":
    main()
