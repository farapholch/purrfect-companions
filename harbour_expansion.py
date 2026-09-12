"""Generator-owned Star Harbour activity wing; vanilla activities and cat furniture."""
import build_world as bw
G,F=bw.GROUND,bw.FLOOR
TEXT={
 'public':{
 'lounge':'CAT LOUNGE\nSpa and TV\nTame, feed,\nthen relax',
 'garden':'MOON GARDEN\nHarvest crops\nReplant seeds\nShare the food',
 'course':'FLIGHT CADET\nJump the pads\nChest at end\nWater below',
 'west':'NEW WING\nCat lounge <-\nCadet course\nvia lounge',
 'south':'MOON GARDEN\nThis way south\nGrow supplies\nfor the crew',
 'pages':[
 'TASK 8 - THE CAT LOUNGE\n\nThe western door of the dome leads to the new lounge. Bring a grown, tamed, well-fed cat and stay nearby while it tries the spa, television or scratching boards.\n\nThe equipment chest holds a cart with harness, a backpack and treats. A crafting bench and anvil stand nearby.',
 'TASK 9 - THE MOON GARDEN\n\nFollow the green-lit path south from the corridor. Harvest wheat, carrots and potatoes, then replant. Water and lamps keep the beds growing in the eternal night.\n\nThe supply chest contains a hoe, seeds, sugar and cod. Use sugar, wheat and cod to craft cat treats at the workbench.',
 'TASK 10 - FLIGHT CADET\n\nTake the south exit from the lounge. Jump across the raised blue pads to the chest on the far platform.\n\nWater catches a missed jump. Swim to either side, step onto the walkway and return to the start. The chest contains a gold helmet and travel supplies.'],
 },
 'private':{
 'lounge':'KATTLOUNGEN\nSpa och TV\nTamj och mata\nsedan vila',
 'garden':'MANTRADGARDEN\nSkorda grodor\nPlantera igen\nDela pa maten',
 'course':'RYMDKADETT\nHoppa mellan\nKista vid mal\nVatten under',
 'west':'NY AVDELNING\nKattlounge <-\nHoppbana via\nloungen',
 'south':'MANTRADGARDEN\nSoderut har\nOdla proviant\ntill besattning',
 'pages':[
 'UPPDRAG 8 - KATTLOUNGEN\n\nKupolens västra dörr leder till den nya loungen. Ta med en vuxen, tämjd och mätt katt och stå nära när den provar spa, TV eller klösbrädor.\n\nUtrustningskistan innehåller vagn med sele, ryggsäck och godis. Här finns också arbetsbänk och städ.',
 'UPPDRAG 9 - MÅNTRÄDGÅRDEN\n\nFölj den gröna ljusgången söderut från korridoren. Skörda vete, morötter och potatis och plantera sedan igen. Vatten och lampor håller odlingen igång i den eviga natten.\n\nFörrådskistan innehåller hacka, frön, socker och torsk. Gör kattgodis av socker, vete och torsk vid arbetsbänken.',
 'UPPDRAG 10 - RYMDKADETT\n\nTa loungens södra utgång. Hoppa över de blå plattformarna till kistan på sista avsatsen.\n\nVatten fångar dig om du missar. Simma åt sidan, kliv upp på gångvägen och gå tillbaka till starten. Kistan innehåller en guldhjälm och reseproviant.'],
 }}

def structures(outdir,variant):
 from pathlib import Path
 t=TEXT[variant];base=Path(outdir)/'structures/hamn';base.mkdir(parents=True,exist_ok=True)
 for name in ['lounge','garden','course','west','south']:
  s=bw.Struct(1,1,1);s.set(0,0,0,'minecraft:standing_sign',{'ground_sign_direction':0})
  s.entity_at(0,0,0,bw.sign_entity(t[name]));s.emit(str(base/f'new_{name}.mcstructure'))
 stock={
 'lounge':[('mjau:vagn_bla',1),('mjau:ryggsack_brun',1),('mjau:godis',12),('minecraft:cod',24)],
 'garden':[('minecraft:iron_hoe',1),('minecraft:wheat_seeds',24),('minecraft:carrot',8),('minecraft:potato',8),('minecraft:sugar',24),('minecraft:cod',24),('minecraft:bone_meal',16),('minecraft:coal',16)],
 'course':[('minecraft:golden_helmet',1),('minecraft:golden_carrot',8),('minecraft:emerald',3)],
 }
 for name,items in stock.items():
  s=bw.Struct(1,1,1);s.set(0,0,0,'minecraft:chest',{'facing_direction':3})
  s.entity_at(0,0,0,bw.chest_entity([bw.item(i,n,count) for i,(n,count) in enumerate(items)]));s.emit(str(base/f'new_{name}_chest.mcstructure'))

