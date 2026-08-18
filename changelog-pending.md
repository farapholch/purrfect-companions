# Ej publicerat på CurseForge ännu

## 3.30.0 — Dress like your cat, and two new neighbours in Cat Haven

The kids asked for it: *you* should be able to wear cat gear, not just the cat.

**A four-piece cat suit.** Hood with ears and pink insides, a vest with a pale
chest, darker trousers, and paws with pink pads. Leather and wool, the same
materials the cats' own outfits are made of. It protects like iron — 2, 6, 5
and 2 — so wearing it is a real choice rather than only dress-up, and it takes
enchantments and mending like any other armour.

**And the suit does something.** One power per piece, so each is worth wearing
on its own — the hood gives night vision, because cats see in the dark; the
vest gives resistance; the trousers give speed; and the paws give a soft
landing, so you take no fall damage. Wear all four and you get speed II and a
higher jump on top, and every cat around you purrs and heals.

Until now everything in this pack was worn by a cat. Nothing had ever been
drawn on a player, and the pack had no attachables at all — the parts that put
something on your own body. All four pieces come out of one table in
`tools/make_player_gear.py`: geometry, textures, attachables, items, recipes.

**Ginger and Domino have moved into Cat Haven.** They were added to the add-on
after the world was built, so until now they only existed out in the wild.
Ginger keeps to the grove in the north-west, where the third key lies. Domino
sits by the lighthouse and watches the sea. Find them, bring cod, and there are
two more quests on the list: *The Grove Keeper* and *The Lighthouse Shadow*.
The caretaker's handbook has a new page about both of them — he wrote it after
the rest of the book, which is why it is last.

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
