# LedelsepodClaude – Project Context

## Purpose
This project collects and curates Norwegian-language podcast episodes on **teamledelse** (team leadership) and **personalledelse** (people management / HR) — always the rolling last 6 months. Dataset starts from January 2026 (Oct–Dec 2025 episodes unavailable from RSS feeds).

## Repository & publisering
- **GitHub:** https://github.com/cathrinei/LedelsespodClaude
- **GitHub Pages:** https://cathrinei.github.io/LedelsespodClaude/Ledelsepod.html
- Branch: `master` — push til master oppdaterer GitHub Pages automatisk

## Files
- `Ledelsepod.csv` — master data, one row per episode (rullerende 6 måneder)
- `Ledelsepod.html` — interactive table with filtering, sorting, stats (CSV import button hidden)
- `README.md` — prosjektbeskrivelse med lenke til GitHub Pages
- `update_podcasts.py` — RSS fetcher; adds new episodes (Rating=0) since last known date per podcast
- `auto_rate.py` — automatisk vurdering av Rating=0-episoder via GitHub Models (gpt-4o-mini, gratis)
- `rate_runner.py` — stabil kjørelogikk for manuell episodeevaluering; importeres av `rate_episodes.py`
- `rate_episodes.py` — data-only (UPDATES + REMOVE_KEYWORDS); skrives per raterunde, slettes etter bruk
- `embed_csv.py` — skriver CSV-innholdet inn i HTML-filens `data`-array; kjøres etter hver raterunde
- `rejected_episodes.csv` — denylist; episodes here are never re-fetched by `update_podcasts.py`
- `.github/workflows/update_podcasts.yml` — GitHub Actions workflow; kjører daglig kl 10:15, manuell trigger tilgjengelig
- `.gitignore` — ekskluderer `__pycache__/`, `*.pyc`, `*.pyo`, `.env`

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
- Four stat cards are clickable filter shortcuts (`.stat-btn`): **Episoder** (reset all), **Teamledelse** (tag filter), **Personalledelse** (tag filter), **Toppkarakter 6/6** (rating=6)
- Active stat card gets green background; clicking again toggles the filter off
- `updateStatBtns()` syncs active state of stat cards with current filter state; called after every filter action and from `resetFilters()`

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
- Tags in the table rows are also clickable (`<button class="tag">`) — clicking filters the table and syncs the tag pills in the controls bar; clicking the same tag again clears the filter
- Event delegation on `#tableBody` handles tag clicks — avoids re-binding on every `renderTable()` call
- Active row tag gets `outline: 2px solid currentColor` to signal selected state

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
- Episode titles are rendered as `<a class="cell-title">` links — clicking opens the episode URL in a new tab; styled to look like plain text (no underline until hover)
- `safeUrl()` blocks non-HTTP(S) URLs to prevent `javascript:` injection
- CSP: `default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'`
- Default filter on load: rating 4+; N/A episodes always shown regardless of filter
- CSV upload capped at 5 MB
- Controls bar is **sticky** (`position: sticky; top: 0`) — stays visible while scrolling
- Rating badges use solid colors (no gradient): green `#166534` (6), blue `#1d4ed8` (5), purple `#6d28d9` (4) — with subtle `box-shadow` ring
- Rows get `data-rating` attribute in `renderTable()` — used for CSS left-border accent per rating level (`td:first-child`)
- Thin vertical column dividers: `rgba(255,255,255,0.08)` on `thead th:not(:last-child)`, `var(--table-divider)` on `tbody td:not(:last-child)`
- Horizontal row dividers: `border-bottom: 1px solid var(--table-divider)` on `tbody tr` — begge bruker `--table-divider` (`#7a9c7e` lyst / `#4a6e4c` mørkt) for tydelig og konsistent rutenett
- Column header and cell horizontal padding: `1.1rem`
- `--text-faint` darkened to `#526b55` (light) / `#5a9060` (dark) — passes WCAG AA (≥4.5:1)
- Rating badge class applied with `+rating >= 1` (not array `.includes()`) to handle string values from data array
- `getFiltered()` uses `+rating` for numeric coercion — handles both string (pre-populated) and int (CSV-loaded) rating values
- `updateStats()` runs a single pass over `data` to compute all six stats
- `data` array is **pre-populated** in the HTML via `embed_csv.py` — no manual CSV import needed