def commands():
 c=[]
 def fill(x1,y1,z1,x2,y2,z2,b):c.append(f'fill {x1} {y1} {z1} {x2} {y2} {z2} {b}')
 def block(x,y,z,b):c.append(f'setblock {x} {y} {z} {b}')
 def load(name,x,y,z):c.append(f'structure load hamn:new_{name} {x} {y} {z}')
 # West wing: open corridor through the former dome wall, furnished around clear aisles.
 fill(-36,G,-10,-16,F+5,12,'quartz_block hollow')
 fill(-35,F+2,-10,-17,F+4,-10,'glass');fill(-36,F+2,-9,-36,F+4,11,'glass')
 fill(-35,F+5,-9,-17,F+5,11,'glass')
 fill(-16,G,-2,-12,F+3,2,'quartz_block hollow');fill(-16,F,-1,-12,F+2,1,'air')
 for x,z in [(-33,-7),(-19,-7),(-33,9),(-19,9)]:block(x,F+4,z,'sea_lantern')
 for x,z,b in [(-32,-5,'mjau:kattspa'),(-26,-5,'mjau:katt_tv'),(-20,-5,'mjau:klosbrada'),(-32,5,'mjau:klosbrada'),(-20,7,'crafting_table'),(-19,7,'anvil')]:block(x,F,z,b)
 load('lounge_chest',-22,F,7);load('lounge',-18,F,3);load('west',-10,F,3)
 # Greenhouse and a lit path from the main corridor, away from tower and hangar.
 fill(18,G,2,22,G,18,'lime_concrete');fill(19,F,2,21,F+2,18,'air')
 fill(14,G,18,28,F+5,32,'quartz_block hollow')
 fill(14,F+1,19,14,F+4,31,'glass');fill(28,F+1,19,28,F+4,31,'glass')
 fill(15,F+5,19,27,F+5,31,'glass');fill(19,F,18,21,F+2,18,'air')
 for z in [6,12,17]:block(18,G,z,'sea_lantern');block(22,G,z,'sea_lantern')
 for x in [16,24]:
  for z in [23,28]:
   block(x+1,F+4,z,'chain');block(x+1,F+3,z,'sea_lantern')
  fill(x,G,23,x+2,G,29,'farmland');block(x+1,G,26,'water')
  for dx in range(3):
   for z in range(23,30):
    if (dx,z)!=(1,26):block(x+dx,F,z,['wheat','carrots','potatoes'][dx]+' ["growth"=7]')
 block(25,F,20,'crafting_table');block(26,F,20,'furnace');load('garden_chest',23,F,20)
 load('garden',17,F,20);load('south',23,F,4)
 # Cadet course: short one-block gaps, maximum two-block rise, water catch basin.
 fill(-28,G,12,-24,G,20,'light_blue_concrete');fill(-27,F,12,-25,F+2,20,'air')
 fill(-32,G-1,19,-20,G-1,40,'quartz_block');fill(-32,G,19,-20,G,40,'quartz_block')
 fill(-30,G,21,-22,G,38,'water')
 fill(-28,F,19,-24,F,20,'light_blue_concrete')
 for z,h in [(22,0),(25,1),(28,1),(31,2)]:
  fill(-27,G,z,-25,F+h,z+1,'light_blue_concrete');block(-26,F+h,z,'sea_lantern')
 fill(-28,G,35,-24,F+2,38,'light_blue_concrete');load('course_chest',-26,F+3,37)
 load('course',-23,F,19)
 for z in [20,26,32,39]:block(-31,F,z,'sea_lantern');block(-21,F,z,'sea_lantern')
 c.append(('sleep',3))
 for x,y,z,b in CHECKS:c.append(f'testforblock {x} {y} {z} {b}')
 # Pace console commands so area-loading waits are not swallowed by a backlog.
 paced=[];pending=0
 for command in c:
  paced.append(command)
  if isinstance(command,tuple):pending=0
  else:
   pending+=1
   if pending==12:paced.append(('sleep',1));pending=0
 paced.append(('sleep',2))
 return paced

CHECKS=[(-32,F,-5,'mjau:kattspa'),(-26,F,-5,'mjau:katt_tv'),(-20,F,-5,'mjau:klosbrada'),(-22,F,7,'chest'),(-20,F,7,'crafting_table'),(-19,F,7,'anvil'),(16,F,23,'wheat'),(17,F,23,'carrots'),(18,F,23,'potatoes'),(17,G,26,'water'),(23,F,20,'chest'),(25,F,20,'crafting_table'),(26,F,20,'furnace'),(-29,G,24,'water'),(-26,F+3,37,'chest'),(-26,F+2,31,'sea_lantern')]
# Walk every doorway/path at feet and head height, not just landmark blocks.
for x,z in [(x,0) for x in range(-25,-10)]+[(20,z) for z in range(2,23)]+[(-26,z) for z in range(8,19)]+[(-32,z) for z in range(21,39)]:
 CHECKS.extend([(x,F,z,'air'),(x,F+1,z,'air')])
