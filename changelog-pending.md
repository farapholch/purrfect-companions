# Ej publicerat på CurseForge ännu

(tomt — 3.32.0 flyttades in i publish/changelog.md vid släppet 2026-08-23.
Nya opublicerade poster skrivs HÄR, inte i publish/, eftersom publish_site.sh
lägger ut publish/*.md på purrfect.pelleops.se och en changelog på sajten som
CurseForge inte har blir en mismatch.)

---

## 3.33.0 — A book that explains the whole thing

The pack has grown for fifteen releases: ninety-seven items, a dozen mechanics,
two worlds. None of it is discoverable in the game. A player who installs it
cold has no way of knowing that a saddled cat fishes for you, that a backpack
cat digs up diamonds, or that the weakest piece of your suit decides the whole
bonus. Achievements tell you *after* you have found something.

**The Cat Care Book.** Craft it from a book and a Cat Treat and it opens a menu:
the cats and where they live, everything a cat can do, every outfit and what it
grants her, the four tiers of your own suit and the rule that the weakest piece
decides, the furniture, and how many achievements you have left to find. It does
not name the ones you have not earned. Some of them are not going to be named at
all.

The contents are generated from the same tables the outfits are built from, so
the book cannot drift away from the pack it describes.

---

<!-- ALLT NEDANFÖR ÄR PROJEKTETS EGEN LOGG och ska INTE med till butiken. -->

## Kattboken — tre fällor testet hittade

- **Bedrocks .lang stödjer inga radbrytningar.** Vaniljas egen fil innehåller
  noll `\n`-escapes. Flerradig text lagd som ett värde sprängde filformatet: 18
  rader utan `=`, som spelet tyst hoppar över. Nu en nyckel per stycke, fogade
  med rawtext i skriptet — och en grind som fäller varje `.lang`-rad utan `=`.
- **Effektnamnens nycklar heter `potion.`, inte `effect.`** — och hoppkraften
  heter `potion.jump`, inte `potion.jumpBoost`. Verifierat mot motorns egen
  en_US.lang. Med vaniljas nycklar står effektnamnen översatta på varje språk
  spelet stödjer utan att paketet översätter en rad.
- **Röktestet kördes från en annan fil än den i repot.**
  `tools/testbot/smoke-test.js` låg i versionshantering men var död kod; testet
  startade `/opt/purrfect-testbot/smoke-test.js` från 8 augusti. En ändring i
  repot ändrade ingenting. Repots kopia är källan nu och kopieras in före varje
  körning.

