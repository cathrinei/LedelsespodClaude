# LedelsepodClaude – Project Context

## Purpose
This project collects and curates Norwegian-language podcast episodes on **teamledelse** (team leadership) and **personalledelse** (people management / HR), published in 2026.

## Repository & publisering
- **GitHub:** https://github.com/cathrinei/LedelsespodClaude
- **GitHub Pages:** https://cathrinei.github.io/LedelsespodClaude/Ledelsepod_2026.html
- Branch: `master` — push til master oppdaterer GitHub Pages automatisk

## Files
- `Ledelsepod_2026.csv` — master data, one row per episode
- `Ledelsepod_2026.html` — interactive table with filtering, sorting, stats (CSV import button hidden)
- `README.md` — prosjektbeskrivelse med lenke til GitHub Pages
- `update_podcasts.py` — RSS fetcher; adds new episodes (Rating=0) since last known date per podcast
- `auto_rate.py` — automatisk vurdering av Rating=0-episoder via Claude API (claude-haiku-4-5)
- `rate_runner.py` — stabil kjørelogikk for manuell episodeevaluering; importeres av `rate_episodes.py`
- `rate_episodes.py` — data-only (UPDATES + REMOVE_KEYWORDS); skrives per raterunde, slettes etter bruk
- `embed_csv.py` — skriver CSV-innholdet inn i HTML-filens `data`-array; kjøres etter hver raterunde
- `rejected_episodes.csv` — denylist; episodes here are never re-fetched by `update_podcasts.py`
- `.github/workflows/update_podcasts.yml` — GitHub Actions workflow; daglig kjøring deaktivert inntil videre, manuell trigger tilgjengelig

## CSV columns

| Column | Description |
|---|---|
| Podcast Name | Official show name |
| Episode Title | Specific episode title |
| Language | Norwegian (alle episoder i dette prosjektet) |
| Published Date | YYYY-MM-DD |
| Host(s) | Host names |
| Guest(s) | Guest names (if notable) |
| Main Topic(s) | Key subjects covered |
| Rating (1–6) | See rubric below |
| Rating Notes | 1–2 sentence justification |
| Tags | Comma-separated — see tag schema below |
| Platform / Link | URL to episode or show |

## CSV policy
- **Only episodes rated 4–6 are kept.** Episodes rated 1–3 are removed entirely.
- **Unrated episodes (Rating=0 / N/A)** are rated automatically by `auto_rate.py` — no manual review needed.
- Always update the CSV **before** the HTML when making data changes. CSV is the source of truth.
- Do not add short videos, teasers, trailers, or highlight compilations — full-length episodes only.

## Tag schema

Two layers — combine with comma (e.g. `teamledelse,feedback`):

**Kategorier** (bruk for episoder som er klart innenfor ett av de to temaene):

| Tag | Når det brukes |
|---|---|
| `teamledelse` | Episoden handler primært om å lede team, teamdynamikk, samarbeid, kollektiv prestasjon |
| `personalledelse` | Episoden handler primært om personalarbeid, HR, individuell medarbeiderutvikling, ansettelse |

**Temataggs** (valgfrie, ved sterk tilknytning til et undertema):

| Tag | Når det brukes |
|---|---|
| `feedback` | Feedback-kultur, tilbakemeldingssamtaler, åpenhet |
| `kultur` | Organisasjonskultur, verdier, psykologisk trygghet |
| `rekruttering` | Ansettelse, onboarding, talentutvikling |
| `motivasjon` | Motivasjon, engasjement, trivsel |
| `coaching` | Coaching, mentoring, individuelle utviklingssamtaler |

## Rating rubric (1–6)

