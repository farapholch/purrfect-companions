# Inskickning — Cat Haven (Worlds-projekt på CurseForge)

Cat Haven är en EGEN produkt på CurseForge: kategorin **Worlds**, inte Add-ons.
Skapa projektet manuellt (API:t kan bara ladda upp filer till befintliga
projekt). Gå till curseforge.com → *Start a Project* → **Minecraft Bedrock** →
**Worlds**. När projektet finns: lägg projekt-id:t i `.curseforge-cathaven-id`
så kan uppladdningen skriptas precis som för add-onet.

## Project name
`Cat Haven`

## Summary (en mening)
`Move into a ready-made cat shelter: find the four cats, let one fish for you, and ride to the lighthouse - Purrfect Companions included, one tap to install.`

## Description
Use the top of `publish/changelog.md` ("Cat Haven — a world to move into") plus:

- Ready-made starter world for the **Purrfect Companions** add-on (bundled inside — nothing to enable by hand)
- You are the shelter's new caretaker; the handbook in the starter chest gives three tasks
- Find Misty, Hazel, Mocha and Snow hiding around the valley
- Saddle a cat and let it catch cod in the fish pond
- Ride the terraced hill to the lighthouse; a reward chest waits at the top
- Survival, easy difficulty, keep-inventory on - made for kids and families
- Link to the add-on project: https://www.curseforge.com/minecraft-bedrock/addons/purrfect-companions

## Logo
Återanvänd `logo.png` (512×512) tills en egen Cat Haven-hjältebild är renderad.

## Fil
`purrfect-cat-haven-v<VER>.mcworld` — byggs med `python3 build_world.py public /tmp`
(testas med `cathaven-test`). Versionen följer alltid add-onets version;
loggboken `.shipped.tsv` använder varianterna `world-public`/`world-private`.
