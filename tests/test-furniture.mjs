import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../PurrfectCompanions_BP/scripts/furniture_visits.js',import.meta.url),'utf8');
const {FurnitureVisits,furnitureSeat}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
function setup(kind='basket',count=2){
 const type={basket:'mjau:sovkorg',spa:'mjau:kattspa',tv:'mjau:katt_tv',scratch:'mjau:klosbrada',window:'mjau:fonsterbadd',fountain:'mjau:kattfontan'}[kind];
 const d={id:'minecraft:overworld',block:type,facing:'north',getBlock(p){const facing=this.facing;return {permutation:{getState:()=>({north:'south',east:'west',south:'north',west:'east'})[facing]},typeId:p.x===0&&p.y===0&&p.z===0?this.block:p.y<0?'minecraft:stone':'minecraft:air',get isAir(){return this.typeId==='minecraft:air'},isLiquid:false}}};
 const players=[{dimension:d,location:{x:0,y:0,z:-2}}];
 const cats=Array.from({length:count},(_,i)=>({id:''+i,location:{x:i*.9,y:0,z:-1},p:{tam:1,humor:1},events:[],getProperty(k){return this.p[k.slice(5)]??0},getComponent(k){return k==='minecraft:is_baby'&&this.baby?{}:undefined},triggerEvent(e){this.events.push(e);if(e==='mjau:mobel_sitt')this.p.mobel=-1;else if(e==='mjau:mobel_av')this.p.mobel=0;else if(e.includes('vila_'))this.p.mobel={basket:5,spa:6,tv:7,scratch:8,window:11,window_sleep:12,fountain:14}[e.slice('mjau:mobel_vila_'.length)];else if(e.startsWith('mjau:mobel_'))this.p.mobel=1},setRotation(r){this.rotation=r}}));
 const v=new FurnitureVisits();let tick=0;
 const update=()=>v.update(d,cats,players,tick+=20,false);
 const arrive=()=>{for(const c of cats){const a=v.active.get(c.id);if(a)c.location={...a.seat}}update()};
 return{d,players,cats,v,update,arrive};
}
{
 const t=setup('basket',3);t.update();assert.equal(t.v.active.size,2);t.cats[0].location={...t.v.active.get('0').seat};t.update();assert.notEqual(t.cats[0].p.mobel,5);t.arrive();assert.equal(t.cats[0].p.mobel,5);assert.equal(t.cats[1].p.mobel,5);assert.equal(t.cats[2].p.mobel,undefined);assert.ok(Math.abs(t.cats[0].location.x-t.cats[1].location.x)>.8);t.d.block='minecraft:air';t.update();assert.equal(t.v.active.size,0);assert.equal(t.cats[0].p.mobel,0);assert.equal(t.cats[1].p.mobel,0);
}
{const t=setup('basket',1);t.update();assert.equal(t.v.active.size,0)}
for(const kind of ['spa','tv']){const t=setup(kind,1);t.update();t.arrive();assert.equal(t.cats[0].p.mobel,kind==='spa'?6:7);assert.equal(t.cats[0].rotation.y,0);t.cats[0].location.x+=1;t.update();assert.equal(t.v.active.size,0)}
for(const property of ['hungrig','sadel','vagn','leker']){const t=setup();t.update();t.arrive();t.cats[0].p[property]=1;t.update();assert.equal(t.v.active.size,0)}
{const t=setup();t.update();t.arrive();t.v.interrupt(t.cats[0],60);assert.equal(t.v.active.size,0)}
{const t=setup();t.update();for(let i=0;i<17;i++)t.update();assert.equal(t.v.active.size,0)}
{const t=setup();t.cats[0].p.mobel=5;t.update();assert.equal(t.cats[0].p.mobel,0);assert.ok(t.cats[0].events.includes('mjau:sovdags_av'))}
{const t=setup('tv',1);t.d.getBlock=()=>({typeId:'minecraft:stone',isAir:false});t.update();assert.equal(t.v.active.size,0)}
{const t=setup();t.update();t.arrive();t.players.length=0;t.update();assert.equal(t.v.active.size,0)}
{const t=setup();t.update();t.arrive();t.cats[0].p.mobel=-1;t.update();assert.equal(t.v.active.size,0);assert.equal(t.cats[0].p.mobel,-1)}
console.log('PASS furniture: paired arrival, capacity, orientation, interruption, hunger, riding, reload, obstruction, timeout');