| Score | Label | Meaning |
|---|---|---|
| 6 | Eksepsjonell | Dyp ledelsesfaglig innsikt, ekspert-gjester/-verter, høy praktisk eller forskningsmessig verdi |
| 5 | Svært nyttig | Solid innhold om ledelse, tydelig fokus, pålitelig og informativt |
| 4 | Nyttig | Relevant ledelsesstoff; kan være overflatenivå eller ledelse er ett av flere temaer |
| 3 | Delvis relevant | Beholdes ikke — fjernes fra CSV |
| 2 | Marginal | Beholdes ikke — fjernes fra CSV |
| 1 | Ikke relevant | Beholdes ikke — fjernes fra CSV |

## Podcast sources

| Show | RSS |
|---|---|
| Lederpodden | https://feeds.captivate.fm/lederpodden/ |
| Lederskap (NHH) | https://feeds.acast.com/public/shows/lederskap |
| Lederliv | https://feeds.acast.com/public/shows/lederliv |
| HR-podden | https://rss.buzzsprout.com/1929646.rss |
| Topplederpodcast (MeyerHaugen) | https://feeds.acast.com/public/shows/633560a50d27d30012586207 |
| The Office – Ledelse, jobb og juss | https://anchor.fm/s/110039498/podcast/rss |
| Smidigpodden | https://feeds.acast.com/public/shows/62b2e41c423bc40013892e2d |
| Psykologkameratene | https://feed.podbean.com/psykologkameratene/feed.xml |

## HTML – tekniske noter

### Data array
The `data` array in the HTML is populated from the CSV via `embed_csv.py`. Unrated episodes (Rating=0) display as **N/A** and always pass through the rating filter.

### Stats
`updateStats()` computes all stats from the `data` array:
- Total episodes, shows, teamledelse-tagged count, personalledelse-tagged count, top-rated (6/6), unrated (N/A)

### "↑ Last inn CSV"-knappen
- Knappen er skjult (`display:none`) — data oppdateres automatisk via GitHub Actions
- Funksjonaliteten er beholdt i koden (kan vises igjen ved å fjerne `style="display:none"`)
- Logikk: åpner fil-picker, leser med `FileReader` (UTF-8, maks 5 MB), `parseCSV()` → `data`-array → `updateStats()` + `refresh()`

### Dark mode
- Toggle button (☾ Mørk / ☀ Lys) in top-right of header
- Preference persisted in `localStorage` (`darkMode` key)
- Deep forest green gradient header (`#0b1f10 → #1e4a30`) — distinguishes from the AI project's blue theme
- Dark mode uses deep black-green background (`#080d08`) with bright green accent (`#4ade80`)

### Tag filter
- Rendered as clickable **pill buttons** (not a `<select>`) — IDs: `.tag-pill` with `data-tag` attribute
- Active tag stored in JS module-level variable `let activeTag = ''` — pills set it directly, `getFiltered()` reads it
- `resetFilters()` sets `activeTag = ''` and resets active pill state

### Podcast filter
- `<select id="podcastFilter">` — placed to the right of the rating filter in the controls bar
- Options populated dynamically from the `data` array (unique podcast names, alphabetically sorted) on page load
- Filters table to a single show; `resetFilters()` resets it to `""` (Alle podkaster)

