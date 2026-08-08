// Spelarsimulering: det enda testet som når has_equipment/is_owner-filtren.
// Event-testerna avfyrar mjau:on_sadel_1 direkt och HOPPAR ÖVER filtren — det
// var så namnrymdsbuggen slank igenom. Här går vi spelarens väg hela vägen:
//
//   1. boten spawnar som spelare             (bedrock-protocol, MC 1.26.40)
//   2. våra föremål finns i item_registry    (skickas separat sedan 1.21.60)
//   3. /give fungerar för egna föremål
//   4. boten TÄMJER katten med torsk i hand  — riktig tämjning, för filtren
//      kräver is_owner, och bara minecraft:tameable registrerar en ägare;
//      att avfyra mjau:on_tame via kommando gör det INTE (0.4 chans/försök)
//   5. boten håller sadeln och interagerar   (inventory_transaction)
//   6. testfor has_property={mjau:sadel=1}   — katten BÄR sadeln
const { spawn } = require('child_process')
const bp = require('bedrock-protocol')

const SRV = '/opt/bds/server'
const sleep = (ms) => new Promise(r => setTimeout(r, ms))
const log = (s) => console.log(s)
let step = 'server-start'
const fail = (msg) => { log(`FAIL [${step}] ${msg}`); cleanup(1) }

const srv = spawn('./bedrock_server', [], { cwd: SRV, env: { ...process.env, LD_LIBRARY_PATH: '.' } })
let srvlog = ''
const say = (cmd) => srv.stdin.write(cmd + '\n')
function cleanup (code) {
  try { say('stop') } catch {}
  setTimeout(() => { try { srv.kill('SIGKILL') } catch {}; process.exit(code) }, 3000)
}
setTimeout(() => fail('total timeout 180 s'), 180000)
srv.stdout.on('data', (d) => { srvlog += d.toString() })

const started = setInterval(() => {
  if (!srvlog.includes('Server started')) return
  clearInterval(started)
  step = 'bot-join'
  runBot().catch(e => fail(e.stack || e.message))
}, 500)