for(const facing of ['north','east','south','west'])for(const kind of ['basket','spa','tv','scratch','window','fountain']){
 const t=setup(kind,kind==='basket'?2:1);t.d.facing=facing;t.update();
 assert.equal(t.v.active.size,t.cats.length);
 for(const c of t.cats)assert.ok(c.events.some(e=>e.endsWith('_'+facing)));
 t.arrive();t.update();assert.equal(t.cats[0].p.mobel,{basket:5,spa:6,tv:7,scratch:8,window:11,window_sleep:12,fountain:14}[kind]);
 const yaw={north:0,east:90,south:180,west:-90}[facing];
 assert.equal(t.cats[0].rotation.y,yaw+(kind==='basket'?(t.v.active.get('0').slot?-12:12):0));
 if(!['basket','spa','window'].includes(kind)){
  const a=t.v.active.get('0').seat;
  assert.ok(({north:a.z<0,east:a.x>1,south:a.z>1,west:a.x<0})[facing]);
 }
 t.d.facing=facing==='north'?'east':'north';t.update();assert.equal(t.v.active.size,0);
}
console.log('PASS four directions: native event, front seat, facing and rotation cancellation');

{const t=setup();t.update();for(const c of t.cats){const a=t.v.active.get(c.id);c.location={x:.5+(a.slot?.2:-.2),y:3/16,z:.5}}t.update();assert.ok(t.cats.every(c=>c.p.mobel<5));assert.ok([...t.v.active.values()].every(v=>['walk','align'].includes(v.phase)));t.arrive();assert.ok(t.cats.every(c=>c.p.mobel===5))}
console.log('PASS basket: no early stop in the shared center');
{const t=setup();t.update();for(const c of t.cats){const a=t.v.active.get(c.id);c.location={...a.seat,y:0}}t.update();assert.ok([...t.v.active.values()].every(v=>v.phase==='walk'))}
{const t=setup();t.update();const c=t.cats[0],a=t.v.active.get(c.id);c.location={...a.seat,x:a.seat.x+.15};c.clearVelocity=()=>{};let impulse;c.applyImpulse=v=>{impulse=v};t.update();assert.equal(a.phase,'align');assert.ok(impulse.x<0&&Math.hypot(impulse.x,impulse.z)<=.06);assert.equal(impulse.y,0);assert.notEqual(c.p.mobel,5);t.v.interrupt(c,80);assert.equal(t.v.active.size,0)}
console.log('PASS alignment: climb first, bounded horizontal step, wait for partner and interruption');

for(const reason of ['hungrig','sadel','vagn','leker','sit','damage','remove','away','reload','timeout']){
 const t=setup('scratch',1),effects=[];
 t.d.spawnParticle=(id,p)=>effects.push({id,p});t.d.playSound=(id,p,options)=>effects.push({id,p,options});
 t.update();assert.equal(effects.length,0);t.arrive();assert.equal(t.cats[0].p.mobel,8);
 assert.equal(effects.length,2);assert.equal(effects[0].id,'mjau:sisal_dust');
 assert.ok(effects[1].options.volume<.3);
 if(reason==='sit')t.cats[0].p.mobel=-1;
 else if(reason==='damage')t.v.interrupt(t.cats[0],60);
 else if(reason==='remove')t.d.block='minecraft:air';
 else if(reason==='away')t.players.length=0;
 else if(reason==='reload'){t.v.active.clear();t.v.cooldown.clear();}
 else if(reason==='timeout'){for(let i=0;i<8;i++)t.update();}
 else t.cats[0].p[reason]=1;
 const before=effects.length;t.update();assert.equal(t.v.active.size,0,reason);
 assert.equal(effects.length,before,reason);assert.equal(t.cats[0].p.mobel,reason==='sit'?-1:0);
}
console.log('PASS scratching: effects only during arrival-confirmed visits; hunger, gear, play, commands, damage, removal, distance, reload and timeout stop them');

