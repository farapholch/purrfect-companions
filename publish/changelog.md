## 2.5.0 — The cart you can sit in, the cat that obeys

Found by playing on Xbox, fixed and now machine-tested:

- **Cats no longer wander while ridden.** Their free-will behaviours — strolling,
  chasing, seeking out beds — switch off the moment a rider sits up, and return
  when the saddle comes off the agenda. A simulated rider now verifies the cat
  drifts 0.00 blocks with no input.
- **The Cat Cart is bigger, and you can finally sit in it.** The cart seat is now
  the first seat: interact and you sit IN the cart, steering like a sled, with
  the back seat free for a friend. A simulated player boards it and drives it
  eighteen blocks in every test run.

New things:

- **Food Bowl** — craft it from a bowl, planks and a cod; cats seek it out.
- **Unicorn Horn** — white, gold or pink, crafted around quartz, gold or
  amethyst. Combine with the wings.

## 2.4.1 — A tail that looks like a tail

The tail was a solid pillar — three blocks wide, three deep, straight up. It
is now slim and curves up and back the way a content cat carries it, and it
still sways. Every breed keeps its own tail colour.

Taming is also now visible to the server side, which tightens our automated
tests.

## 2.4.0 — Names, storage and a proper jump

**Item names were showing as raw ids.** A pack has to declare its languages in
`texts/languages.json`, and ours did not exist — so Minecraft ignored the
translations entirely and fell back to internal identifiers. Every name, and
every button prompt, now reads the way it was written.

- **The Cat Cart carries things.** Fifteen slots, donkey style. Sneak and
  interact to open it.
- **Cats jump higher.** Hold the jump button to charge it.

## 2.3.4 — Steering

Saddled cats carried two control systems at once: the player's own stick input,
and an AI goal that steered the cat towards where the rider was looking. The AI
goal ran at the highest possible priority, so it overrode the player every tick
and the reins felt dead. The AI goal is gone; you steer the cat directly.

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
