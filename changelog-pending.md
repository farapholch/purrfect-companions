# Ej publicerat på CurseForge ännu

## 3.31.4 — Dress like your cat, and two new neighbours in Cat Haven

The kids asked for it: *you* should be able to wear cat gear, not just the cat.

**A four-piece cat suit.** Hood with ears and pink insides, a vest with a pale
chest, darker trousers, and paws with pink pads. Leather and wool, the same
materials the cats' own outfits are made of. It protects like iron — 2, 6, 5
and 2 — so wearing it is a real choice rather than only dress-up, and it takes
enchantments and mending like any other armour.

**The vest is a vest.** It has shoulder pieces and leaves your forearms bare.
The first version wrapped the whole arm and sat flush against the chest, so
with the outward bevel every armour piece has, the two grew into one wide slab
— reported from an Xbox as "you have basically no arms". Sleeveless is also
what the name promised.

**The suit comes in four tiers.** Leather, iron, diamond and netherite. You do
not re-craft it — you upgrade the piece you already wear by combining it with
the metal, so the hood you made on day one is the hood you still have in
netherite. Protection climbs from 2/6/5/2 to 4/8/7/4, and each tier adds a
stronger power: jump strength in iron paws, resistance II and speed II in
diamond, fire resistance in a netherite hood. A full suit is only as strong as
its weakest piece — mix leather with netherite and you get the leather bonus,
which is a rule a seven-year-old can hold in their head.

**The hood has a face.** Amber eyes with mirrored highlights, a pink nose and whiskers — and ears that
actually clear the helmet. Reported from an Xbox: "no eyes and no ears". Both
were true. The ears were three quarters buried inside the helmet, which is
inflated a unit larger than the head; and the face only ever existed in the
16×16 inventory icon, never on the model you wear.

**And the suit does something.** One power per piece, so each is worth wearing
on its own — the hood gives night vision, because cats see in the dark; the
vest gives resistance; the trousers give speed; and the paws give a soft
landing, so you take no fall damage. Wear all four and you get speed II and a
higher jump on top, and every cat around you purrs and heals.

Until now everything in this pack was worn by a cat. Nothing had ever been
drawn on a player, and the pack had no attachables at all — the parts that put
something on your own body. All four pieces come out of one table in
`tools/make_player_gear.py`: geometry, textures, attachables, items, recipes.

**Ginger and Domino have moved into both worlds.** Star Harbour now wakes six
cats instead of four — the ginger one drifted in with a supply run and never
left, the black-and-white one was born aboard. The logbook says so on its
first page.

**In Cat Haven they have quests of their own.** They were added to the add-on after the
world was built, so until now they only existed out in the wild. Ginger keeps
to the grove in the north-west, where the third key lies. Domino
sits by the lighthouse and watches the sea. Find them, bring cod, and there are
two more quests on the list: *The Grove Keeper* and *The Lighthouse Shadow*.
The caretaker's handbook has a new page about both of them — he wrote it after
the rest of the book, which is why it is last.

**The fighters stop now.** Reported from play: you just kept flying forever.
The ship has no physics of its own — no gravity, no drag — and the code did
nothing at all when you were not holding a button, so whatever speed you had
stayed with you until the world ran out of sky. Let go and it now glides to a
stop in about a second. **And the sky is bigger than it was.** The leash was measured from the station
alone — but the crater, the relay mast and the probe sit 90, 95 and 96 blocks
out, so the warning started nagging fifteen blocks after you arrived at the
very place the logbook sent you to. It now reaches 150 blocks, and it does not
speak at all while you are near an outpost. The void beyond still has no ground
to land on and no way back, so the net stays — but it is there to catch someone
flying away, not someone flying there.

**Also in this release**
- The trousers recipe was, letter for letter, vanilla's leather leggings. You
  would have crafted vanilla trousers and wondered where the ears went. Caught
  before shipping by the recipe check that compares every recipe against a
  snapshot of vanilla's.
- New checks for anything worn on a player: the geometry and texture have to
  exist, the declared texture size has to match the actual image, and the bones
  have to be the player skeleton's. Wrong bone names put the clothes in the
  ground, and no server test can see that.
- The pack now has a hero image with all six cats in a meadow, a shorter
  gallery gif, and an outfit picture where every cat wears something different
  and one is fully kitted out.
- Icon cleanup only deletes icons it made itself now. The old rule was "keep a
  list, delete the rest", and that list was forgotten three times — Ginger's
  spawn egg, the guard dog's face and the secret cats' icons were each deleted
  on the next build.
