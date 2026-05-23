# Ledelsepod.html – tekniske noter

## Data array
The `data` array in the HTML is populated from the CSV via `embed_csv.py`. Unrated episodes (Rating=0) display as **N/A** and always pass through the rating filter.

## Stats
`updateStats()` computes all stats from the `data` array:
- Total episodes, shows, teamledelse-tagged count, personalledelse-tagged count, top-rated (6/6), unrated (N/A)
- Three stat cards are clickable filter shortcuts (`.stat-btn`): **Episoder** (reset all), **Teamledelse** (tag filter), **Personalledelse** (tag filter), **Toppkarakter 6/6** (rating=6)
- Active stat card gets green background; clicking again toggles the filter off
- `updateStatBtns()` syncs active state of stat cards with current filter state; called after every filter action and from `resetFilters()`
- `updateResetBtn()` toggles `.filters-active` class on Nullstill-knappen når søk, rating, podkast, tag eller favoritter er aktivt — grønn kant og tekst som visuelt signal; called from `refresh()`
- Tom tilstand: når `renderTable()` får `rows.length === 0` vises en rad med melding og snarvei til `resetFilters()`
- **URL-tilstand**: `filtersToUrl()` oppdaterer URL-parametere (`search`, `rating`, `podcast`, `tag`, `favs`) ved hver filterendring via `history.replaceState` — filtrert visning kan deles som URL; `applyUrlFilters()` leser og gjenoppretter tilstand ved sideinnlasting
- **Favoritter**: `favorites` er et `Set` lagret i `localStorage` (`ledelsepod_favorites`); stjerne-knapp (`.fav-btn`) per rad i EPISODE-cellen (foran tittelen); `favId(row)` bruker `podcast::title` som nøkkel; Favoritter-knapp i kontrollbar toggler `showFavsOnly`-filter; gul stjerne (`#f59e0b`) når aktiv
- **Mobil sveip-til-favoritt**: sveip høyre (>60px, horisontal dominans) på et episodekort toggler favoritt — event delegation via `touchstart`/`touchmove`/`touchend`/`touchcancel` på `#tableBody` (passive listeners); Y-koordinat spores for å avvise scroll-gester på iOS Safari; `tr.dataset.fav` settes i `renderTable()` for identifikasjon; `.fav-flashed`-klasse trigger gul glimt-animasjon (`@keyframes fav-flash`) som visuell bekreftelse
- Under sveip: kort forskyves med `translateX`, gul venstrekant vokser via `--swipe-p` CSS-variabel på `::before`; ved avbrytelse snapper kortet tilbake med `.ep-card--snapping` (0.18s ease); `lastX` trackes i `touchmove` og brukes i `touchend` (mer pålitelig enn `changedTouches` på iOS); diagonal-toleranse 0.75 (ikke 0.5) siden iOS alltid legger litt vertikal bevegelse inn
- Hint "sveip → for favoritt" vises på første kort via `ep-card--hint::after`, `@media (hover: none) and (pointer: coarse)` — skjules permanent etter første vellykkede sveip (`localStorage` nøkkel `ledelsepod_swipe_used`)
- Favoritt-stjerne (`.fav-btn`) vises i mobilkortets header via `.ep-card__header-right` ved siden av Lytt-lenke og 🔗-knapp

## "↑ Last inn CSV"-knappen
- Knappen er skjult (`display:none`) — data oppdateres automatisk via GitHub Actions
- Funksjonaliteten er beholdt i koden (kan vises igjen ved å fjerne `style="display:none"`)
- Logikk: åpner fil-picker, leser med `FileReader` (UTF-8, maks 5 MB), `parseCSV()` → `data`-array → `updateStats()` + `refresh()`

## Dark mode
- Toggle button (☾ Mørk / ☀ Lys) in top-right of header
- Preference persisted in `localStorage` (`darkMode` key)
- Deep forest green gradient header (`#0b1f10 → #1e4a30`) — distinguishes from the AI project's blue theme
- Dark mode uses deep black-green background (`#080d08`) with bright green accent (`#4ade80`)

