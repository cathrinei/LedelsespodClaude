# LedelsepodClaude – Project Context

## Purpose
This project collects and curates Norwegian-language podcast episodes on **teamledelse** (team leadership) and **personalledelse** (people management / HR) — rolling last 3 months in the main view; episodes 3–12 months old are archived in `Ledelsepod_arkiv.csv`. Dataset starts from January 2026 (Oct–Dec 2025 episodes unavailable from RSS feeds).

## Repository & publisering
- **GitHub:** https://github.com/cathrinei/LedelsespodClaude
- **GitHub Pages:** https://cathrinei.github.io/LedelsespodClaude/Ledelsepod.html
- Branch: `master` — push til master oppdaterer GitHub Pages automatisk

## Files
- `Ledelsepod.csv` — master data, one row per episode (rullerende 3 måneder)
- `Ledelsepod_arkiv.csv` — arkivdata, episoder 3–12 måneder gamle (rullerende); eldre fjernes helt
- `Ledelsepod.html` — interactive table with filtering, sorting, stats (CSV import button hidden); stats-bar viser «+ N arkiverte»-knapp som toggles arkivvisning (3–12 mnd)
- `README.md` — prosjektbeskrivelse med lenke til GitHub Pages
- `update_podcasts.py` — RSS fetcher; adds new episodes (Rating=0) since last known date per podcast
- `auto_rate.py` — automatisk vurdering av Rating=0-episoder via GitHub Models (gpt-4o-mini, gratis)
- `rate_runner.py` — stabil kjørelogikk for manuell episodeevaluering; importeres av `rate_episodes.py`
- `rate_episodes.py` — data-only (UPDATES + REMOVE_KEYWORDS); skrives per raterunde, slettes etter bruk
- `embed_csv.py` — skriver CSV-innholdet inn i HTML-filens `data`- og `archiveData`-array; kjøres etter hver raterunde
- `rejected_episodes.csv` — denylist; episodes here are never re-fetched by `update_podcasts.py`
- `failed_attempts.csv` — teller mislykkede API-forsøk per episode; etter `MAX_ATTEMPTS=3` forsøk sendes episoden automatisk til `rejected_episodes.csv`
- `.github/workflows/update_podcasts.yml` — GitHub Actions workflow; kjører onsdag og fredag kl 23:05, manuell trigger tilgjengelig
- `.gitignore` — ekskluderer `__pycache__/`, `*.pyc`, `*.pyo`, `.env`
- `docs/HTML_NOTES.md` — tekniske detaljer om Ledelsepod.html (stats, filter, mobil, dark mode osv.)
- `docs/SCRIPTS.md` — tekniske detaljer om alle Python-skript og CSV-filer

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
- **3-month main window:** `Ledelsepod.csv` holds only the last 3 months. Older episodes move automatically to `Ledelsepod_arkiv.csv` (kept up to 12 months, then deleted).
- Always update the CSV **before** the HTML when making data changes. CSV is the source of truth.
- Do not add short videos, teasers, trailers, or highlight compilations — full-length episodes only.

## Tag schema

Two layers — combine with comma (e.g. `teamledelse,feedback`):

**Kategorier** (bruk for episoder som er klart innenfor ett av de tre temaene):

| Tag | Når det brukes |
|---|---|
| `teamledelse` | Episoden handler primært om å lede team, teamdynamikk, samarbeid, kollektiv prestasjon |
| `personalledelse` | Episoden handler primært om personalarbeid, HR, individuell medarbeiderutvikling, ansettelse |
| `produktledelse` | Episoden handler primært om produktledelse, produktstrategi, produkteierskap, roadmap-prioritering eller digital produktutvikling |

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
| Åpen kilde | https://feeds.acast.com/public/shows/apen-kilde |

## Workflow

### Automatisk (GitHub Actions — aktiv)
- Kjører onsdag og fredag kl 23:05 Oslo-tid
- Ingen secrets nødvendig — bruker `GITHUB_TOKEN` (automatisk tilgjengelig)
- Manuell trigger tilgjengelig via Actions-knappen i GitHub
- Steg: fetch → rate → embed → **valider data-array** → commit/push → kjøringssammendrag
- Valideringssteget (`Valider data-array i HTML`) parser `const data = [...]` som JSON og feiler jobben hvis arrayen er ugyldig — forhindrer at korrupt HTML pushes

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

