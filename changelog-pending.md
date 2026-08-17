# Ej publicerat på CurseForge ännu

## 3.28.0 — Dress like your cat

The kids asked for it: *you* should be able to wear cat gear, not just the cat.

**A four-piece cat suit.** Hood with ears and pink insides, a vest with a pale
chest, darker trousers, and paws with pink pads. Leather and wool, the same
materials the cats' own outfits are made of. It protects like iron — 2, 6, 5
and 2 — so wearing it is a real choice rather than only dress-up, and it takes
enchantments and mending like any other armour.

Until now everything in this pack was worn by a cat. Nothing had ever been
drawn on a player, and the pack had no attachables at all — the parts that put
something on your own body. All four pieces come out of one table in
`tools/make_player_gear.py`: geometry, textures, attachables, items, recipes.

**Also in this release**
- The trousers recipe was, letter for letter, vanilla's leather leggings. You
  would have crafted vanilla trousers and wondered where the ears went. Caught
  before shipping by the recipe check that compares every recipe against a
  snapshot of vanilla's.
- New checks for anything worn on a player: the geometry and texture have to
  exist, the declared texture size has to match the actual image, and the bones
  have to be the player skeleton's. Wrong bone names put the clothes in the
  ground, and no server test can see that.
- Icon cleanup only deletes icons it made itself now. The old rule was "keep a
  list, delete the rest", and that list was forgotten three times — Ginger's
  spawn egg, the guard dog's face and the secret cats' icons were each deleted
  on the next build.
