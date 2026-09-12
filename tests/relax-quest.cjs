const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const source = fs.readFileSync(require('node:path').join(__dirname, '../PurrfectCompanions_BP/scripts/main.js'), 'utf8');
const code = source.slice(source.indexOf('function lugnStund('), source.indexOf('function finnsMobel('));
let awards = 0, messages = 0, complete = false, owner = 'p1';
const pl = { id: 'p1', dimension: {id:'overworld'}, location: {x:0,y:0,z:0}, sendMessage(){messages++;} };
function cat(id){ const props=new Map(); return {id,dimension:{id:'overworld'},location:{x:0,y:0,z:0},getComponent:()=>({tamedToPlayerId:owner}),getDynamicProperty:k=>props.get(k),setDynamicProperty:(k,v)=>props.set(k,v)}; }
const a=cat('a'), b=cat('b');
const ctx={catHavenWorld:true, world:{getAllPlayers:()=>[pl]}, avstandMellan:(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z),hasAward:()=>complete,give:()=>{awards++;complete=true;}};
vm.createContext(ctx); vm.runInContext(code,ctx);
const run=(c,s)=>ctx.lugnStund(c,s);
run(a,'tv'); assert.equal(awards,0);
ctx.catHavenWorld=false;run(a,'spa');assert.equal(messages,0);ctx.catHavenWorld=true;

pl.dimension.id='nether';run(a,'spa');assert.equal(messages,0);pl.dimension.id='overworld';
pl.location.x=7;run(a,'spa');assert.equal(messages,0);pl.location.x=0;
run(a,'spa');run(a,'spa');assert.equal(messages,1);
run(b,'tv');assert.equal(awards,0);

// Fresh runtime: persisted cat receipt still works after reload.
vm.runInContext(code,ctx);run(a,'tv');assert.equal(awards,1);
run(a,'tv');run(b,'spa');assert.equal(awards,1);assert.equal(messages,1);
console.log('PASS: order, same cat, distance, dimension, world guard, reload and one-time reward');

// Verify actual reward implementation and persisted duplicate protection.
let xp=0, items=[], props=new Map();
const player={id:'reward-player', setDynamicProperty:(k,v)=>props.set(k,v), getDynamicProperty:k=>props.get(k),
 addTag(){}, onScreenDisplay:{setTitle(){}}, playSound(){}, addExperience:n=>xp+=n,
 getComponent:()=>({container:{addItem:i=>items.push(i)}})};
const rewardCode=source.slice(source.indexOf('function hasAward('),source.indexOf('// PROGRESS-RAPPORTEN:'));
const rewards={awarded:new Map(),console:{log(){}},ItemStack:class {constructor(id,n){this.id=id;this.n=n;}}};
vm.createContext(rewards);vm.runInContext(rewardCode,rewards);
rewards.give(player,'lugn_stund');rewards.awarded.clear();rewards.give(player,'lugn_stund');
assert.equal(xp,25);assert.equal(items.length,1);assert.equal(items[0].id,'mjau:godis');assert.equal(items[0].n,6);
console.log('PASS: actual give() pays 25 XP and 6 treats once, including after memory-cache reset');
