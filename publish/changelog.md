## 2.3.3 — Things that sit where they should

Three fixes, all found by playing:

- **Outfits swung away from the cat.** Every accessory rotated around its own
  pivot point instead of the body part it belongs to, so the crown flew off to
  the side whenever the cat turned its head. Hats, saddles, capes and backpacks
  were all affected.
- **The tail was stubby.** It had been seated one unit too far into the body,
  hiding half its length. It now meets the body flush.
- **Cats could glide without moving their legs.** The sitting pose could only be
  left when the sit flag cleared. Movement now always breaks it.

## 2.3.2 — Readable button prompts

Standing next to a cat, or riding one, showed a raw translation key instead of a
word. Minecraft builds the dismount prompt from the entity id, and there is no
built-in text behind it for custom creatures. Every prompt the add-on can
produce is now spelled out: *Put on*, *Ride*, *Mount*, *Dismount*.

## 2.3.1 — Snow's ears

Snow is a white cat, so her ears disappeared into the rest of her coat. They are
now grey with a pink inner, clearly separated from the fur.

Includes everything from 2.3.0, where outfits finally became visible on the cat.