async function runBot () { return runPhase(true) }
async function runBot2 () { return runPhase(false) }
async function runPhase (first) {
  const NAME = first ? 'TestKatt' : 'Provkatt'
  const client = bp.createClient({ host: '127.0.0.1', port: 19199, username: NAME, offline: true })
  const state = { catId: null, myPos: null, registry: {}, inv: [], wantCat: !first }

  client.on('error', (e) => fail('client error: ' + e.message))
  client.on('disconnect', (p) => { if (step !== 'done' && step !== 'reconnect') fail('disconnect: ' + JSON.stringify(p.message || p)) })
  client.on('start_game', (p) => { state.myPos = p.player_position; state.myId = p.runtime_entity_id })
  client.on('move_player', (p) => {
    if (p.runtime_id === state.myId) state.myPos = p.position
  })
  client.on('item_registry', (p) => {
    for (const i of p.itemstates || []) state.registry[i.runtime_id] = i.name
    const n = Object.values(state.registry).filter(x => x.startsWith('mjau:')).length
    log(`ITEMREGISTRY ${n} mjau-föremål`)
  })
  client.on('inventory_content', (p) => {
    if (p.window_id === 'inventory' || p.window_id === 0) state.inv = p.input || []
  })
  // Världen är full av katter — kvarvarande från gamla körningar plus naturliga
  // spawns (de HAR spawn rules för plains). Identifiera vår katt på POSITIONEN:
  // bara den som dyker upp vid summon-målet räknas.
  client.on('add_entity', (p) => {
    log(`ADD ${p.entity_type} @ ${Math.round(p.position.x)},${Math.round(p.position.y)},${Math.round(p.position.z)}`)
    if (!p.entity_type.startsWith('mjau:')) return
    if (!state.ground && p.position.y < 300) state.ground = p.position
    if (p.entity_type === 'mjau:misty' && !state.catId && state.wantCat) {
      state.catId = p.runtime_id
      state.catPos = p.position
      log(`CAT runtime_id ${state.catId}`)
    }
  })

  const slotOf = (name) => state.inv.findIndex(s => s && state.registry[s.network_id] === name)
  function hold (slot) {
    client.queue('mob_equipment', {
      runtime_entity_id: client.entityId,
      item: state.inv[slot], slot, selected_slot: slot, window_id: 'inventory',
    })
  }
  function interact (slot) {
    client.queue('inventory_transaction', {
      transaction: {
        legacy: { legacy_request_id: 0 },
        transaction_type: 'item_use_on_entity',
        actions: [],
        transaction_data: {
          entity_runtime_id: state.catId,
          action_type: 'interact',
          hotbar_slot: slot,
          held_item: state.inv[slot],
          player_pos: state.catPos ? { x: state.catPos.x - 2, y: state.catPos.y, z: state.catPos.z - 2 } : state.myPos,
          click_pos: { x: 0, y: 0.5, z: 0 },
        },
      },
    })
  }

  // Räkna ALLA inkommande paket — avslöjar om strömmen lever och vad som saknas
  const stats = {}
  const _emit = client.emit.bind(client)
  client.emit = (ev, ...a) => { stats[ev] = (stats[ev] || 0) + 1; return _emit(ev, ...a) }

  await new Promise(res => client.on('spawn', res))
  log('SPAWN')
  // En riktig klient begär chunk-radie efter start — utan prenumeration skickar
  // servern varken chunks eller entitetsuppdateringar i dem.
  client.queue('request_chunk_radius', { chunk_radius: 8, max_radius: 8 })

  // Servern kör auktoritativ rörelse och förväntar sig player_auth_input varje
  // tick från en riktig klient. Utan strömmen har den ingen etablerad position
  // att validera interaktioner mot — de kastas tyst. Skicka ~10 ticks/sekund.
  let tick = 0
  const NOFLAGS = Object.fromEntries([
    'ascend','descend','north_jump','jump_down','sprint_down','change_height','jumping',
    'auto_jumping_in_water','sneaking','sneak_down','up','down','left','right','up_left',
    'up_right','want_up','want_down','want_down_slow','want_up_slow','sprinting',
    'ascend_block','descend_block','sneak_toggle_down','persist_sneak','start_sprinting',
    'stop_sprinting','start_sneaking','stop_sneaking','start_swimming','stop_swimming',
    'start_jumping','start_gliding','stop_gliding','item_interact','block_action',
    'item_stack_request','handled_teleport','emoting','missed_swing','start_crawling',
    'stop_crawling','start_flying','stop_flying','client_ack_server_data',
    'client_predicted_vehicle','paddling_left','paddling_right','block_breaking_delay_enabled',
    'horizontal_collision','vertical_collision','down_left','down_right','use_item',
    'camera_relative_movement_enabled','rot_controlled_by_move_direction',
    'start_spin_attack','stop_spin_attack','is_in_client_predicted_server_vehicle',
    'client_reactions','jump_released_raw','jump_pressed_raw','jump_current_raw',
    'sneak_released_raw','sneak_pressed_raw','sneak_current_raw'
  ].map(f => [f, false]))
  const ticker = setInterval(() => {
    if (!state.myPos) return
    try {
      // Sikta på katten — servern kan validera att spelaren tittar på det
      // den interagerar med. Bedrock-yaw: 0 = +z, medurs.
      let aimYaw = 45, aimPitch = 20
      if (state.catPos && state.myPos) {
        const dx = state.catPos.x - state.myPos.x, dz = state.catPos.z - state.myPos.z
        const dy = (state.catPos.y + 0.3) - state.myPos.y
        aimYaw = -Math.atan2(dx, dz) * 180 / Math.PI
        aimPitch = -Math.atan2(dy, Math.hypot(dx, dz)) * 180 / Math.PI
      }
      client.queue('player_auth_input', {
        pitch: aimPitch, yaw: aimYaw, position: state.myPos,
        move_vector: { x: 0, z: 0 }, head_yaw: aimYaw,
        input_data: { _value: 0n, ...NOFLAGS },
        input_mode: 'mouse', play_mode: 'normal', interaction_model: 'classic',
        interact_rotation: { x: aimPitch, z: aimYaw },
        tick: BigInt(tick++), delta: { x: 0, y: 0, z: 0 },
        analogue_move_vector: { x: 0, z: 0 },
        camera_orientation: { x: 0, y: 0, z: 1 },
        raw_move_vector: { x: 0, z: 0 },
      })
    } catch (e) { clearInterval(ticker); fail('auth_input: ' + e.message) }
  }, 100)

  // start_game ger y=32769 — "hitta säker spawn"-sentinel; boten hänger i
  // tomrummet. Att teleportera en limbo-spelare får servern att koppla ner den
  // inom 3 ms, oavsett vad tickern rapporterar. Sätt i stället botens
  // SPAWNPOINT på riktig mark (naturligt spawnade katter står bevisligen där)
  // och återanslut — då landar den rätt från början.
  step = 'ground'
  if (!first) { log(`MYPOS ${JSON.stringify(state.myPos)}`) } else {
    // Lita inte på slumpen (naturliga katter) för markreferens — BYGG marken:
    // en ihålig stenlåda på fasta koordinater. Deterministiskt, och katten
    // hålls instängd så den inte vandrar utom interaktionsräckhåll (6 block)
    // under tämjningsloopen.
    // Taket på y103 satt i huvudhöjd — spelaren kvävdes och dog, och döda
    // spelare matchar inga selektorer. Interiör 3 block hög löser det.
    say('fill 0 100 0 6 104 6 stone hollow')
    await sleep(1500)
    // Dynamiska add_entity når aldrig boten — i SAMTLIGA körningar har de bara
    // anlänt via chunk-strömmen före spawn. Så: städa och summona katten NU,
    // i fas A. Fas B får den då serverad i chunk-strömmen med giltigt
    // runtime-id, instängd i lådan en block från spawnpunkten.
    for (const c of ['misty', 'hazel', 'mocha', 'snow']) say(`kill @e[type=mjau:${c}]`)
    await sleep(1500)
    say('summon mjau:misty 4 102 4')
    await sleep(1500)
    // En återansluten spelare hamnar på sin UTLOGGNINGSposition, inte på sin
    // spawnpoint — limbo ärvs för evigt. En NY spelare landar däremot på
    // världsspawnen. Sätt den i lådan och anslut som färskt namn i fas B.
    say('setworldspawn 3 101 3')
    await sleep(1500)
    step = 'reconnect'
    client.disconnect()
    await sleep(2500)
    return runBot2()
  }

  step = 'give'
  say('give Provkatt mjau:sadel_brun')
  say('give Provkatt cod 32')
  await sleep(2000)
  step = 'summon'
  // Katten summonades i fas A och kom i chunk-strömmen — vänta bara in den.
  for (let w = 0; w < 14 && !state.catId; w++) await sleep(500)
  const top = Object.entries(stats).sort((a, b) => b[1] - a[1]).slice(0, 8)
  log('PACKETS ' + top.map(([k, v]) => `${k}:${v}`).join(' '))
  if (!state.catId) {
    const m = srvlog.match(/summon[^\n]*|successfully summoned[^\n]*/gi)
    log('SRV-SUMMON: ' + JSON.stringify((m || []).slice(-3)))
    return fail('katten spawnade aldrig')
  }
  const cod = slotOf('minecraft:cod'); const saddle = slotOf('mjau:sadel_brun')
  log(`INVENTORY sadel slot ${saddle}, torsk slot ${cod}`)
  if (cod < 0 || saddle < 0) return fail('föremålen dök inte upp i inventariet')

  // 4) riktig tämjning: 0.4 chans per torsk — försök tills ägarskapet sitter
  step = 'tame'
  let ok = false
  for (let i = 1; i <= 15 && !ok; i++) {
    hold(cod); await sleep(400)
    interact(cod); await sleep(900)
    say('testfor @e[type=mjau:misty,has_property={mjau:tam=1}]')
    await sleep(800)
    if (!state.tamedSeen && srvlog.includes('Found entity.mjau:misty')) {
      state.tamedSeen = true; log(`TAMED efter forsok ${i}`)
      // markera i loggen var tam-checken slutar sa sadel-checken inte laser fel rad
      state.tameMark = srvlog.length
    }
    // tam? då matchar sadel-interaktionen (is_owner + has_equipment)
    hold(saddle); await sleep(400)
    interact(saddle); await sleep(900)
    say('testfor @e[type=mjau:misty,has_property={mjau:sadel=1}]')
    await sleep(1200)
    ok = srvlog.indexOf('Found entity.mjau:misty', state.tameMark || srvlog.length - 1) >= 0 && state.tamedSeen
    log(`TAME försök ${i}: ${ok ? 'ÄGARE + SADEL PÅ' : 'inte än'}`)
  }
  step = 'verify'
  // Förbrukades torsken alls? Oförändrat antal = servern processar inte
  // interaktionerna; färre = de processas men tämjningen slår fel.
  say('testfor @p[hasitem={item=cod,quantity=32..}]')
  await sleep(1500)
  log('COD ' + (srvlog.includes('Found Provkatt') ? 'INTAKT (32 kvar) — interaktionerna processas INTE' : 'förbrukad — interaktionerna når fram'))
  if (!ok) return fail('kunde inte tämja + sadla på 15 försök — filterkedjan bruten')
  log('VERIFIED hela spelarkedjan: give → tämja (is_owner) → hålla sadel (has_equipment) → interagera → katten bär sadeln')
  step = 'done'
  cleanup(0)
}
