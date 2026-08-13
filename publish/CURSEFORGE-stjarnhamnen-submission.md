# Inskickning — Star Harbour (Worlds-projekt på CurseForge)

Star Harbour är en EGEN produkt på CurseForge, precis som Cat Haven: kategorin
**Worlds**, inte Add-ons. Projektet måste skapas manuellt — API:t kan bara ladda
upp filer till projekt som redan finns.

**Så här:** curseforge.com → *Start a Project* → **Minecraft Bedrock** →
**Worlds**. När projektet är godkänt: lägg projekt-id:t i
`.curseforge-starharbour-id`, så kan uppladdningen skriptas som för de andra.
(Cat Havens id är 1647453 — Star Harbour ska INTE dit, det är ett annat projekt.)

## Project name
`Star Harbour`

## Summary (en mening, max 255 tecken)
`A dark cat station adrift among the stars: wake its four cats, find four energy blades, and climb to the observation deck - Purrfect Companions included, one tap to install.`

## Description

En rymdstation som legat mörk länge. Du är dess nya hamnmästare.

- Färdig äventyrsvärld för **Purrfect Companions** — add-onet ligger inbakat,
  ingenting behöver aktiveras för hand
- **Fyra katter sover ombord** — en i kupolen, en i korridoren, en i hangaren,
  en på utkiken. Väck dem med torsken ur startkistan
- **Fyra energisvärd** — ett i varje färg, inlåsta i olika fack runt stationen.
  De hugger, och de lyser upp vägen
- **Hangaren** med skytteln som aldrig flög mer, och de två spjutjaktarna
  bredvid som är ännu äldre. Något värt att behålla sitter fastspänt i lastrummet
- **Utkiken** högst upp i stationen, dit man klättrar via servicestegen. Stjärnorna
  är närmast där
- Loggboken i startkistan ger uppdragen i ordning
- Survival, lätt svårighetsgrad, behåll-inventarie — gjord för barn och familjer
- Länk till add-onet:
  https://www.curseforge.com/minecraft-bedrock/addons/purrfect-companions

**Skriv INTE ut i beskrivningen:** hur man får fram den femte katten. Loggbokens
sista sida antyder henne ("fur like the space between stars ... she answers only
to someone who carries all four colours at once") och det ska räcka — samma
linje som med Midnight i Cat Haven. Att avslöja ritualen tar bort hela poängen.

## Logo & galleri
- Logo: `starharbour-logo.png` (512×512)
- Galleri/hjältebild: `starharbour-hero.png` (1280×720)
- Båda genereras med `python3 tools/promo/make_harbour_art.py --promo` och ligger
  i `publish/` — de laddas upp till purrfect.pelleops.se och går att spara ner
  därifrån i webbläsaren
- **Riktiga in-game-screenshots saknas** — de måste tas på Xbox eller i klienten
  (byggservern är headless). Ta 2–3: kupolen inifrån, hangaren med jaktplanen,
  och utsikten från däcket. CurseForge-granskningen gillar riktiga skärmdumpar,
  och Cat Haven-inskickningen hade samma lucka
- Världslistans ikon (`world_icon.jpeg`, 800×450) bäddas in automatiskt av
  `build_spaceworld.py` — den är EGEN, inte Cat Havens

## Fil
`star-harbour-v<VER>.mcworld` — byggs med
`python3 build_spaceworld.py public /tmp/starharbour-release`
(hela kedjan: `tools/hamn-test`). Det byggs även en `.mctemplate` med samma
namn; den formen är ännu inte provkörd i Mod Mate, så ladda upp `.mcworld`
först och lägg till mallen när den är testad.

Versionen följer alltid add-onets version.

## Changelog för första uppladdningen
Se `publish/starharbour-changelog.md`.

## Att tänka på
- **Sökvägslängden.** Filnamnet blir mappnamn på Xbox, och 256 tecken var nog
  för att Mod Mate tyst skulle tappa en fil. Döp inte om filen till något längre
  — `tools/hamn-test` mäter och failar över 250 tecken.
- **Aldrig familjeversionen.** `stjarnhamnen-*-familj.mcworld` innehåller
  privata kattnamn och ska aldrig laddas upp någonstans publikt.
