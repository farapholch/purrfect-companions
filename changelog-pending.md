# Ej publicerat på CurseForge ännu

(tomt — 3.34.0 flyttades in i publish/changelog.md vid släppet 2026-08-29.
Nya opublicerade poster skrivs HÄR, inte i publish/, eftersom publish_site.sh
lägger ut publish/*.md på purrfect.pelleops.se och en changelog på sajten som
CurseForge inte har blir en mismatch.)

---

## 3.35.0 — The cat tower looks like a cat tower

It was a thin post between two wide plates, and it read as an I-beam. Worse,
every part of it sampled the same corner of a single 16×16 texture, so the sisal
post and the carpet platform looked identical — a rope could not look like rope.

It has a thicker sisal post with visible wraps, a plank base, carpeted
platforms, a rim all the way round the top instead of on two sides only, a
mid-level shelf that makes it a tower rather than a stool, and a ball on a
string hanging under the shelf.

---

<!-- ALLT NEDANFÖR ÄR PROJEKTETS EGEN LOGG och ska INTE med till butiken. -->

## Klösträdet och tre generatorfel (projektlogg)

Blockbyggaren la `"uv": [0,0]` på VARJE kub och gjorde texturen 16x16, så alla
ytor på ett block samplade samma pixlar. Kuber kan nu ange ett MATERIAL som
tredje fält; gör de det packas UV:n ut på en 128x64-duk och varje material målas
för sig. Kuber utan tredje fält beter sig precis som förut, så de sju andra
möblerna är byte-identiska.

**Tre fel i `build_blocks.py` som hittades på vägen, alla äldre än i dag:**

- **Skriptet kraschade på slutet.** Loopen tog alla entitetsfiler och antog
  `component_groups`; skeppet har inga. Kraschen kom EFTER att blocken skrivits,
  så bygget såg ut att lyckas ända tills man läste sista raden. Samma klass av
  fel som build_accessories fick fixad 2026-08-13.
- **Den skrev sönder kolonins nattgrupp.** Omnumreringen satte move_to_block
  till 12 och random_sitting till 15 i ALLA grupper, inklusive `mjau:sovdags`
  som fått 19 och 20 just för att inte krocka med `mjau:fri`. Kördes
  build_blocks efter build_accessories var sovhögen tyst trasig. Grupper med
  medvetet valda prioriteter står nu i en skyddslista, och byggordningen spelar
  inte längre roll — provat med fyra körningar i blandad ordning.
- **Kattluckan fick en kollisionslåda.** Den ska gå att gå igenom och stod
  handrättad till `false` i den genererade filen; nästa körning hade skrivit
  över den. Blocket säger det själv nu.
