// Kommer spelaren åt ryggsäckens last? (3.25.0)
//
// replaceitem i slot.inventory bevisar att containern finns, men inte att en
// spelare kommer åt den. Första försöket letade efter paketet container_open
// och fick inget — men inte heller från en KISTFÖRSEDD VANILJAÅSNA i samma
// körning. Kontrollen visade att provet inte kunde avgöra frågan, så vägen in
// gjordes oberoende av den inbyggda luckan: smyg intill katten, så lämnar hon
// över lasten (paketets 20-tick-loop).
//
// DEN gesten är boten faktiskt bra på: den kräver bara position och smygflagga
// i player_auth_input — inga interaktionspaket, inget klienthandslag. Facit
// hämtas från servern med testfor @p[hasitem=...]: ligger smaragden i botens
// inventarie har överlämningen skett.
//
// Byggd på interact-test.js (samma stenlåda, samma auth_input-ström).
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
  runPhase(true).catch(e => fail(e.stack || e.message))
}, 500)

async function runPhase (first) {
  const NAME = first ? 'TestKatt' : 'Provkatt'
  const client = bp.createClient({ host: '127.0.0.1', port: 19199, username: NAME, offline: true })
  const state = { catId: null, myPos: null, registry: {}, inv: [], wantCat: !first, opens: [] }

  client.on('error', (e) => fail('client error: ' + e.message))
  client.on('disconnect', (p) => { if (step !== 'done' && step !== 'reconnect') fail('disconnect: ' + JSON.stringify(p.message || p)) })
  client.on('start_game', (p) => { state.myPos = p.player_position; state.myId = p.runtime_entity_id })
  client.on('move_player', (p) => { if (p.runtime_id === state.myId) state.myPos = p.position })
  client.on('inventory_content', (p) => {
    if (p.window_id === 'inventory' || p.window_id === 0) state.inv = p.input || []
  })
  client.on('add_entity', (p) => {
    if (!p.entity_type) return
    log(`ADD ${p.entity_type} @ ${Math.round(p.position.x)},${Math.round(p.position.y)},${Math.round(p.position.z)}`)
    if (!p.entity_type.startsWith('mjau:') && p.entity_type !== 'minecraft:donkey') return
    const naraLadan = Math.abs(p.position.x - 3) < 8 && Math.abs(p.position.y - 102) < 6 &&
                      Math.abs(p.position.z - 3) < 8
    if (!naraLadan) return
    if (p.entity_type === 'minecraft:donkey' && !state.donkeyId) {
      state.donkeyId = p.runtime_id
      log(`DONKEY runtime_id ${state.donkeyId}`)
    }
    if (p.entity_type === 'mjau:misty' && !state.catId && state.wantCat) {
      state.catId = p.runtime_id
      state.catPos = p.position
      log(`CAT runtime_id ${state.catId}`)
    }
  })
  // KONTROLLEN: framstegsrapporten ("Kattens rapport") utlöses av EXAKT samma
  // gest — smyga inom 2,5 block från en tämjd katt — och är bevisad på riktig
  // Xbox sedan 3.23.0. Kommer den inte till boten heller är det botens
  // smygflagga som inte biter, inte överlämningen som är trasig. Utan den här
  // kontrollen går de två felen inte att skilja åt.
  client.on('text', (p) => {
    const t = JSON.stringify(p.message || '') + JSON.stringify(p.parameters || '')
    if (/rapport|report|uppdrag|quests/i.test(t)) { state.rapport = true; log('RAPPORT mottagen') }
  })

  // Behålls som biinformation: öppnas den inbyggda luckan ändå för någon är
  // det en bonus — men testet hänger inte på den.
  client.on('container_open', (p) => {
    state.opens.push(p)
    log(`CONTAINER_OPEN type=${p.container_type} id=${p.window_id}`)
  })

  await new Promise(res => client.on('spawn', res))
  client.queue('request_chunk_radius', { chunk_radius: 8, max_radius: 8 })

  let tick = 0
  let sneaking = false
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
        input_data: { _value: 0n, ...NOFLAGS, sneaking, sneak_down: sneaking, persist_sneak: sneaking },
        input_mode: 'mouse', play_mode: 'normal', interaction_model: 'classic',
        interact_rotation: { x: aimPitch, z: aimYaw },
        tick: BigInt(tick++), delta: { x: 0, y: 0, z: 0 },
        analogue_move_vector: { x: 0, z: 0 },
        camera_orientation: { x: 0, y: 0, z: 1 },
        raw_move_vector: { x: 0, z: 0 },
      })
    } catch (e) { clearInterval(ticker); fail('auth_input: ' + e.message) }
  }, 100)

  // FAS A bygger scenen och kopplar ner: dynamiska add_entity når aldrig boten,
  // katten måste komma i chunk-strömmen till en NY spelare (samma lärdom som
  // interact-test.js).
  step = 'scen'
  if (first) {
    // TICKINGAREA FÖRST. Utan den ligger chunkarna vid lådan oladdade —
    // fill och summon rapporterar ingenting och katten finns helt enkelt inte
    // när fas B letar efter den. (purrfect-test tömmer världens db varje
    // körning, så gårdagens tickingarea finns inte kvar.)
    say('tickingarea add 0 96 0 16 110 16 boxen')
    await sleep(1500)
    say('fill 0 100 0 6 104 6 stone hollow')
    await sleep(1500)
    say('testforblock 0 100 0 stone')
    await sleep(800)
    for (const c of ['misty', 'hazel', 'mocha', 'snow']) say(`kill @e[type=mjau:${c}]`)
    await sleep(1500)
    say('summon mjau:misty 4 102 4')
    await sleep(1500)
    // Tam + ryggsäck via kommando: den här körningen prövar ÖPPNANDET, inte
    // tämjningsfiltren (dem täcker interact-test.js).
    say('event entity @e[type=mjau:misty] mjau:on_tame')
    await sleep(1000)
    say('event entity @e[type=mjau:misty] mjau:on_ryggsack_1')
    await sleep(1000)
    // LASTEN som ska lämnas över. Smaragd: inget annat i testvärlden ger
    // spelaren en smaragd av misstag, så facit blir entydigt.
    say('replaceitem entity @e[type=mjau:misty,x=4,y=102,z=4,r=8] slot.inventory 0 emerald 1')
    await sleep(1000)
    say('setworldspawn 3 101 3')
    await sleep(1500)
    step = 'reconnect'
    clearInterval(ticker)
    client.disconnect()
    await sleep(2500)
    return runPhase(false)
  }

  step = 'vanta-katt'
  for (let w = 0; w < 20 && !state.catId; w++) await sleep(500)
  if (!state.catId) {
    srvlog = ''
    say('testfor @e[type=mjau:misty,x=4,y=102,z=4,r=8]')
    await sleep(1500)
    log('SRV: ' + JSON.stringify(srvlog.split('\n').filter(l => /Found|No targets/.test(l))))
    return fail('katten kom aldrig i chunk-strömmen')
  }

  // SMYG INTILL. Boten står redan i lådan bredvid katten; det enda som behövs
  // är smygflaggan i strömmen och att paketets loop hinner snurra (var 20:e
  // tick). Tio sekunder är gott om marginal.
  step = 'smyg'
  sneaking = true
  await sleep(10000)
  sneaking = false

  step = 'facit'
  srvlog = ''
  say('testfor @p[hasitem={item=emerald,quantity=1..}]')
  await sleep(2000)
  const fick = /Found/.test(srvlog)
  srvlog = ''
  say('testfor @e[type=mjau:misty,x=4,y=102,z=4,r=8,hasitem={item=emerald,location=slot.inventory}]')
  await sleep(2000)
  const kvarHosKatten = /Found/.test(srvlog)

  clearInterval(ticker)
  step = 'done'
  log(`LUCKAN  container_open: ${state.opens.length > 0 ? 'JA (bonus)' : 'nej'}`)
  log(`KONTROLL framstegsrapporten (samma gest, beprövad): ${state.rapport ? 'kom' : 'kom INTE'}`)
  if (fick && !kvarHosKatten) {
    log('OK   ÖVERLÄMNING — smaragden gick från kattens väska till spelaren')
    return cleanup(0)
  }
  if (!state.rapport) {
    log('OKÄNT botens smygflagga når inte servern — varken överlämningen ELLER den')
    log('      beprövade framstegsrapporten löste ut. Frågan är obesvarad här.')
    return cleanup(2)
  }
  log(`FAIL överlämningen uteblev fast rapporten kom (smaragd: ${fick}, kvar hos katten: ${kvarHosKatten})`)
  cleanup(1)
}
