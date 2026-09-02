# Ej publicerat på CurseForge ännu

(tomt — 3.36.0–3.40.0 flyttades in i publish/changelog.md vid släppet 2026-09-02.
Nya opublicerade poster skrivs HÄR, inte i publish/, eftersom publish_site.sh
lägger ut publish/*.md på purrfect.pelleops.se och en changelog på sajten som
CurseForge inte har blir en mismatch.)

---

## 3.42.0 — The outfits get their materials

The outfits were the last flat colour left. A saddle was a brown box, a cart a
tan one, and a crown a yellow slab with the same three shades as the cap.

Every outfit now draws from one shared sheet at four texels per unit, and each
one is painted as what it is made of. Leather has stitching along the edges.
Wool is knitted, with ribs, and the scarf has a fringe. Metal has bevelled
edges, a highlight and rivets — the armour has a ridge down the back. The cart
is planks with nails, and its wheels have a rim, a hub and spokes. The glasses
have real lenses with a highlight. The wings have rows of feathers, the bat
wings have finger bones and a ragged trailing edge. The crown has three jewels
and points along the top. The cape has folds and a gold border. The witch hat
has a band and a buckle, the santa hat a white fluffy brim and pompom, and the
collar a real gold bell. The energy blade glows from a white core, and the Void
cloak has stars and a nebula in it.

This also fixes something nobody had reported: the secret cats' outfits were
tinted by their own coat, so a saddle on Midnight was black. One sheet for
everyone means one saddle.

## 3.41.0 — The cat suit gets the same fur

The player's cat suit was the last thing still drawn at one texel per unit,
and next to the new cats it looked like cardboard: the trousers were three
colours in total. It is on its own 256x256 sheet now, four texels per unit,
like the cats.

The **leather suit is a tabby**: rings round the body, arms and legs, an M on
the forehead, and a face with the same almond eyes, vertical pupil, pink nose
and small smile as the cats. Paws are light with pads and toe splits.

The **metal tiers** used to be the same suit in another colour. They keep the
fur, in iron, diamond or netherite tint, and wear plates on top of it: a brow
band on the hood, a chest plate with rivets, shoulder caps, a belt, knee
guards and toe caps. You can tell the tier at a distance now.

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
