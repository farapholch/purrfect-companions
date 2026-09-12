const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../PurrfectCompanions_BP/scripts/main.js'), 'utf8');
// Run the actual production effect loops with a strict Bedrock property mock.
const start = source.indexOf('  // KATTSPA.');
const end = source.indexOf('  // EN påminnelse', start);
assert.ok(start > 0 && end > start);
for (const type of ['kattspa', 'katt_tv']) {
  let humor = 1, effects = 0, present = true;
  const pos = { x: 0, y: 0, z: 0 };
  const c = { id: 'cat', location: pos,
    setProperty: (_, value) => { assert.ok(value >= 0 && value <= 2); humor = value; },
    addEffect: () => effects++ };
  const ctx = { lugnStund() {}, tamda: [c], kattSpaPlatser: type === 'kattspa' ? [pos] : [],
    kattTvPlatser: type === 'katt_tv' ? [pos] : [],
    kattSpaSenast: new Map(), kattTvSenast: new Map(), system: { currentTick: 0 },
    las: () => humor, avstandMellan: (a,b) => Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z),
    finnsMobel: () => present, d: { spawnParticle() {}, playSound() {} } };
  const run = () => vm.runInNewContext(source.slice(start, end), ctx);
  run(); assert.equal(humor, 2);
  const firstEffects = effects;
  humor = 1; run(); assert.equal(humor, 1); assert.equal(effects, firstEffects);
  ctx.system.currentTick = 400; humor = 2; run();
  if (type === 'kattspa') assert.equal(effects, 2, 'happy cats still receive spa regeneration');
  ctx.system.currentTick = 800; humor = 0; run(); assert.equal(humor, 0);
  humor = 1; present = false; run(); assert.equal(humor, 1);
  present = true; c.location = { x: 5, y: 0, z: 0 }; run(); assert.equal(humor, 1);
}
console.log('PASS: TV/spa mood cap, cooldown, hunger, removal, distance and regeneration');
