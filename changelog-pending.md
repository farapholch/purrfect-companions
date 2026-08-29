# Ej publicerat på CurseForge ännu

(tomt — 3.33.0 flyttades in i publish/changelog.md vid släppet 2026-08-27.
Nya opublicerade poster skrivs HÄR, inte i publish/, eftersom publish_site.sh
lägger ut publish/*.md på purrfect.pelleops.se och en changelog på sajten som
CurseForge inte har blir en mismatch.)

---

## 3.34.0 — Big cats are big, and hungry cats say so

**Feeding your cats matters now.** The pack has always tracked whether a cat is
hungry — that is what the tail has been telling you — but nothing came of it. A
cat that had not eaten in a quarter of an hour behaved exactly like a fed one.

A hungry cat stops bringing you morning gifts and stops digging up treasure
until you feed her. Nothing you depend on ever breaks: she still follows, still
carries, still lets you ride her, still warns you. Cod, salmon or a Cat Treat and
she is back at it. The Cat Care Book tells you how many are waiting.

Cats also get hungry far more slowly than the tail used to suggest — it was six
to twelve minutes from a full bowl, which would have made this a chore instead of
a habit. It is twenty to forty now.

### 3.34.0 — Big cats are big

Snow the Ragdoll now has more health than Mocha the Birman, and takes up more
room. Until now every cat had the same twenty health and the same hitbox no
matter its size — speed was the only thing that told them apart. Both follow the
cat's own size now, and armour adds to it instead of flattening it, so a big cat
in netherite is still the bigger cat.

---

<!-- ALLT NEDANFÖR ÄR PROJEKTETS EGEN LOGG och ska INTE med till butiken. -->

## Storleken märks (projektlogg)

`minecraft:scale` skalar MODELLEN, inte kollisionslådan — en birma på 0,85 var
lika bred att gå in i som en ragdoll på 1,15. Samma fel fanns i hundpaketet och
rättades där i 1.4.0.

Grundliv och träffyta HÄRLEDS nu ur skalan som redan står i `mjau:adult`, så det
inte blir en tabell till att hålla i synk. Livet avrundas till jämna tal, för
spelet ritar hjärtan i par.

Rustningen satte tidigare ett FAST värde (40/44/50/60), vilket hade raderat hela
skillnaden i samma sekund man satte pansar på katten. Den adderar nu.

Grinden räknar om båda värdena ur skalan och fäller på ett handredigerat värde —
provad mot en katt med träffytan tillbakaställd till 0,7.
