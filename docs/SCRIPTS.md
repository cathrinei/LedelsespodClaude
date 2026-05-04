# Script-tekniske noter

## update_podcasts.py
- `FEEDS` dict: add new podcasts with name (must match CSV) and RSS URL — 8 feeds currently
- Fetches only episodes newer than last known date per podcast (`latest_date_per_podcast`)
- `User-Agent` set to `LedelsepodCrawler/1.0 (privat bruk)` — honest identifier, not browser spoofing
- Language hardcoded to `"Norwegian"` for all fetched episodes (Norwegian-only project)
- New episodes get `Rating=0` — automatically rated by `auto_rate.py` in the next step
- **Rullerende 3-månedersvindu:** episoder eldre enn 3 måneder flyttes fra `Ledelsepod.csv` til `Ledelsepod_arkiv.csv` på hver kjøring
- **Arkiv 3–12 måneder:** `Ledelsepod_arkiv.csv` beholder episoder mellom 3 og 12 måneder gamle; eldre fjernes helt
- `months_ago(n)` beregner eksakt dato-til-dato n måneder tilbake (f.eks. 2026-05-04 → 2026-02-04); bruker `calendar.monthrange` for å håndtere kanttilfeller som 31. jan → 28. feb
- `default_from` = `months_ago(3)` — brukes som fallback hente-grense per podcast hvis ingen kjent dato finnes
- Arkivering og opprydding skjer alltid basert på `datetime.now()` — uavhengig av siste hentingsdato
- `pending_review()` runs at end of every execution — flags unrated episodes older than `REVIEW_AFTER_DAYS = 2` days
- Errors distinguish between HTTP errors and network errors
- `REJECTED_PATH` points to `rejected_episodes.csv` — loaded via `load_rejected()` at startup
- `existing_keys` built from current CSV rows — prevents re-adding duplicates within CSV
- New episodes filtered against both `rejected` and `existing_keys` before being appended
- Per-feed output shows: `+ N ny(e)`, `N hoppet over (forkastet)`, `N duplikat(er)` as relevant
- `_extract_host(podcast_name, item, channel)` henter vertsnavn direkte fra RSS — prioriteringsrekkefølge: `itunes:author` (item) → `dc:creator` (item) → `HOST_OVERRIDES` → `itunes:author` (channel) → `managingEditor` (channel)
- `HOST_OVERRIDES` dict: manuell overstyring for podcaster der RSS kun inneholder forkortet navn eller organisasjonsnavn — aktive oppføringer: Lederskap (NHH) → "Therese Egeland, Joel W. Berge", Lederliv → "Ole Christian Apeland"

## auto_rate.py
- Krever `pip install openai` og miljøvariabel `GITHUB_TOKEN`
- `GITHUB_TOKEN` er alltid tilgjengelig i GitHub Actions — ingen secrets å sette opp
- Bruker GitHub Models via OpenAI-kompatibelt API: `https://models.inference.ai.azure.com`
- Modell: `gpt-4o-mini` (gratis for offentlige repos, 150 req/dag)
- Leser CSV, finner alle rader med `Rating=0`, kaller API for hver episode
- Svarformat: JSON med feltene `host`, `guest`, `main_topics`, `rating`, `rating_notes`, `tags`
- `SYSTEM_PROMPT` inneholder eksplisitte språkkrav: korrekt bokmål, unngå anglisismer («tangentielt» → «perifert berørt», «hovemotiv» → «hovedmotiv»)
- `host`-feltet fra modellen brukes kun hvis RSS-hentet vertsnavn mangler (RSS har prioritet)
- Rating 4–6: beholdes i CSV med utfylte felt
- Rating 1–3: fjernes fra CSV og skrives til `rejected_episodes.csv` (med deduplicering via `normalize()`)
- Ingen gyldig respons / ugyldig rating: telles i `failed_attempts.csv` — fjernes fra CSV og re-prøves neste kjøring; etter `MAX_ATTEMPTS=3` forsøk sendes episoden til `rejected_episodes.csv`
- `load_failed_attempts()` / `save_failed_attempts()` — laster/lagrer `failed_attempts.csv` som `{(podcast_lower, title_lower): attempts}`; skriving hoppes over hvis dict er uendret
- `_handle_failure()` — felles helper for None-respons og ugyldig rating; returnerer True ved auto-forkasting
- `append_rejected` og `normalize` importeres fra `rate_runner`
- Nøkkel fjernes fra `failed_attempts` når episode får gyldig rating (uansett om den beholdes eller forkastes)
- Ingen N/A-episoder skal bli liggende i CSV etter en vellykket kjøring
- Output: norske statusmeldinger med `OK`/`FJERNES`/`FORKASTES`-prefixer

## embed_csv.py
- Leser `Ledelsepod.csv`, serialiserer hver rad som JSON og erstatter `const data = [...]` i `Ledelsepod.html`
- Validerer: fil finnes, CSV har minst én daterad, header har ≥ 11 kolonner, JSON-serialisering lykkes — `sys.exit(1)` med tydelig feilmelding ved alle feil
- Rader med færre enn 11 kolonner paddes med tomme strenger
- `re.subn` forventer nøyaktig 1 treff på `const data = \[.*?\]` — feiler hvis mønsteret ikke finnes eller matcher flere ganger

## rate_runner.py
- Stabil fil med all kjørelogikk — aldri slettes
- Eksponerer: `run(updates, remove_keywords)`, `append_rejected(removed_rows)`, `normalize(s)`
- Internt: `_find_update()`, `_should_remove()` — substring-matching mot tittel
- `append_rejected` brukes også av `auto_rate.py` (importert) — single source of truth for rejected-logikk
- `WARN`-output viser kun episoder med `Rating=0` uten treff i `UPDATES` — allerede ratede episoder vises ikke
- `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` sikrer korrekt output i Windows-terminal (emojis i titler)

## rate_episodes.py
- Skrives på nytt for hver raterunde — kun data, ~10–15 linjer
- Inneholder `UPDATES`-dict og `REMOVE_KEYWORDS`-liste, importerer og kaller `run()` fra `rate_runner.py`
- `UPDATES`: nøkkel `(podcast_name_lower, title_keyword_lower)` → `(host, guest, topics, rating, notes, tags)` — substring-matching mot tittel
- `REMOVE_KEYWORDS`: episoder som fjernes fra CSV og skrives til `rejected_episodes.csv`
- Kjøres én gang og slettes etter bruk

## rejected_episodes.csv
- Two columns: `Podcast Name`, `Episode Title` (case-insensitive matching)
- Episodes here are **never re-added** by `update_podcasts.py`, regardless of date
- Auto-populated by `auto_rate.py` (rating 1–3 or MAX_ATTEMPTS exceeded) and `rate_runner.py`
- Can also be edited manually to block specific episodes permanently
- `append_rejected()` in `rate_runner.py` deduplicates before writing — safe to run multiple times