{const t=setup('scratch',1);t.cats[0].baby=true;t.update();assert.equal(t.v.active.size,0);t.cats[0].baby=false;t.update();t.arrive();assert.equal(t.cats[0].p.mobel,8)}
console.log('PASS kittens: stay with their parent; furniture becomes available after growth');

{
 const t=setup('window',2);t.update();assert.equal(t.v.active.size,1);
 const c=t.cats.find(c=>t.v.owns(c)),v=t.v.active.get(c.id);
 c.location={...v.seat,y:0};t.update();assert.equal(v.phase,'walk');
 t.arrive();assert.equal(c.p.mobel,11);assert.equal(c.location.y,1);
 for(let i=0;i<7;i++)t.update();assert.equal(c.p.mobel,11);
 t.update();assert.equal(c.p.mobel,12);
 t.cats.length=1;t.cats[0]=c;
 for(let i=0;i<12;i++)t.update();assert.equal(c.p.mobel,0);assert.equal(t.v.active.size,0);
}
for(const reason of ['hungrig','sadel','vagn','leker','sit','damage','remove','rotate','away','reload']){
 const t=setup('window',1);t.update();t.arrive();for(let i=0;i<8;i++)t.update();
 assert.equal(t.cats[0].p.mobel,12);
 if(reason==='sit')t.cats[0].p.mobel=-1;
 else if(reason==='damage')t.v.interrupt(t.cats[0],220);
 else if(reason==='remove')t.d.block='minecraft:air';
 else if(reason==='rotate')t.d.facing='east';
 else if(reason==='away')t.players.length=0;
 else if(reason==='reload'){t.v.active.clear();t.v.cooldown.clear();}
 else t.cats[0].p[reason]=1;
 t.update();assert.equal(t.v.active.size,0,reason);
 assert.equal(t.cats[0].p.mobel,reason==='sit'?-1:0,reason);
}
console.log('PASS window perch: climb before posing, one place, watch then sleep, timeout and all sleep interruptions');

// Real native TV stop from the server regression: 0.552 blocks from the seat.
for(const facing of ['north','east','south','west']){
 const t=setup('tv',1);t.d.facing=facing;t.update();
 const c=t.cats[0],v=t.v.active.get(c.id),a={north:0,east:90,south:180,west:-90}[facing]*Math.PI/180;
 const dx=.49053955078125,dz=.25346736907959;
 c.location={x:v.seat.x+dx*Math.cos(a)-dz*Math.sin(a),y:v.seat.y,z:v.seat.z+dx*Math.sin(a)+dz*Math.cos(a)};
 let impulse;c.clearVelocity=()=>{};c.applyImpulse=x=>{impulse=x};
 t.update();assert.equal(v.phase,'align');assert.notEqual(c.p.mobel,7);
 assert.ok(Math.hypot(impulse.x,impulse.z)<=.06);assert.equal(impulse.y,0);
 t.arrive();assert.equal(c.p.mobel,7);
}
{const t=setup('tv',1);t.update();const c=t.cats[0],v=t.v.active.get(c.id);c.location={...v.seat,y:.4};t.update();assert.equal(v.phase,'walk')}
console.log('PASS TV native arrival edge: align to the viewing seat in four directions; no posing above floor');

// Native basket stop reproduced with a partner already occupying the near seat.
for(const facing of ['north','east','south','west']){
 const t=setup();t.d.facing=facing;t.update();
 const c=t.cats[0],v=t.v.active.get(c.id),mate=t.cats[1],mv=t.v.active.get(mate.id);
 mate.location={...mv.seat};
 const a={north:0,east:90,south:180,west:-90}[facing]*Math.PI/180;
 c.location={x:v.seat.x+.700365028381348*Math.cos(a),y:v.seat.y,z:v.seat.z+.700365028381348*Math.sin(a)};
 c.clearVelocity=()=>{};let impulse;c.applyImpulse=x=>{impulse=x};
 t.update();assert.equal(v.phase,'align');assert.notEqual(c.p.mobel,5);assert.notEqual(mate.p.mobel,5);
 assert.ok(Math.hypot(impulse.x,impulse.z)<=.06);assert.equal(impulse.y,0);
 t.update();assert.equal(t.v.active.size,2);
 t.arrive();assert.equal(c.p.mobel,5);assert.equal(mate.p.mobel,5);
}
console.log('PASS shared basket native edge: both visitors settle after the final bounded step');

