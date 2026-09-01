# Ej publicerat på CurseForge ännu

(tomt — 3.35.0 flyttades in i publish/changelog.md vid släppet 2026-09-01.
Nya opublicerade poster skrivs HÄR, inte i publish/, eftersom publish_site.sh
lägger ut publish/*.md på purrfect.pelleops.se och en changelog på sajten som
CurseForge inte har blir en mismatch.)

---

## 3.36.0 — The cats have markings now

A player wrote in and asked, very politely, whether the textures could be
improved. They were right. The faces have always had detail, but the bodies were
flat slabs of a single colour — no fur, no shading, no markings at all. The pack
even called Misty a grey tabby and Ginger a warm ginger tabby without a single
stripe on either of them.

They are tabbies now: stripes down the sides and across the back, a lighter
belly, rings on the legs and tail. Hazel keeps her white bib and paws, and Snow
and Mocha are deliberately left unstriped — a Ragdoll and a Birman are not tabby
cats, and striping them would not have been a better texture, just the wrong
cat.

---

<!-- ALLT NEDANFÖR ÄR PROJEKTETS EGEN LOGG och ska INTE med till butiken. -->

## Kattteckningarna (projektlogg)

Hund- och grispaketen har haft mönstermaskineri hela tiden (fläckar, sadel,
bringa, strumpor, ullkrus). Katterna är det ÄLDSTA paketet och byggdes innan
den tekniken fanns. `tools/make_cat_markings.py` är den, portad hit.

**UV-ytorna läses ur geometrin**, inte ur en tabell i skriptet — ändras modellen
följer teckningen med. Kroppens sidor är bara 10x5 pixlar, vilket är varför det
måste vara varannan-tredje kolumn och inte mer.

**KÄLLAN ÄR art/kattpalsar/, inte paketet.** Målas det i paketet blir en andra
körning en dubbelmålning och ränderna mörknar för varje gång någon råkar köra
skriptet. Originalen ligger utanför resurspaketet så de inte skeppas.

**Körordningen är viktig:** teckningar → make_cat_textures (Ginger och Domino
härleds ur de MÅLADE) → build_accessories (plaggens UV-ytor målas in igen).

Vita bringor och tassar skyddas av ett FÄRGTEST, inte av en lista: bara pixlar
nära pälsens grundfärg rörs. Huvudet undantas helt — samma försiktighet som
make_cat_textures tar, och av samma skäl.

Bildregressionen föll med flit på alla 27 vyer och facit skrevs om efter att
Pelle sett före/efter-bilden.