### Øvrige tekniske noter
- Language column (index 2) is kept in CSV/data array but **not displayed** in the table — all episodes are Norwegian
- Sort: `sort` object (`col`, `asc`); `RATING_COL = 7`, `DATE_COL = 3` — default sort is date descending (newest first)
- `data-col` in table headers refers to **data array indices** (col 2 is skipped in table display — so `data-col="3"` = date, `data-col="4"` = hosts, etc.)
- Tags whitelisted via `tagMeta` — 7 tags: `teamledelse`, `personalledelse`, `feedback`, `kultur`, `rekruttering`, `motivasjon`, `coaching`
- Tags can be combined (comma-separated); `tagsOf(row)` helper used for all tag checks
- `safeUrl()` blocks non-HTTP(S) URLs to prevent `javascript:` injection
- CSP: `default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'`
- Default filter on load: rating 4+; N/A episodes always shown regardless of filter
- CSV upload capped at 5 MB
- Controls bar is **sticky** (`position: sticky; top: 0`) — stays visible while scrolling
- Rating badges use solid colors (no gradient): green `#166534` (6), blue `#1d4ed8` (5), purple `#6d28d9` (4) — with subtle `box-shadow` ring
- Rows get `data-rating` attribute in `renderTable()` — used for CSS left-border accent per rating level (`td:first-child`)
- Thin vertical column dividers: `rgba(255,255,255,0.08)` on `thead th:not(:last-child)`, `var(--row-border)` on `tbody td:not(:last-child)`
- Column header and cell horizontal padding: `1.1rem`
- `--text-faint` darkened to `#526b55` (light) / `#5a9060` (dark) — passes WCAG AA (≥4.5:1)
- Rating badge class applied with `+rating >= 1` (not array `.includes()`) to handle string values from data array
- `getFiltered()` uses `+rating` for numeric coercion — handles both string (pre-populated) and int (CSV-loaded) rating values
- `updateStats()` runs a single pass over `data` to compute all six stats
- `data` array is **pre-populated** in the HTML via `embed_csv.py` — no manual CSV import needed

## update_podcasts.py – tekniske noter
- `FEEDS` dict: add new podcasts with name (must match CSV) and RSS URL — 8 feeds currently
- Fetches only episodes newer than last known date per podcast (`latest_date_per_podcast`)
- `User-Agent` set to `LedelsepodCrawler/1.0 (privat bruk)` — honest identifier, not browser spoofing
- Language hardcoded to `"Norwegian"` for all fetched episodes (Norwegian-only project)
- New episodes get `Rating=0` — automatically rated by `auto_rate.py` in the next step
- `pending_review()` runs at end of every execution using `existing_rows + all_new` (no second file read) — flags unrated episodes older than 5 days
- `REVIEW_AFTER_DAYS = 2` constant controls the threshold
- Errors distinguish between HTTP errors and network errors
- `REJECTED_PATH` points to `rejected_episodes.csv` — loaded via `load_rejected()` at startup
- `existing_keys` built from current CSV rows — prevents re-adding duplicates within CSV
- New episodes filtered against both `rejected` and `existing_keys` before being appended
- Per-feed output shows: `+ N ny(e)`, `N hoppet over (forkastet)`, `N duplikat(er)` as relevant

## auto_rate.py – tekniske noter
- Krever `pip install anthropic` og miljøvariabel `ANTHROPIC_API_KEY`
- Leser CSV, finner alle rader med `Rating=0`, kaller Claude API for hver
- Modell: `claude-haiku-4-5` (kostnadseffektiv)
- Prompt caching: `cache_control: {type: "ephemeral"}` på system-prompten — rubrikk og tagskjema caches på tvers av alle episoder i samme kjøring
- Svarformat: JSON med feltene `host`, `guest`, `main_topics`, `rating`, `rating_notes`, `tags`
- Rating 4–6: beholdes i CSV med utfylte felt
- Rating 1–3: fjernes fra CSV og skrives til `rejected_episodes.csv` (med deduplicering via `normalize()`)
- Output: norske statusmeldinger med `OK`/`WARN`-prefixer, samme stil som `rate_runner.py`
- I GitHub Actions: kjøres med `ANTHROPIC_API_KEY` fra repository secret

## rate_runner.py – tekniske noter
- Stabil fil med all kjørelogikk — aldri slettes
- Eksponerer én funksjon: `run(updates, remove_keywords)`
- Internt: `_find_update()`, `_should_remove()`, `_append_rejected()` — alle prefixet `_` (ikke ment for direkte bruk)
- `WARN`-output viser kun episoder med `Rating=0` uten treff i `UPDATES` — allerede ratede episoder vises ikke
- `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` sikrer korrekt output i Windows-terminal (emojis i titler)