for(const kind of ['spa','tv']){const t=setup(kind,1);t.update();const c=t.cats[0],a=t.v.active.get(c.id);c.location={...a.seat,y:1};t.update();assert.notEqual(c.p.mobel,kind==='spa'?6:7,'never rest atop furniture');}
{const a=furnitureSeat({x:0,y:0,z:0},'spa');assert.deepEqual(a,{x:.5,y:1/16,z:.5});}

// Soft plants do not obstruct paws; solid blocks and liquids still do.
for(const plant of ['minecraft:short_grass','minecraft:tallgrass','minecraft:dandelion','minecraft:poppy']){
 const t=setup('scratch',1),original=t.d.getBlock.bind(t.d),seat=furnitureSeat({x:0,y:0,z:0},'scratch');
 t.d.getBlock=q=>Math.floor(q.x)===Math.floor(seat.x)&&Math.floor(q.y)===0&&Math.floor(q.z)===Math.floor(seat.z)?{typeId:plant,isAir:false,isLiquid:false}:original(q);
 t.update();assert.equal(t.v.active.size,1,'scratch must allow '+plant);t.arrive();t.update();assert.equal(t.cats[0].p.mobel,8);
}
for(const obstruction of ['minecraft:stone','minecraft:oak_fence','minecraft:water','minecraft:lava','minecraft:sweet_berry_bush']){
 const t=setup('scratch',1),original=t.d.getBlock.bind(t.d),seat=furnitureSeat({x:0,y:0,z:0},'scratch');
 t.d.getBlock=q=>Math.floor(q.x)===Math.floor(seat.x)&&Math.floor(q.y)===0&&Math.floor(q.z)===Math.floor(seat.z)?{typeId:obstruction,isAir:false,isLiquid:['minecraft:water','minecraft:lava'].includes(obstruction)}:original(q);
 t.update();assert.equal(t.v.active.size,0,'unsafe or solid seat '+obstruction);
}
console.log('PASS scratching: soft vegetation allowed, solid/liquid/harmful obstructions rejected');

for(const facing of ['north','east','south','west']){
 const t=setup('spa',1);t.d.facing=facing;t.update();t.arrive();
 for(let i=0;i<8;i++)t.update();
 const v=t.v.active.get('0');assert.equal(v.phase,'exit');
 assert.ok(t.cats[0].events.includes('mjau:mobel_spa_exit_'+facing));
 t.cats[0].location={...v.exitSeat};t.update();assert.equal(t.v.active.size,0);
 for(let i=0;i<15;i++)t.update();assert.equal(t.v.active.size,0);
}
{const t=setup('spa',1);t.update();t.arrive();for(let i=0;i<8;i++)t.update();t.cats[0].p.hungrig=1;t.update();assert.equal(t.v.active.size,0)}
{const t=setup('spa',1);t.update();t.arrive();for(let i=0;i<19;i++)t.update();assert.equal(t.v.active.size,0)}
{const t=setup('fountain',1);t.update();t.arrive();assert.equal(t.cats[0].p.mobel,14);for(let i=0;i<6;i++)t.update();assert.equal(t.v.active.size,0)}
console.log('PASS water: four-direction spa exit, cooldown, exit interruption/timeout and bounded drinking');

{const t=setup('spa',1);t.update();t.arrive();const get=t.d.getBlock.bind(t.d);
 t.d.getBlock=p=>p.z===-1&&p.y===0?{typeId:'minecraft:stone',isAir:false,isLiquid:false}:get(p);
 for(let i=0;i<8;i++)t.update();const v=t.v.active.get('0');assert.equal(v.phase,'exit');assert.ok(v.exitSeat.x>1);
}
{const t=setup('spa',1);t.update();t.arrive();const get=t.d.getBlock.bind(t.d);
 t.d.getBlock=p=>p.y===0&&!(p.x===0&&p.z===0)?{typeId:'minecraft:stone',isAir:false,isLiquid:false}:get(p);
 for(let i=0;i<8;i++)t.update();assert.equal(t.v.active.size,0);assert.equal(t.cats[0].p.mobel,0);
}
console.log('PASS spa: alternate clear exit and cancellation when all exits blocked');
