// Spelar-röktest: ansluter en RIKTIG klient (bedrock-protocol) till testservern
// och verifierar det servern aldrig kan se från kommandosidan:
//
//   JOIN        klienten tar sig hela vägen till spawn på aktuell MC-version
//   REGISTRY    alla egna föremål finns i item_registry som klienten får
//   GIVE        egna föremål går att ge till en spelare (verklig registrering)
//   ENTITIES    egna entiteter strömmas till klienten med rätt typnamn
//   PROPS       sync_entity_property-paket flödar (entity properties når klienter)
//
// Vad den INTE testar: interaktioner (använd-föremål-på-katt). Servern kräver
// fullt modernt klienthandslag (tick-ack, prediction) innan den processar
// interaktionspaket från klienten — dokumenterat försök i interact-test.js.
// Exit 0 = allt grönt.
const { spawn } = require('child_process')
const bp = require('bedrock-protocol')

const SRV = '/opt/bds/server'
const sleep = (ms) => new Promise(r => setTimeout(r, ms))
const checks = { join: false, registry: 0, give: false, entities: new Set(), props: 0, form: '' }
let srvlog = ''

const srv = spawn('./bedrock_server', [], { cwd: SRV, env: { ...process.env, LD_LIBRARY_PATH: '.' } })
srv.stdout.on('data', (d) => { srvlog += d.toString() })
const say = (cmd) => srv.stdin.write(cmd + '\n')
const finish = (code) => {
  try { say('stop') } catch {}
  setTimeout(() => { try { srv.kill('SIGKILL') } catch {}; process.exit(code) }, 3000)
}
setTimeout(() => { console.log('FAIL timeout'); finish(1) }, 90000)

async function main () {
  while (!srvlog.includes('Server started')) await sleep(500)
  const client = bp.createClient({ host: '127.0.0.1', port: 19199, username: 'Provkatt', offline: true })
  const registry = {}
  client.on('error', (e) => { console.log('FAIL client: ' + e.message); finish(1) })
  client.on('item_registry', (p) => {
    for (const i of p.itemstates || []) registry[i.runtime_id] = i.name
    checks.registry = Object.values(registry).filter(x => x.startsWith('mjau:')).length
  })
  client.on('add_entity', (p) => { if (p.entity_type.startsWith('mjau:')) checks.entities.add(p.entity_type) })
  client.on('sync_entity_property', () => { checks.props++ })
  // KATTBOKENS MENY. Servern skickar modal_form_request när form.show() körs;
  // nyttolasten är formuläret som JSON, med rawtext-nycklarna OLÖSTA (klienten
  // översätter dem själv). Att paketet kommer fram bevisar att skriptet byggde
  // menyn, att servern kunde serialisera den och att den nådde en riktig klient.
  client.on('modal_form_request', (p) => { checks.form = String(p.data || '') })
  client.on('inventory_content', (p) => {
    for (const s of (p.input || [])) {
      if (!s) continue
      const id = registry[s.network_id]
      if (id === 'mjau:sadel_brun') checks.give = true
      // KATTBOKEN har en egen rad, inte bara en högre siffra i REGISTRY:
      // guiden är paketets enda ingång för en ny spelare, och ett föremål som
      // tyst faller ur registret gör hela funktionen onåbar utan att något
      // annat test märker det.
      if (id === 'mjau:kattbok') checks.bok = true
    }
  })

  await new Promise(res => client.on('spawn', res))
  checks.join = true
  // säkra att minst en egen entitet finns inom synhåll för entitetskontrollen
  say('summon mjau:misty 4 102 4')
  say('give Provkatt mjau:sadel_brun')
  say('give Provkatt mjau:kattbok')
  say('scriptevent mjau:test_bok kor')
  say('scriptevent mjau:test_boksidor kor')
  await sleep(6000)

  const rows = [
    ['JOIN', checks.join],
    ['REGISTRY', checks.registry >= 40, `${checks.registry} mjau-föremål`],
    ['GIVE', checks.give, 'mjau:sadel_brun nådde inventariet'],
    ['BOK', checks.bok, 'mjau:kattbok nådde inventariet'],
    // UNDERSIDORNA rapporteras av SERVERN (console.log), inte till klienten —
    // därför läses serverloggen och inte ett paket. Kroken kräver en inloggad
    // spelare, så den hör hemma här och inte i live-testets kommandofas.
    ['BOKSIDOR', srvlog.includes('BOKSIDOR-TEST OK'),
      (srvlog.match(/BOKSIDOR-TEST OK: [^\n]*/) || ['inget svar'])[0].replace('BOKSIDOR-TEST OK: ', '')],
    ['BOKMENY', checks.form.includes('mjau.bok.titel') &&
       (checks.form.match(/mjau\.bok\.sekt\./g) || []).length >= 6,
      `formulär ${checks.form.length} tecken, ` +
      `${(checks.form.match(/mjau\.bok\.sekt\./g) || []).length} avdelningar`],
    ['ENTITIES', checks.entities.size >= 1, [...checks.entities].join(',')],
    ['PROPS', checks.props >= 1, `${checks.props} property-syncs`],
  ]
  let fail = 0
  for (const [name, ok, info] of rows) {
    console.log(`${ok ? 'OK  ' : 'FAIL'} ${name}${info ? ' — ' + info : ''}`)
    if (!ok) fail = 1
  }
  finish(fail)
}
main().catch(e => { console.log('FAIL ' + e.message); finish(1) })
