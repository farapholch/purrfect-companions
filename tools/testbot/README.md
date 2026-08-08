# Test bot (bedrock-protocol)

A real Minecraft Bedrock client that connects to the test server. Lives in
`/opt/purrfect-testbot` (node_modules stay out of this repo); these are the
versioned scripts.

- **smoke-test.js** — wired into `purrfect-test` as an optional stage. Proves
  what the command side never can: the client reaches spawn on the current MC
  version, every custom item is present in `item_registry` (sent as its own
  packet since 1.21.60), `/give` works for custom items, custom entities stream
  with correct type names, and entity-property syncs flow.
- **interact-test.js** — the attempt to simulate use-item-on-entity (taming
  with cod, saddling). Everything up to the interaction works; the server
  consumes the packets but never processes them, most likely because a modern
  authoritative server requires the full client handshake (tick ack, movement
  prediction) before honouring interaction transactions. Kept as documentation
  and a starting point.
- **join-test.js** — minimal join probe.

Hard-won findings encoded in these scripts:

- `start_game.player_position` can be the find-safe-spawn sentinel (y 32769) —
  the bot hangs in limbo. Teleporting a limbo player disconnects it within
  milliseconds. A reconnecting player spawns at its logout position, so limbo
  is inherited forever; a NEW username spawns at world spawn. The fix: build a
  hollow stone box at fixed coordinates, `setworldspawn` inside it, connect
  with a fresh name.
- The box interior must be 3 blocks tall — with the ceiling at head height the
  player suffocates, and dead players match no selectors.
- Dynamic `add_entity` broadcasts never reach the bot; entities only arrive in
  the chunk stream before spawn. Summon the target entity BEFORE the client
  connects and capture its runtime id from the stream.
- The server expects a continuous `player_auth_input` stream (~10/s). The
  claimed position must always match the server's view of the player.
- `execute as <name>` does not match in BDS console commands; use absolute
  coordinates.
