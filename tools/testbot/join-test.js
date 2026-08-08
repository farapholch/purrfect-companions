// Steg 1: kan boten alls spawna in på 1.26.40?
// Förra försöket (bedrock-protocol med protokolldata för 1.21) dog exakt här:
// anslöt, men kraschade i resource_pack_client_response och spawnade aldrig.
const bp = require('bedrock-protocol')

const client = bp.createClient({
  host: '127.0.0.1',
  port: 19199,
  username: 'TestKatt',
  offline: true,
})

let done = false
const die = (msg, code) => { if (!done) { done = true; console.log(msg); process.exit(code) } }

client.on('join', () => console.log('JOIN'))          // paketutbytet klart
client.on('spawn', () => die('SPAWN', 0))             // boten står i världen
client.on('error', (e) => die('ERROR ' + e.message, 1))
client.on('disconnect', (p) => die('DISCONNECT ' + JSON.stringify(p.message || p), 1))
setTimeout(() => die('TIMEOUT — ingen spawn på 45 s', 1), 45000)
