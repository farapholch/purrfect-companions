"""North village activities, authored as world content rather than add-on runtime."""
G,F=-61,-60
TEXT={
'public':{
 'cafe':'CAT CAFE\nCook and picnic\nTreat your cats\nSupplies inside',
 'depot':'CART DEPOT\nEquip your cat\nFollow the loop\nReturn here',
 'pond':'FISHING GROVE\nRods in chest\nFish from pier\nPlant a tree',
 'way':'NEW NORTH WING\nCafe and carts\nFishing grove\nFollow gravel',
 'pages':['MORE TO DO - THE CAT CAFE\n\nFollow the gravel north of the house, then west to the cafe. Cook your catch in the smoker, craft cat treats and picnic at the tables. The chest holds sugar, wheat, cod and coal. The treats are for cats; cooked fish is for you.',
 'MORE TO DO - CART RIDES\n\nThe depot beside the cafe holds three cart colours. Tame a grown cat, equip a cart and use it to ride the broad gravel loop around the new north wing. The harness comes with the cart.\n\nThe loop is a practice route, with no timer or locked reward.',
 'MORE TO DO - THE FISHING GROVE\n\nThe little pond east of the depot has an open fishing pier. Take a rod from the chest and cast into the water. The bank steps let you climb out.\n\nSaplings and bone meal let you plant more trees in the grass around the pond. Apples and bread are picnic supplies.']},
'private':{
 'cafe':'KATTKAFE\nLaga och fika\nGodis till katt\nMat i kistan',
 'depot':'VAGNDEPAN\nUtrusta katten\nFolj slingan\nKom tillbaka',
 'pond':'FISKELUNDEN\nSpon i kistan\nFiska vid brygg\nPlantera trad',
 'way':'NYTT I NORR\nKafe och vagnar\nFiskelund\nFolj gruset',
 'pages':['MER ATT GÖRA - KATTKAFÉET\n\nFölj grusvägen norr om huset och sedan västerut till kaféet. Tillaga fångsten i rökugnen, gör kattgodis och fika vid borden. Kistan innehåller socker, vete, torsk och kol. Godiset är till katterna; tillagad fisk är till dig.',
 'MER ATT GÖRA - VAGNTURER\n\nDepån vid kaféet har vagnar i tre färger. Tämj en vuxen katt, utrusta den med vagn och kör den breda grusslingan runt den nya norra delen. Selen följer med vagnen.\n\nSlingan är en övningsväg utan tidtagning eller låst belöning.',
 'MER ATT GÖRA - FISKELUNDEN\n\nDen lilla dammen öster om depån har en öppen fiskebrygga. Ta ett spö ur kistan och kasta ut i vattnet. Strandens trappsteg hjälper dig upp om du ramlar i.\n\nPlantor och benmjöl låter dig plantera fler träd i gräset runt dammen. Äpplen och bröd är picknickproviant.']}}

def structures(b,outdir,variant):
 from pathlib import Path
 base=Path(outdir)/'structures/haven';base.mkdir(parents=True,exist_ok=True)
 for name in ['cafe','depot','pond','way']:
  s=b.Struct(1,1,1);s.set(0,0,0,'minecraft:standing_sign',{'ground_sign_direction':0});s.entity_at(0,0,0,b.sign_entity(TEXT[variant][name]));s.emit(str(base/f'new_{name}.mcstructure'))
 stocks={'cafe':[('minecraft:sugar',24),('minecraft:wheat',24),('minecraft:cod',24),('minecraft:coal',16),('mjau:godis',8)],'depot':[('mjau:vagn_tra',1),('mjau:vagn_rod',1),('mjau:vagn_bla',1),('minecraft:cod',24)],'pond':[('minecraft:fishing_rod',1),('minecraft:fishing_rod',1),('minecraft:oak_sapling',8),('minecraft:bone_meal',24),('minecraft:apple',8),('minecraft:bread',8)]}
 for name,items in stocks.items():
  s=b.Struct(1,1,1);s.set(0,0,0,'minecraft:chest',{'facing_direction':3});s.entity_at(0,0,0,b.chest_entity([b.item(i,n,count) for i,(n,count) in enumerate(items)]));s.emit(str(base/f'new_{name}_chest.mcstructure'))

