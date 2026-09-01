# Ej publicerat på CurseForge ännu

(tomt — 3.35.0 flyttades in i publish/changelog.md vid släppet 2026-09-01.
Nya opublicerade poster skrivs HÄR, inte i publish/, eftersom publish_site.sh
lägger ut publish/*.md på purrfect.pelleops.se och en changelog på sajten som
CurseForge inte har blir en mismatch.)

---

**The head is not a box any more.** It was a 6x5x4 cube, and it read as exactly
that. Cats are widest at the cheeks and narrow toward the muzzle, so there are
cheek tufts now that flare out at the jaw — the outline changes width three times
on the way up instead of going straight. Together with the muzzle it is the same
head, but it stops reading as a brick.

(The ears were rebuilt three times on the way to that — tapered, smaller, wider
and lower — and every version was worse than the ones that were already there.
The ears were never the problem. They are untouched.)

## 3.38.0 — The bodies stop being flat colour

Same player, a follow-up: they are an artist, and said as kindly as they could
that the kittens are hard for them to look at. Measured per body part they were
right, and it could be put in numbers. The head has twelve tones. Snow's **tail
was one single tone across 100% of it**, her legs 95%, her body 79% — and
Aurora, Nova, Midnight and the ghost had no variation at all outside the head.
Minecraft shades whole *faces* by direction but never inside a face, so a flat
colour field stays a flat colour field however well the engine lights it.

Two of those were not "flat" so much as **the wrong breed**:

* **Snow is a Ragdoll.** Her *ears* were already grey against a white body — the
  points were in the art — but her tail and legs were pure white. Points belong
  on ears, face, tail and legs; she had them in one place out of four. She has
  them everywhere now, with white feet.
* **Mocha is a Birman** and had her points everywhere, but a Birman's signature
  is white *gloves*. Her legs ran brown all the way down. They don't now.

The rest is breed-neutral and applies to every cat: light from above on the
body, and a contact shadow where the legs and the tail meet it. No body part is
a single tone any more.

Which cat is pointed is derived, not listed: if the ear colour differs clearly
from the body, the cat is pointed and the ear colour *is* the point colour. That
catches Snow and Mocha and nobody else, without a list to keep in sync.

## 3.37.0 — Softer faces, a nose, and a cat door that stops shedding dirt

**Every cat has a proper inner ear.** Measured across all ten, this was a
patchwork: Aurora, Midnight, Nova and the ghost had no inner ear at all, Domino
and Ginger had one twenty steps from their fur — invisible — and the rest were
split between pink and white. On every one of them it also sat half a texel off
centre and bled onto the *side* of the ear, because the ear's front face starts
at x 33.30 and that first texel is a third of the way onto the side. The
generator owns it now: one texel, dead centre, in a pink mixed far enough toward
the fur that it stays visible on a black cat and a white one alike.

**The cats have a nose now.** The head was a single cube, so the entire face lay
in one plane and every feature was painted on. In profile a cat was a brick. There
is a small muzzle in front of the skull now — pink nose, mouth below it, and a
lighter muzzle patch, which is what makes it read as a nose rather than a bump.
Every cat has it, including Aurora, Nova, Midnight and the ghost.

**The faces are also softer.** Each eye was 2x2 in a face only 5 texels tall, the
mouth was a hard black bar straight across, and the brow was a near-black band.
Correct, but stern. The eyes are 2x3 now — a kitten's proportions rather than an
adult cat's — the highlight stays, the brow is softened toward the fur, and the
mouth is a warm brown instead of black. Nothing was added; the same handful of
texels simply sit where a young face has them.

**The cat door no longer breaks into dirt.** Break a block in Bedrock and the
particles are sampled from its own texture, and a block with no collision box
sprays them through the whole cube. The cat door's texture was a single flat
brown — eight units from vanilla dirt — so knocking one down produced a cloud of
what looked exactly like dirt in the middle of your living room. The kids
reported it as "it has a dirt effect when you take it away", which is precisely
what it was.

The door now has a dark frame, a pale flap and a visible hinge, so it reads as a
door and its particles read as anything but soil. The same check caught the
**food bowl**, whose rim colour was four units from dirt; it is light birch now.

**A generator was quietly accumulating again.** `mjau:on_tame` had grown to nine
copies of the same component group, one per build. Harmless to the engine, but it
is the same fault that once made every kitten spawn wearing a bow, and the old
guard only knew how to recognise that one shape. It checks every list now.


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
