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

- **Sveip-hint**: vises alltid på første kort — bør skjules permanent etter at brukeren har sveipet én gang (lagre i `localStorage`)
- **PWA**: legg til `manifest.json` + `<meta>`-tagger for installerbar app på hjemskjermen (~1 time)

## Kode

- Inline `style`-attributt på `.fav-btn` i `renderTable()` bør flyttes til CSS
- `embed_csv.py` mangler feilhåndtering ved ugyldig CSV-input
- Workflow-validering: sjekk at `data`-arrayen i HTML er gyldig JSON etter at `embed_csv.py` har kjørt

## Data

- Vurdere å legge til flere podcast-kilder i `FEEDS`-dicten i `update_podcasts.py`