def commands():
 c=[]
 def fill(x,y,z,xx,yy,zz,b):c.append(f'fill {x} {y} {z} {xx} {yy} {zz} {b}')
 def put(x,y,z,b):c.append(f'setblock {x} {y} {z} {b}')
 def load(n,x,y,z):c.append(f'structure load haven:new_{n} {x} {y} {z}')
 fill(-34,F,-20,24,F+5,-18,'air')
 # Broad loop leaves the existing kitchen garden and trade post in its centre.
 for x,z,xx,zz in [(-34,-20,24,-18),(-34,-4,24,-2),(-34,-17,-32,-5),(22,-17,24,-5),(4,-1,6,3)]:
  fill(x,G,z,xx,G,zz,'gravel')
 # Clear only new activity plots, leaving the old garden untouched.
 fill(-30,F,-16,-9,F+5,-6,'air')
 fill(-30,G,-16,-20,G,-6,'spruce_planks')
 for x,z in [(-30,-16),(-20,-16),(-30,-6),(-20,-6)]:fill(x,F,z,x,F+3,z,'oak_log')
 fill(-30,F+4,-16,-20,F+4,-6,'oak_slab')
 for x in [-28,-22]:put(x,F+3,-11,'lantern ["hanging"=true]')
 put(-28,F,-14,'smoker');put(-27,F,-14,'crafting_table');load('cafe_chest',-25,F,-14)
 for x in [-28,-23]:
  fill(x,F,-10,x+1,F,-10,'oak_slab');fill(x,F,-8,x+1,F,-8,'oak_slab')
  fill(x,F,-9,x+1,F,-9,'oak_planks')
 load('cafe',-20,F,-5)
 # Cart shed has full-height entrance and three clear blocks to the loop.
 fill(-17,G,-16,-10,G,-7,'spruce_planks')
 for x,z in [(-17,-16),(-10,-16),(-17,-7),(-10,-7)]:fill(x,F,z,x,F+3,z,'oak_log')
 fill(-17,F+4,-16,-10,F+4,-7,'oak_slab');put(-13,F+3,-13,'lantern ["hanging"=true]')
 load('depot_chest',-14,F,-14);load('depot',-11,F,-5)
 # Two-deep pool stays above bedrock, with a shallow step all around.
 fill(11,G-2,-15,19,G,-7,'clay');fill(12,G,-14,18,G,-8,'water');fill(13,G-1,-13,17,G-1,-9,'water')
 fill(14,G,-7,16,G,-6,'spruce_planks');fill(14,G,-10,16,G,-8,'spruce_planks')
 load('pond_chest',19,F,-6);load('pond',18,F,-5)
 for x,z in [(10,-16),(20,-16)]:
  fill(x,F,z,x,F+3,z,'oak_log');fill(x-1,F+3,z-1,x+1,F+4,z+1,'oak_leaves');put(x,F+3,z,'oak_log')
 for x,z in [(-31,-17),(-8,-17),(9,-17),(21,-17),(-31,-5),(9,-5),(21,-5)]:
  put(x,F,z,'oak_fence');put(x,F+1,z,'lantern')
 load('way',3,F,1)
 for x,y,z,b in CHECKS[:8]:c.append(f'testforblock {x} {y} {z} {b}')
 # Bedrock console drains ~20 commands/s; avoid swallowing subsequent chunk waits.
 paced=[]
 for i,cmd in enumerate(c):
  paced.append(cmd)
  if i%12==11:paced.append(('sleep',1))
 paced.append(('sleep',3));return paced

CHECKS=[(-28,F,-14,'smoker'),(-27,F,-14,'crafting_table'),(-25,F,-14,'chest'),(-14,F,-14,'chest'),(19,F,-6,'chest'),(13,G-1,-12,'water'),(12,G,-12,'water'),(15,G,-9,'spruce_planks')]
for x,z in [(x,-3) for x in range(-33,24)]+[(x,-19) for x in range(-33,24)]+[(-33,z) for z in range(-18,-3)]+[(23,z) for z in range(-18,-3)]+[(5,z) for z in range(-2,4)]+[(-26,z) for z in range(-7,-3)]+[(-13,z) for z in range(-12,-3)]+[(15,z) for z in range(-9,-3)]:
 CHECKS.extend([(x,F,z,'air'),(x,F+1,z,'air')])
