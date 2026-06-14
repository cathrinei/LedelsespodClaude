# Privat tilgang til Ledelsepod.html (uten localhost)

Alternativer for å gjøre siden tilgjengelig kun for deg selv, fra hvilken som helst enhet.

## Alternativ 1: Cloudflare Pages + Cloudflare Access (anbefalt)

**Sikkerhet:** identitetsbasert (engangskode på e-post)
**Kostnad:** gratis (opptil 50 brukere)

1. Opprett konto på [cloudflare.com](https://cloudflare.com)
2. Gå til **Pages** → koble til GitHub-repoet `cathrinei/LedelsespodClaude`
3. Sett build-output til rotkatalogen (ingen build-kommando nødvendig)
4. Aktiver **Cloudflare Access** på det genererte domenet (`*.pages.dev`)
5. Opprett en Access Policy: tillat kun e-postadressen `cat@indroy.no`
6. Ved besøk får du en engangskode på e-post — ingen andre kan komme inn

**Merk:** GitHub Actions pusher til master → Cloudflare Pages deployer automatisk ved hvert push.

---

## Alternativ 2: Vercel med deployment protection

**Sikkerhet:** passordbasert
**Kostnad:** gratis (Hobby-plan)

1. Opprett konto på [vercel.com](https://vercel.com)
2. Importer GitHub-repoet `cathrinei/LedelsespodClaude`
3. Ingen build-kommando — sett output directory til `.` (rot)
4. Gå til **Settings → Deployment Protection** og aktiver passord
5. Besøk siden og skriv inn passordet

**Merk:** Passordet lagres i browseren — du trenger bare taste det inn én gang per enhet.

---

## Alternativ 3: GitHub Pages + privat repo

**Sikkerhet:** repoet er skjult, ingen innlogging på selve siden
**Kostnad:** ~4 USD/mnd (GitHub Pro)

- Gjør repoet privat under **Settings → Change repository visibility**
- GitHub Pro er nødvendig for å bruke Pages på private repos
- Siden har ingen innlogging — kun repoet er skjult

**Anbefales ikke** hvis du vil ha reell tilgangskontroll på selve siden.
