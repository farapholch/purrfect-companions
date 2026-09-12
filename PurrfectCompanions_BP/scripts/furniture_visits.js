// Short, cancellable furniture visits. Native move_to_block does the walking;
// the script only reserves places, recognises arrival and controls the rest pose.
const TYPES = { basket: 'mjau:sovkorg', spa: 'mjau:kattspa', tv: 'mjau:katt_tv', scratch: 'mjau:klosbrada', window: 'mjau:fonsterbadd', fountain: 'mjau:kattfontan' };
export const prop = (c, key, fallback = 0) => {
  try { return c.getProperty('mjau:' + key) ?? fallback; } catch { return fallback; }
};
const distance = (a,b) => Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
// Only harmless, collision-free vegetation; fences, liquids and damaging plants remain blocked.
const SOFT_PLANTS = new Set(['short_grass','tallgrass','tall_grass','fern','large_fern','dandelion','yellow_flower','poppy','red_flower','blue_orchid','allium','azure_bluet','red_tulip','orange_tulip','white_tulip','pink_tulip','oxeye_daisy','cornflower','lily_of_the_valley','sunflower','lilac','rose_bush','peony'].map(id=>'minecraft:'+id));
const clearSpace = block => !!block && !block.isLiquid && (block.isAir || SOFT_PLANTS.has(block.typeId));
const YAWS={north:0,east:90,south:180,west:-90};
export function furnitureFacing(block) {
  try { const direction=block?.permutation?.getState('minecraft:cardinal_direction');
    // Bedrock defaults this trait to south. Preserve the old north-facing model
    // in existing worlds; the placement state records the player's direction.
    return ({south:'north',west:'east',north:'south',east:'west'})[direction] ?? 'north'; } catch { return 'north'; }
}
export function furnitureSeat(block, kind, slot = 0, facing = 'north') {
  const x=kind==='basket'?(slot?.46:-.46):0;
  const z=kind==='basket'?0:kind==='spa'?0:kind==='spa_exit'?-1.4:kind==='fountain'?-1.1:kind==='scratch'?-.95:kind==='window'?-.25:-1.3;
  const angle=YAWS[facing]*Math.PI/180;
  return {x:block.x+.5+x*Math.cos(angle)-z*Math.sin(angle),
    y:block.y+(kind==='basket'?3/16:kind==='spa'?1/16:kind==='window'?1:0),
    z:block.z+.5+x*Math.sin(angle)+z*Math.cos(angle)};
}
export class FurnitureVisits {
  constructor() { this.active = new Map(); this.cooldown = new Map(); this.stations = []; this.nextScan = 0; this.night = false; }
  owns(c) { return this.active.has(c.id); }
  eligible(c) {
    try {
      return !c.getComponent('minecraft:is_baby') && prop(c,'tam') === 1 && prop(c,'humor',1) > 0 &&
        !prop(c,'hungrig') && !prop(c,'sadel') && !prop(c,'vagn') && !prop(c,'leker') &&
        prop(c,'mobel') >= 0 && !c.target;
    } catch { return false; }
  }
  release(id, tick, partner = true) {
    const visit = this.active.get(id); if (!visit) return;
    this.active.delete(id); this.cooldown.set(id, tick + 400);
    try {
      const sitting=prop(visit.cat,'mobel')===-1;
      visit.cat.triggerEvent('mjau:mobel_av');
      if(sitting)visit.cat.triggerEvent('mjau:mobel_sitt');
      if (!prop(visit.cat,'sadel') && !prop(visit.cat,'vagn'))
        visit.cat.triggerEvent(this.night ? 'mjau:sovdags_pa' : 'mjau:sovdags_av');
    } catch { }
    if (partner && visit.partner) this.release(visit.partner,tick,false);
  }
  interrupt(c,tick) { if(prop(c,'tam')!==1)return; this.release(c.id,tick); this.cooldown.set(c.id,tick+200); }
  present(d,visit) {
    try { return d.id === visit.dimension && d.getBlock(visit.block)?.typeId === TYPES[visit.kind] && furnitureFacing(d.getBlock(visit.block)) === visit.facing; }
    catch { return false; }
  }
  freeSeat(d,seat,kind) {
    try {
      const feet=d.getBlock({x:Math.floor(seat.x),y:Math.floor(seat.y),z:Math.floor(seat.z)});
      const head=d.getBlock({x:Math.floor(seat.x),y:Math.floor(seat.y)+1,z:Math.floor(seat.z)});
      const floor=d.getBlock({x:Math.floor(seat.x),y:Math.floor(seat.y)-1,z:Math.floor(seat.z)});
      return clearSpace(head) && (kind === 'basket' ? feet?.typeId === TYPES.basket : kind==='spa' ? feet?.typeId===TYPES.spa : kind==='window' ? feet?.isAir && floor?.typeId===TYPES.window : clearSpace(feet) && floor && !floor.isAir && !floor.isLiquid);
    } catch { return false; }
  }
  reserve(c,station,slot,partner,tick,d) {
    const visit={cat:c,kind:station.kind,block:{...station.block},dimension:d.id,slot,partner,facing:station.facing,
      seat:furnitureSeat(station.block,station.kind,slot,station.facing),phase:'walk',until:tick+300};
    c.triggerEvent(`mjau:mobel_${station.kind === 'basket' ? 'basket'+slot : station.kind}_${station.facing}`);
    this.active.set(c.id,visit);
  }
  leaveSpa(d,visit,tick) {
    // Walk to a clear ground cell outside the basin before restoring ambient AI.
    for (const facing of [visit.facing,...Object.keys(YAWS).filter(f=>f!==visit.facing)]) {
      const seat=furnitureSeat(visit.block,'spa_exit',0,facing);
      if (!this.freeSeat(d,seat,'ground')) continue;
      visit.exitSeat=seat;visit.phase='exit';visit.until=tick+200;
      visit.cat.triggerEvent(`mjau:mobel_spa_exit_${facing}`);
      return true;
    }
    return false;
  }
  update(d,cats,players,tick,night) {
    this.night=night;
    const ids=new Set(cats.map(c=>c.id));
    players=players.filter(p=>p && p.dimension.id===d.id);
    for (const [id,visit] of [...this.active]) {
      if (this.active.get(id)!==visit) continue;
      const c=visit.cat;
      let near=false;
      try { near=players.some(p=>distance(p.location,c.location)<8); } catch { }
      if (!ids.has(id) || !this.eligible(c) || !near || !this.present(d,visit) ||
          !this.freeSeat(d,visit.seat,visit.kind)) { this.release(id,tick); continue; }
      if (tick>=visit.until) {
        if (!(visit.kind==='spa' && visit.phase==='rest' && this.leaveSpa(d,visit,tick))) {
          this.release(id,tick);continue;
        }
      }
      if (visit.phase==='exit') {
        if (!this.freeSeat(d,visit.exitSeat,'ground') || distance(c.location,visit.exitSeat)<.25)
          this.release(id,tick);
        else if (distance(c.location,visit.exitSeat)<.8) {
          if (!visit.exitAlign) { c.triggerEvent('mjau:mobel_vantar');visit.exitAlign=true; }
          try {
            const dx=visit.exitSeat.x-c.location.x,dz=visit.exitSeat.z-c.location.z;
            const length=Math.hypot(dx,dz);
            c.clearVelocity();
            if(length>.001)c.applyImpulse({x:dx/length*.06,y:0,z:dz/length*.06});
          } catch { }
        }
        continue;
      }
      if (visit.phase==='walk') {
        const onSurface=!['basket','spa','scratch','window','tv','fountain'].includes(visit.kind) || Math.abs(c.location.y-visit.seat.y)<.12;
        if (onSurface && distance(c.location,visit.seat)<=(visit.kind==='basket'?.8:visit.kind==='tv'?.65:.55)) {
          c.triggerEvent('mjau:mobel_vantar');
          try { c.clearVelocity(); } catch { }
          visit.phase=['basket','spa','scratch','window','tv','fountain'].includes(visit.kind)?'align':'ready';visit.until=tick+240;
        }
      } else if (distance(c.location,visit.seat)>(visit.kind==='basket'&&visit.phase==='align'?.85:.75)) { this.release(id,tick); continue; }
      if (visit.phase==='align') {
        const dx=visit.seat.x-c.location.x,dz=visit.seat.z-c.location.z;
        const horizontal=Math.hypot(dx,dz);
        if(horizontal<=.05 && Math.abs(visit.seat.y-c.location.y)<.12) {
          try { c.clearVelocity(); } catch { }
          visit.phase='ready';visit.until=tick+240;
        } else {
          // Native pathfinding reaches the furniture; gentle physical steps align
          // the final few pixels without teleporting or freezing overlapping cats.
          try {
            c.clearVelocity();
            const strength=Math.min(.06,horizontal*.2);
            if(horizontal>.001)c.applyImpulse({x:dx/horizontal*strength,y:0,z:dz/horizontal*strength});
          } catch { }
        }
      }
      if (visit.phase==='ready' && (!visit.partner || ['ready','rest'].includes(this.active.get(visit.partner)?.phase))) {
        const mate=visit.partner && this.active.get(visit.partner);
        if (visit.partner && !mate) { this.release(id,tick); continue; }
        // Both cats must reach their reserved places before either falls asleep.
        const visitors=mate && mate.phase==='ready' ? [visit,mate] : [visit];
        for (const v of visitors) {
          v.cat.triggerEvent(`mjau:mobel_vila_${v.kind}`);
          v.phase='rest';v.nextEffect=tick;v.until=tick+(v.kind==='basket'?600:v.kind==='window'?400:v.kind==='fountain'?120:160);
          if(v.kind==='window')v.sleepAt=tick+160;
        }
      }
      if (visit.phase==='rest') {
        if(visit.kind==='window' && tick>=visit.sleepAt){
          c.triggerEvent('mjau:mobel_vila_window_sleep');visit.sleepAt=Infinity;
        }
        if (visit.kind==='scratch' && tick>=visit.nextEffect) {
          visit.nextEffect=tick+20;
          const a=YAWS[visit.facing]*Math.PI/180;
          const dust={x:visit.block.x+.5+.34*Math.sin(a),y:visit.block.y+.18,
            z:visit.block.z+.5-.34*Math.cos(a)};
          try { d.spawnParticle('mjau:sisal_dust',dust); } catch { }
          try { d.playSound('step.wood',dust,{volume:.22,pitch:1.6}); } catch { }
        }
        try {
          // Rotate the cat toward its furniture's front in place;
          // never teleports it through a wall or across the world.
          c.setRotation({x:0,y:YAWS[visit.facing]+(visit.kind==='basket' ? (visit.slot? -12:12) : 0)});
        } catch { }
      }
    }
    // Persisted component groups can survive a world reload; reservations do not.
    for (const c of cats) if (prop(c,'mobel')>0 && !this.owns(c) && !(this.cooldown.get(c.id)>tick) && players.some(p=>distance(p.location,c.location)<8)) {
      try {
        c.triggerEvent('mjau:mobel_av');
        if(!prop(c,'sadel') && !prop(c,'vagn'))
          c.triggerEvent(this.night ? 'mjau:sovdags_pa' : 'mjau:sovdags_av');
      } catch { }
      this.cooldown.set(c.id,tick+100);
    }
    if (tick>=this.nextScan) {
      this.nextScan=tick+100;this.stations=[];const seen=new Set();
      for (const p of players) {
        const L=p.location;
        for(let x=Math.floor(L.x)-4;x<=Math.floor(L.x)+4;x++)
          for(let y=Math.floor(L.y)-1;y<=Math.floor(L.y)+1;y++)
            for(let z=Math.floor(L.z)-4;z<=Math.floor(L.z)+4;z++) {
              const key=`${x},${y},${z}`;if(seen.has(key))continue;seen.add(key);
              try { const block=d.getBlock({x,y,z});const type=block?.typeId;
                const kind=Object.keys(TYPES).find(k=>TYPES[k]===type);
                if(kind)this.stations.push({kind,block:{x,y,z},key,facing:furnitureFacing(block)});
              } catch { }
            }
      }
      for (const [id,until] of this.cooldown) if (until<=tick) this.cooldown.delete(id);
    }
    const candidates=cats.filter(c=>this.eligible(c)&&!this.owns(c)&&!(this.cooldown.get(c.id)>tick)).slice(0,24);
    for(const station of this.stations) {
      try { if(d.getBlock(station.block)?.typeId!==TYPES[station.kind] || furnitureFacing(d.getBlock(station.block))!==station.facing)continue; } catch { continue; }
      if([...this.active.values()].some(v=>v.dimension===d.id&&distance(v.block,station.block)<.1))continue;
      const pool=candidates.filter(c=>!this.owns(c)&&distance(c.location,station.block)<4 && players.some(p=>distance(p.location,c.location)<8))
        .filter(c=>this.stations.filter(s=>s.kind===station.kind).every(s=>distance(c.location,station.block)<=distance(c.location,s.block)))
        .sort((a,b)=>distance(a.location,station.block)-distance(b.location,station.block));
      const count=station.kind==='basket'?2:1;
      if(pool.length<count)continue;
      if(count===2)pool.sort((a,b)=>distance(a.location,furnitureSeat(station.block,'basket',0,station.facing))-distance(b.location,furnitureSeat(station.block,'basket',0,station.facing)));
      if(!Array.from({length:count},(_,slot)=>this.freeSeat(d,furnitureSeat(station.block,station.kind,slot,station.facing),station.kind)).every(Boolean))continue;
      try {
        for(let slot=0;slot<count;slot++)this.reserve(pool[slot],station,slot,count===2?pool[1-slot].id:null,tick,d);
      } catch { for(const c of pool.slice(0,count))this.release(c.id,tick); }
    }
  }
}
