# Ej publicerat på CurseForge ännu

**VID SLÄPP AV 3.33.0, LÄGG TILLBAKA RADEN OM KATTBOKEN i publish/index.html.**
Den togs bort 2026-08-27 därför att sajten listade boken som funktion medan
CurseForge stod på 3.32.0 utan den — sidan lovade något man inte kunde hämta.
Raden lyder:

    <li><b>The Cat Care Book</b> — a book and a Cat Treat, and it explains
    everything above: every outfit, every suit tier, and how many achievements
    you have left</li>

(publish/description.md behöll sin rad: den texten når CurseForge först när den
klistras in vid släppet, alltså samtidigt som versionen finns.)

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

## Uthållighetsprovet (projektlogg, inte butikstext)

`tools/purrfect-uthallighet` — tre faser, världen rivs INTE emellan:

1. sätter tillstånd på en katt (fyra egenskaper, tämjning, tre diamanter i
   ryggsäcken), sparar och stänger av
2. startar om SAMMA värld och läser tillbaka allt
3. trettio tämjda katter i en minut och mäter vad de tolv looparna kostar

Alla tolv loopar är lindade i `matt()`, som bokför tid per varv. Festkanonen
lindas medvetet inte — den sparar sitt handtag för att kunna stoppa sig själv.

**Första mätningen betalade för provet direkt.** Kolonislingan stod för 3,10 ms
av paketets 4,30 ms, alltså 72 % av all skriptkostnad, för en loop som mest
jämför tal. Orsaken: `entity.location` är en INBYGGD getter som bygger ett nytt
objekt vid varje anrop, och avståndshjälparen läste den sex gånger per par —
1 656 inbyggda anrop i sekunden med 24 katter. Platserna läses nu en gång per
katt och varv: kolonin 3,10 → ~1,0 ms, totalen 4,30 → under 2 ms.

Provet ställer tillbaka `level-name` när det är klart. Utan det klagade
purrfect-test vid nästa körning, och ett prov som stökar för ett annat prov blir
brus man slutar läsa.