**Unntak — direkte til master:** rene dataoppdateringer (hente nye episoder, arkivere gamle) committes direkte til master uten branch og PR. GitHub Actions gjør dette automatisk; ved manuell kjøring gjelder samme regel.

**CLAUDE.md skal alltid committes i samme commit som kodeendringene den dokumenterer** — ikke i en separat PR etterpå.

```bash
git checkout -b 2026-04-30
git push -u origin 2026-04-30
```

All utvikling skjer på datobranchen. Merge til master via PR når sesjonen er ferdig.

**Merge via GitHub (anbefalt):**
- GitHub foreslår automatisk en Pull Request når du pusher en ny branch
- Review endringene, merge, og slett branchen i GitHub-grensesnittet

### Opprydding av branches og PRer
**Påminnelse hver 7. dag:** slett gamle branches og lukkede PRer.

```bash
# Slett alle remote branches unntatt master
git branch -r | grep -v "HEAD\|master" | sed 's/origin\///' | xargs -I{} git push origin --delete {}

# Rydd opp lokale tracking-refs og slett lokale branches
git fetch --prune
git branch | grep -v "master" | xargs git branch -d
```

### Branch protection (Rulesets)
Branch protection er fjernet — ingen rulesets aktive på `master`.
- **Utvikling:** alltid via branch + PR (se branch-workflow over)
- **GitHub Actions:** pusher direkte til master som unntak — nødvendig for den automatiske daglige oppdateringen (fetch → rate → embed → push)

## Etter HTML-endringer — kvalitetskontroll
Kjør HTMLHint og ESLint ved endringer i `Ledelsepod.html`:
```bash
npx htmlhint Ledelsepod.html
# Trekk ut JS og lint (se under for ESLint-oppsett)
node -e "const fs=require('fs'),h=fs.readFileSync('Ledelsepod.html','utf8'),m=h.match(/<script>([\s\S]*?)<\/script>/g);fs.writeFileSync('_temp_lint.js',m.map((s,i)=>'// block '+(i+1)+'\n'+s.replace(/<\/?script[^>]*>/g,'')).join('\n'));"
npx eslint _temp_lint.js && rm _temp_lint.js
```

Kjør Lighthouse for helhetlig kvalitetssjekk (Performance, Accessibility, Best Practices, SEO):
```bash
python -m http.server 7731 --bind 127.0.0.1 &
npx lighthouse http://127.0.0.1:7731/Ledelsepod.html --output=json,html --output-path=./lighthouse-report --chrome-flags="--headless --no-sandbox --disable-gpu --user-data-dir=C:/Temp/lighthouse-chrome" --only-categories=performance,accessibility,best-practices,seo
```
Mål: Performance ≥ 90, Accessibility = 100, Best Practices ≥ 95, SEO ≥ 90.

## Etter HTML-endringer — WCAG AA-sjekk
Verifiser følgende før publisering:
- **Kontrast:** all brødtekst ≥ 4.5:1, stor tekst (18pt / 14pt bold) ≥ 3:1 — sjekk både lys og mørk modus
- **Nye interaktive elementer:** knapper og lenker må ha synlig tekst eller `aria-label`; skjemafelt må ha tilknyttet `<label>` eller `aria-label`
- **Tabellhoder:** nye `<th>`-elementer må ha `scope="col"` eller `scope="row"`
- **Dekorative ikoner:** unicode-tegn og SVG-ikoner som ikke er meningsbærende skal ha `aria-hidden="true"`
- **Tilstandsknapper (toggle/filter):** bruk `aria-pressed` for av/på-knapper, `aria-sort` for sorterbare kolonner
- **Fokus:** alle interaktive elementer skal ha synlig `:focus-visible`-stil
- **Farge som eneste signal:** ny informasjon som bare formidles via farge er ikke tillatt — legg til tekst, ikon eller mønster
- **Live-regioner:** dynamisk innhold (f.eks. radteller, statusmeldinger) skal ha `aria-live="polite"`

## WCAG AA — kjente anbefalte forbedringer (ikke kritiske)

| Element | Forbedring |
|---|---|
| `<caption>` i tabell | Bør stå rett etter `<table>` — nå plassert etter `<thead>` |