## Tag filter
- Rendered as clickable **pill buttons** (not a `<select>`) — IDs: `.tag-pill` with `data-tag` attribute
- Active tag stored in JS module-level variable `let activeTag = ''` — pills set it directly, `getFiltered()` reads it
- `resetFilters()` sets `activeTag = ''` and resets active pill state
- Tags in the table rows are also clickable (`<button class="tag">`) — clicking filters the table and syncs the tag pills in the controls bar; clicking the same tag again clears the filter
- `renderTags()` wraps tags i `<span class="tag-group">` (`.tag-group { display: inline-flex; gap: 0.35rem }`) for konsistent avstand mellom tags i både tabell og mobilkort
- Event delegation on `#tableBody` handles tag clicks — avoids re-binding on every `renderTable()` call
- Active row tag gets `filter: brightness(0.82); font-weight: 700` to signal selected state (no outline)

## Podcast filter
- `<select id="podcastFilter">` — placed to the right of the rating filter in the controls bar
- Options populated dynamically from the `data` array (unique podcast names, alphabetically sorted) on page load
- Filters table to a single show; `resetFilters()` resets it to `""` (Alle podkaster)
- Podcast names in table rows are rendered as `<button class="cell-podcast" data-podcast="...">` — clicking filters the table and syncs the dropdown; clicking same name again clears the filter
- Event delegation on `#tableBody` handles podcast clicks — same pattern as tag clicks; `aria-pressed` reflects active state; aktiv tilstand vises med `text-decoration: underline` (ikke outline)

## Øvrige tekniske noter
- Language column (index 2) is kept in CSV/data array but **not displayed** in the table — all episodes are Norwegian
- Sort: `sort` object (`col`, `asc`); `RATING_COL = 7`, `DATE_COL = 3` — default sort is date descending (newest first)
- `data-col` in table headers refers to **data array indices** (col 2 is skipped in table display — so `data-col="3"` = date, `data-col="4"` = hosts, etc.)
- Tags whitelisted via `tagMeta` — 9 tags: `teamledelse`, `personalledelse`, `produktledelse`, `feedback`, `kultur`, `rekruttering`, `motivasjon`, `coaching`, `endringsledelse` (merk: `produktledelse`-taggen finnes fortsatt i `tagMeta` for episodevisning, men kortet og tag-pill-filteret er fjernet)
- Tags can be combined (comma-separated); `tagsOf(row)` helper used for all tag checks
- Episode titles are rendered as `<a class="cell-title">` links — clicking opens the episode URL in a new tab; styled to look like plain text (no underline until hover)
- `safeUrl()` blocks non-HTTP(S) URLs to prevent `javascript:` injection
- CSP: `default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'`
- Default filter on load: rating 4+; N/A episodes always shown regardless of filter
- CSV upload capped at 5 MB
- `.sticky-outer` wrapper er **sticky** (`position: sticky; top: 0; z-index: 10`) på desktop — inneholder `<header>` (tittel + mørk-modus-knapp) og `.sticky-ui` (`.stats-bar` + `.controls`), hele toppområdet følger med ved scrolling; på mobil (`≤720px`) er wrapperen `static`
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

## Mobilvisning (≤600px)
- Breakpoint `@media (max-width: 600px)` bytter fra tabell til kortlayout
- `renderTable()` injiserer en `<td class="card-cell" colspan="10">` per rad via `insertAdjacentHTML` — skjult på desktop, synlig på mobil
- Kortstruktur: **header-left** (liten rating-badge 24px + dato) · **header-right** (► Lytt + 🔗 + ★) · tittel · meta (podkastnavn + vert) · tags. Gjester, emner og begrunnelse utelates
- 🔗-knappen (copy-btn) er grensefri ikon på desktop (episodekolonnen); på mobil er den del av kortets header-right uten border
- Desktop EPISODE-kolonne: `★ 🔗 [tittel]` — favoritt og kopieringsikon gruppert til venstre før tittelen
- Desktop LYTT-kolonne: kun `► Lytt`-lenke
- Tabell og `<thead>` skjules med `display:none` på mobil; `tbody tr` blir `display:block` med kortutseende
- Rating-fargekant (`border-left`) bevares på `<tr>` også i kortvisning
- Header stables vertikalt, stats vises i 2-kolonners grid, kontroller full bredde på mobil
- Dark mode fungerer automatisk via CSS-variabler
