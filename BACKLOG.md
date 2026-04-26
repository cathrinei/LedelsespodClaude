# Backlog — foreslåtte forbedringer

## Tilgjengelighet (WCAG AA)

| Element | Forbedring |
|---|---|
| `.stat-btn` | ✅ Eksplisitt `:focus-visible`-stil finnes |
| `#rowCount` | ✅ `role="status"` lagt til |
| Stjerne-ikon `★` i kolonneheader | ✅ Stjerne fjernet fra kolonneheader; `aria-hidden` lagt til i favToggle-knapp |
| `.ep-card` (mobilkort) | ✅ `role="article"` lagt til |
| `header .subtitle` | ✅ Kontrast økt til `rgba(255,255,255,0.8)` |

## UX / mobil

- ✅ **Sveip-hint**: skjules permanent etter første sveip via `localStorage` (`ledelsepod_swipe_used`)
- **PWA**: legg til `manifest.json` + `<meta>`-tagger for installerbar app på hjemskjermen (~1 time)

## Kode

- ✅ Inline `style`-attributt på `.fav-btn` flyttet til CSS
- ✅ `embed_csv.py`: feilhåndtering for manglende fil, tom CSV og ugyldig header lagt til
- ✅ Workflow: valideringssteg som sjekker at `data`-arrayen i HTML er gyldig JSON etter `embed_csv.py`

## Data

- ✅ **Auto-reject etter 3 mislykkede forsøk**: `failed_attempts.csv` teller API-feil per episode; etter `MAX_ATTEMPTS=3` sendes episoden til `rejected_episodes.csv` automatisk
- Vurdere å legge til flere podcast-kilder i `FEEDS`-dicten i `update_podcasts.py`