### Mobilvisning (≤600px)
- Breakpoint `@media (max-width: 600px)` bytter fra tabell til kortlayout
- `renderTable()` injiserer en `<td class="card-cell" colspan="10">` per rad via `insertAdjacentHTML` — skjult på desktop, synlig på mobil
- Kortet viser: podcastnavn, rating-badge, klikkbar tittel, dato, vert, tags, Lytt-knapp. Gjester, emner og begrunnelse utelates
- Tabell og `<thead>` skjules med `display:none` på mobil; `tbody tr` blir `display:block` med kortutseende
- Rating-fargekant (`border-left`) bevares på `<tr>` også i kortvisning
- Header stables vertikalt, stats vises i 2-kolonners grid, kontroller full bredde på mobil
- Dark mode fungerer automatisk via CSS-variabler

## update_podcasts.py – tekniske noter
- `FEEDS` dict: add new podcasts with name (must match CSV) and RSS URL — 8 feeds currently
- Fetches only episodes newer than last known date per podcast (`latest_date_per_podcast`)
- `User-Agent` set to `LedelsepodCrawler/1.0 (privat bruk)` — honest identifier, not browser spoofing
- Language hardcoded to `"Norwegian"` for all fetched episodes (Norwegian-only project)
- New episodes get `Rating=0` — automatically rated by `auto_rate.py` in the next step
- Episodes older than 6 months are pruned from the CSV on every run (rullerende vindu)
- `default_from` beregnes dynamisk som `today - 6 months` — ikke lenger hardkodet til 2026
- `pending_review()` runs at end of every execution using pruned rows — flags unrated episodes older than 5 days
- `REVIEW_AFTER_DAYS = 2` constant controls the threshold
- Errors distinguish between HTTP errors and network errors
- `REJECTED_PATH` points to `rejected_episodes.csv` — loaded via `load_rejected()` at startup
- `existing_keys` built from current CSV rows — prevents re-adding duplicates within CSV
- New episodes filtered against both `rejected` and `existing_keys` before being appended
- Per-feed output shows: `+ N ny(e)`, `N hoppet over (forkastet)`, `N duplikat(er)` as relevant
- `_extract_host(podcast_name, item, channel)` henter vertsnavn direkte fra RSS — prioriteringsrekkefølge: `itunes:author` (item) → `dc:creator` (item) → `HOST_OVERRIDES` → `itunes:author` (channel) → `managingEditor` (channel)
- `HOST_OVERRIDES` dict: manuell overstyring for podcaster der RSS kun inneholder forkortet navn eller organisasjonsnavn — aktive oppføringer: Lederskap (NHH) → "Therese Egeland, Joel W. Berge", Lederliv → "Ole Christian Apeland"

## auto_rate.py – tekniske noter
- Krever `pip install openai` og miljøvariabel `GITHUB_TOKEN`
- `GITHUB_TOKEN` er alltid tilgjengelig i GitHub Actions — ingen secrets å sette opp
- Bruker GitHub Models via OpenAI-kompatibelt API: `https://models.inference.ai.azure.com`
- Modell: `gpt-4o-mini` (gratis for offentlige repos, 150 req/dag)
- Leser CSV, finner alle rader med `Rating=0`, kaller API for hver episode
- Svarformat: JSON med feltene `host`, `guest`, `main_topics`, `rating`, `rating_notes`, `tags`
- `host`-feltet fra modellen brukes kun hvis RSS-hentet vertsnavn mangler (RSS har prioritet)
- Rating 4–6: beholdes i CSV med utfylte felt
- Rating 1–3: fjernes fra CSV og skrives til `rejected_episodes.csv` (med deduplicering via `normalize()`)
- Ingen gyldig respons / ugyldig rating: fjernes midlertidig fra CSV, legges **ikke** i `rejected_episodes.csv` — re-hentes og re-prøves neste kjøring
- Ingen N/A-episoder skal bli liggende i CSV etter en vellykket kjøring
- Output: norske statusmeldinger med `OK`/`FJERNES`-prefixer

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

