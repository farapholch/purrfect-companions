# Furniture visual review (development after 3.54.0)

GameTests measure native navigation and position. Diagnostic renders sample the
real geometry, textures and animation keyframes. Neither is a graphical
Minecraft client inspection. The checks below remain pending in a real client.

Use the local development add-on in a copy of a Creative flat world. Keep cats
adult, fed and tamed, standing freely without saddles or carts. Stay within eight blocks;
bring cats within four blocks of the furniture. Leave two blocks clear around it.

1. Basket for Two: try Mocha and Snow together. Check separate cushions, settling,
   closed eyes and gentle breathing. Compare bare cats with doctor coat/booties
   and backpack/cape. Inspect paws, coat hems, cushions and tail attachments.
2. Cat Spa: check native walking into the shallow basin, settling at its floor
   and lifting a paw toward the lowered muzzle. Try coat/booties; verify water animation continues.
3. Cat TV: check the cat faces the screen and gently moves its head while the bird
   animates. Try a large Snow with raincoat/backpack and then a bare small Mocha.
4. Break and replace each furniture item from all four directions. The front
   should face the placing player. Try two identical furniture types with mixed
   directions. Check pre-existing furniture retains its original orientation.
5. During rest, remove furniture, command sitting, equip riding gear, walk away,
   and save/reload. Cats must regain normal movement when appropriate; a player's
   sitting command must remain under player control.

Capture a short clip from the front and side at normal game scale for each action.

6. Scratching board: try bare Mocha and clothed Snow in all four directions.
   Check alternating front paws touch the low sisal ramp, small fibre particles
   and quiet scratching sounds. Interrupt, reload and remove the board; effects
   must stop. Verify the front clearance and crafting recipe in Survival.

7. Window Perch: place its back against a glass window with clear space above
   and in front. Test all directions with adult Mocha and Snow, with/without
   raincoat/backpack. Check native hop onto the cushion, viewing direction,
   head/tail motion, then settling with closed eyes and breathing after 8 seconds.
   Look for window/frame clipping and interrupt both watching and sleep.

## Additional diagnostic review (2026-09-11, 3.57.1)

- `/tmp/pc-mobelgranskning.png` samples basket sleep, spa, TV and the window
  watch/lowering/sleep sequence using the actual meshes, textures and keyframes.
  Inspected doctor coat/booties on Mocha and cape/backpack or raincoat/backpack
  on Snow. No detached garments observed in these sampled poses. The render
  does not reproduce Minecraft lighting, interpolation or the native jump.
- Native tests now exercise eight paired basket visits, walls behind TV/spa/
  scratching board and a neighbouring hideaway in all directions. Window tests
  equip raincoat/backpack, retain adjacent glass, add a neighbouring hideaway
  and reject blocked headroom before testing the hop/watch/sleep cycle.
- Initial repeat reproduced a basket approach stop0.7004 blocks from the seat.
  A bounded final alignment now starts within0.8 blocks on the cushion; the
  final required seat tolerance remains0.05. Both cats must arrive before sleep.
- These additions do not complete the graphical-client checklist above. This
  server has no accessible graphical Minecraft client or desktop tool.

Final local results: all eight paired visits and all12 wall/neighbour scenarios
passed in `/tmp/pc-room-fixed-server.log`; all four clothed window scenarios
passed in `/tmp/pc-room-window-server.log`. Static suite passed in
`/tmp/pc-room-quick.log`. The3.57.1 archive was checked against the tested source
and public staging. The graphical-client checklist is still pending.

## Spa/TV photo regressions — local 3.58.0

The user supplied Minecraft photos of cats standing above the spa and TV. The
spa used a solid 9/16-block collision slab (soap-bottle height); TV collision
filled its entire block footprint. Spa now uses its 1/16-block basin floor,
with the native visit target centered inside the bath and precise arrival
alignment. Its full selection outline still includes the soap dispenser.
TV collision has a six-unit depth around the actual screen/stand instead of
a full-block platform; its viewing seat remains on the ground in front.

The targeted `tools/purrfect-gametest --spa-tv` case starts a tamed adult on top
of each object in the north-facing scenario, then checks native arrival, exact
height, facing, staying and interruption in four directions, with a wall and
neighbouring furniture. Wild spawn-egg cats and kittens still do not perform
adult tamed furniture visits. The new test does not claim to prevent all
entities from standing on the actual top edge of a television.

Diagnostic views: `/tmp/pc-spatv-poses.png`, small bare Mocha and large clothed
Snow, two bath frames and TV sitting. These are software renders; real-client
confirmation of the updated version remains necessary.