## rate_episodes.py – tekniske noter
- Skrives på nytt for hver raterunde — kun data, ~10–15 linjer
- Inneholder `UPDATES`-dict og `REMOVE_KEYWORDS`-liste, importerer og kaller `run()` fra `rate_runner.py`
- `UPDATES`: nøkkel `(podcast_name_lower, title_keyword_lower)` → `(host, guest, topics, rating, notes, tags)` — substring-matching mot tittel
- `REMOVE_KEYWORDS`: episoder som fjernes fra CSV og skrives til `rejected_episodes.csv`
- Kjøres én gang og slettes etter bruk

## rejected_episodes.csv – tekniske noter
- Two columns: `Podcast Name`, `Episode Title` (case-insensitive matching)
- Episodes here are **never re-added** by `update_podcasts.py`, regardless of date
- Auto-populated by `rate_episodes.py` when episodes are removed (rated 1–3)
- Can also be edited manually to block specific episodes permanently
- `_append_rejected()` in `rate_runner.py` deduplicates before writing — safe to run multiple times; uses `normalize()` for consistent casing and a single `os.path.exists` check

## Workflow

### Automatisk (GitHub Actions — deaktivert inntil videre)
- Daglig kjøring (10:15 Oslo-tid) er kommentert ut i `.github/workflows/update_podcasts.yml`
- Aktiveres ved å uncommente `schedule`-blokken og sette `ANTHROPIC_API_KEY` som repository secret
- Manuell trigger (Actions-knapp i GitHub) er fortsatt tilgjengelig

### Manuelt (lokalt)
1. `python update_podcasts.py` — henter nye episoder
2. `python auto_rate.py` — vurderer automatisk (krever `ANTHROPIC_API_KEY`)
3. `python embed_csv.py` — oppdaterer HTML
4. `git add Ledelsepod_2026.csv Ledelsepod_2026.html && git commit -m "..." && git push`

### Manuell overstyring (ved behov)
- Skriv `rate_episodes.py` med `UPDATES`-dict og `REMOVE_KEYWORDS`-liste, kjør det — patcher spesifikke episoder
- For å blokkere en episode permanent: legg til manuelt i `rejected_episodes.csv`
- For å legge til en ny podcast: legg til RSS-feed i `FEEDS`-dicten i `update_podcasts.py`

### Branch-workflow (for større endringer)
Bruk en egen branch for nye features — merge til master når klar.

```
# Start ny branch
git checkout -b navn-på-branch

# Jobb normalt, commit og push
git add .
git commit -m "Beskrivelse"
git push -u origin navn-på-branch
```

**Merge via GitHub (anbefalt):**
- GitHub foreslår automatisk en Pull Request når du pusher en ny branch
- Review endringene, merge, og slett branchen i GitHub-grensesnittet

**Merge via terminal:**
```
git checkout master
git merge navn-på-branch
git push
git branch -d navn-på-branch  # slett branch lokalt
```
7. **Etter HTML-endringer — WCAG AA-sjekk:** verifiser følgende før publisering:
   - **Kontrast:** all brødtekst ≥ 4.5:1, stor tekst (18pt / 14pt bold) ≥ 3:1 — sjekk både lys og mørk modus
   - **Nye interaktive elementer:** knapper og lenker må ha synlig tekst eller `aria-label`; skjemafelt må ha tilknyttet `<label>` eller `aria-label`
   - **Tabellhoder:** nye `<th>`-elementer må ha `scope="col"` eller `scope="row"`
   - **Dekorative ikoner:** unicode-tegn og SVG-ikoner som ikke er meningsbærende skal ha `aria-hidden="true"`
   - **Tilstandsknapper (toggle/filter):** bruk `aria-pressed` for av/på-knapper, `aria-sort` for sorterbare kolonner
   - **Fokus:** alle interaktive elementer skal ha synlig `:focus-visible`-stil
   - **Farge som eneste signal:** ny informasjon som bare formidles via farge er ikke tillatt — legg til tekst, ikon eller mønster
   - **Live-regioner:** dynamisk innhold (f.eks. radteller, statusmeldinger) skal ha `aria-live="polite"`