### Automatisk (GitHub Actions — aktiv)
- Kjører daglig kl 10:15 Oslo-tid
- Ingen secrets nødvendig — bruker `GITHUB_TOKEN` (automatisk tilgjengelig)
- Manuell trigger tilgjengelig via Actions-knappen i GitHub

### Manuelt (lokalt)
1. `python update_podcasts.py` — henter nye episoder
2. `python auto_rate.py` — vurderer automatisk (krever `GITHUB_TOKEN` satt i miljøet)
3. `python embed_csv.py` — oppdaterer HTML
4. `git add Ledelsepod.csv Ledelsepod.html && git commit -m "..." && git push`

### Manuell overstyring (ved behov)
- Skriv `rate_episodes.py` med `UPDATES`-dict og `REMOVE_KEYWORDS`-liste, kjør det — patcher spesifikke episoder
- For å blokkere en episode permanent: legg til manuelt i `rejected_episodes.csv`
- For å legge til en ny podcast: legg til RSS-feed i `FEEDS`-dicten i `update_podcasts.py`

### Branch-workflow
**Alltid opprett en ny branch når datoen er ny** — bruk dato som branchnavn (`YYYY-MM-DD`):

**CLAUDE.md skal alltid committes i samme commit som kodeendringene den dokumenterer** — ikke i en separat PR etterpå.

```
git checkout -b 2026-04-23
git push -u origin 2026-04-23
```

All utvikling skjer på datobranchen. Merge til master via PR når sesjonen er ferdig.

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

### Branch protection (Rulesets)
Repoet har en ruleset på `master` satt opp via Settings → Rules → Rulesets:
- **Bypass:** Repository admin (cathrinei) — kan pushe direkte og overstyre regler
- **Rule:** Restrict deletions — ingen kan slette master-branchen
- `github-actions[bot]` er ikke tilgjengelig som bypass-aktør på gratis plan; boten kan pushe fordi kun `Restrict deletions` er aktivert (ikke push-restriksjoner)
7. **Etter HTML-endringer — WCAG AA-sjekk:** verifiser følgende før publisering:
   - **Kontrast:** all brødtekst ≥ 4.5:1, stor tekst (18pt / 14pt bold) ≥ 3:1 — sjekk både lys og mørk modus
   - **Nye interaktive elementer:** knapper og lenker må ha synlig tekst eller `aria-label`; skjemafelt må ha tilknyttet `<label>` eller `aria-label`
   - **Tabellhoder:** nye `<th>`-elementer må ha `scope="col"` eller `scope="row"`
   - **Dekorative ikoner:** unicode-tegn og SVG-ikoner som ikke er meningsbærende skal ha `aria-hidden="true"`
   - **Tilstandsknapper (toggle/filter):** bruk `aria-pressed` for av/på-knapper, `aria-sort` for sorterbare kolonner
   - **Fokus:** alle interaktive elementer skal ha synlig `:focus-visible`-stil
   - **Farge som eneste signal:** ny informasjon som bare formidles via farge er ikke tillatt — legg til tekst, ikon eller mønster
   - **Live-regioner:** dynamisk innhold (f.eks. radteller, statusmeldinger) skal ha `aria-live="polite"`

## WCAG AA — kjente anbefalte forbedringer (ikke kritiske)

Disse er identifisert men ikke utbedret — kan tas ved anledning:

| Element | Forbedring |
|---|---|
| `.stat-btn` (`role="button"`) | Mangler eksplisitt `:focus-visible`-stil — arver ikke fra standard `button`-selector |
| `#rowCount` | Har `aria-live="polite"` men mangler `role="status"` for semantisk klarhet |
| Stjerne-ikon `&#9733;` i kolonneheader | Bør ha `aria-hidden="true"` |
| `header .subtitle` | Kontrast `rgba(255,255,255,0.55)` på mørk bakgrunn er marginal (~4.5:1) |
| `.ep-card` (mobilkort) | Mangler semantisk `role="article"` eller tilsvarende landmark |
| `<caption>` i tabell | Bør stå rett etter `<table>` — nå plassert etter `<thead>` |
