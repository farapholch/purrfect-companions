# Ej publicerat på CurseForge ännu

(tomt — 3.41.0–3.45.0 flyttades in i publish/changelog.md vid släppet 2026-09-03.
Nya opublicerade poster skrivs HÄR, inte i publish/, eftersom publish_site.sh
lägger ut publish/*.md på purrfect.pelleops.se och en changelog på sajten som
CurseForge inte har blir en mismatch.)

---
---

<!-- ALLT NEDANFÖR ÄR PROJEKTETS EGEN LOGG och ska INTE med till butiken. -->

## Plaggen (projektlogg, 3.42.0)

Plaggen bor i ETT delat ark `textures/entity/plagg.png` (1024x1024, plagg-
geometrierna deklarerar 256x256 → fyra texlar per enhet). Materialen bor i
`tools/plaggmaterial.py`: en funktion per plagg, uppslagen på namnet i
MATERIAL; nytt plagg utan rad får tyg. Kuber som delar uv-ruta målas en gång.
Klientdefinitionernas `textures.default` pekar på plagg.png för alla katter;
de tio per-katt-atlasen är borttagna (git rm). Renderarna slår upp texturerna
i klientdefinitionen när en sådan finns, annars `<namn>.png` (dräkten,
hunden). Kronans tinnar är HÅL i texturen (alpha 0, entity_alphatest).

## Dräkten (projektlogg, 3.41.0)

`tools/make_player_gear.py` målar dräkten i SKALA=4 på ett 256x256-ark
(geometrin deklarerar fortfarande 64x64); hjälparna importeras från
make_cat_pals (Duk, korn, blanda …). Renderaren fick `enheter=` för att kunna
sampla ett ark i annan skala än geometrin — dräkt- och hundrenderingar skickar
tretupler och fick förut alltid en texel per enhet. purrfect-test tillåter
heltalsmultipel för attachables. OBS: förhandsbildens lager läggs luva → väst →
byxor → tassar och byxornas bålkub täcker västens ljusa bringa i BILDEN; i
spelet ligger bringan 0,05 framför (inflate) och syns, verifierat på Xbox
tidigare. Renderaren slänger inflate.

## Pälsarket (projektlogg, 3.40.0)

Hela texturkedjan — make_cat_markings, make_cat_textures (pälsdelen),
make_cat_shading, make_cat_faces, make_midnight_texture, make_spokkatt_texture
och art/kattpalsar — ersatt av EN generator, `tools/make_cat_pals.py`, som
målar `<katt>_pals.png` (512x128) från en tabell per katt. Geometrin
deklarerar 128x32 uv-enheter (PALS i build_accessories) och Bedrock läser
arket fyra gånger tätare. Plaggen ligger kvar i 256-atlaset; katten ritas ur
`Texture.pals`, plaggen ur `Texture.default`. Atlasets kattrader (v < 26) töms
vid bygget så ingen luras av den gamla 1x-katten.

Renderarna (render_regression, render_preview) samplar per kub ur rätt textur
med rätt skala. make_variant döper om `_pals`-arket också (samma \b-fälla som
pc_-ikonerna). Spärrarna i purrfect-test läser arket i uv-enheter gånger skala.

Två fällor på vägen: ränder som vaggade 1,2 texlar var elfte rad blev
S-formade sömmar (nu 0,7 och långsammare), och en mun som går nedåt i
vinklarna — som på en riktig katt — läser som bister på en kub; den går uppåt
nu, ett ω. Testets rosa-test tog först Mochas bruna öra för inneröra: rosa
har blått i sig, brunt har det inte.

## Kattteckningarna (projektlogg, 3.36.0 — kedjan är ersatt, se ovan)

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
