"""Furniture action contracts: bounded coat edits, seamless loops and paw/muzzle proximity."""
import json,sys,unittest,math
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];sys.path[:0]=[str(BASE),str(BASE/'tools')]
import render_regression as r
from review_furniture_visits import sample
RP=BASE/'PurrfectCompanions_RP';A=json.loads((RP/'animations/katt.animation.json').read_text())['animations']
class Actions(unittest.TestCase):
 def test_spa_basin_and_thin_tv_collision(self):
  spa=json.loads((BASE/'PurrfectCompanions_BP/blocks/kattspa.json').read_text())['minecraft:block']['components']
  tv=json.loads((BASE/'PurrfectCompanions_BP/blocks/katt_tv.json').read_text())['minecraft:block']['components']
  self.assertEqual(spa['minecraft:collision_box']['size'],[16,1,16])
  self.assertEqual(spa['minecraft:selection_box']['size'],[16,9,16])
  self.assertEqual(tv['minecraft:collision_box'],{'origin':[-8,0,-3],'size':[16,13,6]})
 def test_managed_visits_are_not_ambient_targets(self):
  managed={'mjau:'+b for b in ('sovkorg','kattspa','katt_tv','klosbrada','fonsterbadd','kattfontan')}
  for path in (BASE/'PurrfectCompanions_BP/entities').glob('*.json'):
   e=json.loads(path.read_text())['minecraft:entity']
   ambient=e.get('component_groups',{}).get('mjau:fri',{}).get('minecraft:behavior.move_to_block',{})
   self.assertFalse(managed.intersection(ambient.get('target_blocks',[])),path)
 def test_large_cat_clears_fountain(self):
  e=json.loads((BASE/'PurrfectCompanions_BP/entities/snow.json').read_text())['minecraft:entity']
  radius=e['components']['minecraft:collision_box']['width']*e['component_groups']['mjau:adult']['minecraft:scale']['value']/2
  goal=e['component_groups']['mjau:mobel_fountain_north']['minecraft:behavior.move_to_block']
  self.assertGreater(-goal['target_offset'][2]-.5-radius,.1)
 def test_closed_eyes_only_change_eye_regions(self):
  import make_cat_pals as fur
  box=fur.ytor(fur.BEN['head'][0])['north'];x,y,w,h=box
  for cat in fur.katterna():
   aw,ah,awake=r.read_png(str(RP/f'textures/entity/{cat}_pals.png'))
   sw,sh,sleep=r.read_png(str(RP/f'textures/entity/{cat}_sleep.png'))
   self.assertEqual((aw,ah),(sw,sh));count=0
   for py in range(ah):
    for px in range(aw):
     if awake[py][px]!=sleep[py][px]:
      count+=1;self.assertTrue(x<=px<x+w and y<=py<y+h,(cat,px,py))
   self.assertGreater(count,20,cat)
 def test_seamless_bounded_actions(self):
  for name in ('korgvila','spa','tv','scratch','window','fountain'):
   action=A['animation.katt.'+name]
   for bone,channels in action['bones'].items():
    for channel,v in channels.items():
     self.assertEqual(sample(v,0),sample(v,action['animation_length']),(name,bone,channel))
     for t in range(41):
      self.assertTrue(all(math.isfinite(x) for x in sample(v,t/10)))
  settle=A['animation.katt.korglagg'];rest=A['animation.katt.korgvila']
  for bone,channels in settle['bones'].items():
   for channel,v in channels.items():self.assertEqual(sample(v,1.2),sample(rest['bones'][bone][channel],0))
 def test_navigation_outranks_ambient_looking(self):
  for path in (BASE/'PurrfectCompanions_BP/entities').glob('*.json'):
   entity=json.loads(path.read_text())['minecraft:entity']
   goals=[g['minecraft:behavior.move_to_block']['priority'] for name,g in entity.get('component_groups',{}).items()
     if name.startswith('mjau:mobel_') and 'minecraft:behavior.move_to_block' in g]
   if not goals:continue
   for name in ('look_at_player','random_look_around'):
    self.assertLess(max(goals),entity['components']['minecraft:behavior.'+name]['priority'])
 def test_scratching_has_alternating_paws_and_separate_navigation_mode(self):
  b=A['animation.katt.scratch']['bones']
  self.assertGreater(sample(b['leg2']['rotation'],.25)[0],sample(b['leg3']['rotation'],.25)[0])
  self.assertGreater(sample(b['leg3']['rotation'],.75)[0],sample(b['leg2']['rotation'],.75)[0])
  for path in (BASE/'PurrfectCompanions_BP/entities').glob('*.json'):
   e=json.loads(path.read_text())['minecraft:entity'];props=e['description'].get('properties',{})
   if 'mjau:mobel' not in props:continue
   self.assertLessEqual(len(props),32)
   for direction in ('north','east','south','west'):
    event=e['events']['mjau:mobel_scratch_'+direction]
    self.assertEqual(event['sequence'][0]['set_property']['mjau:mobel'],9)
   self.assertEqual(e['events']['mjau:mobel_vila_scratch']['set_property']['mjau:mobel'],8)
  board=json.loads((BASE/'PurrfectCompanions_BP/blocks/klosbrada.json').read_text())['minecraft:block']
  half=board['components']['minecraft:collision_box']['size'][0]/32
  snow=json.loads((BASE/'PurrfectCompanions_BP/entities/snow.json').read_text())['minecraft:entity']
  radius=snow['components']['minecraft:collision_box']['width']*snow['component_groups']['mjau:adult']['minecraft:scale']['value']/2
  offset=snow['component_groups']['mjau:mobel_scratch_north']['minecraft:behavior.move_to_block']['target_offset']
  self.assertGreater(-offset[2]-half-radius,.05) # clearance even at alignment tolerance
  fx=json.loads((RP/'particles/sisal_dust.json').read_text())['particle_effect']
  self.assertEqual(fx['description']['identifier'],'mjau:sisal_dust')
  self.assertLessEqual(fx['components']['minecraft:emitter_rate_instant']['num_particles'],3)
  self.assertLessEqual(fx['components']['minecraft:particle_lifetime_expression']['max_lifetime'],.5)
 def test_window_lowering_matches_watch_and_sleep(self):
  lower=A['animation.katt.windowlagg']['bones'];watch=A['animation.katt.window']['bones'];rest=A['animation.katt.korgvila']['bones']
  for bone,channels in lower.items():
   for channel,value in channels.items():
    self.assertEqual(sample(value,0),sample(watch.get(bone,{}).get(channel,[0,0,0]),0))
    self.assertEqual(sample(value,1.2),sample(rest[bone][channel],0))
  board=json.loads((BASE/'PurrfectCompanions_BP/blocks/fonsterbadd.json').read_text())['minecraft:block']
  self.assertEqual(board['components']['minecraft:collision_box']['size'][1],16)
  self.assertEqual(board['components']['minecraft:selection_box']['size'][1],16)
  for path in (BASE/'PurrfectCompanions_BP/entities').glob('*.json'):
   e=json.loads(path.read_text())['minecraft:entity'];props=e['description'].get('properties',{})
   if 'mjau:mobel' not in props:continue
   self.assertLessEqual(len(props),32)
   for facing in ('north','east','south','west'):
    g=e['component_groups']['mjau:mobel_window_'+facing]['minecraft:behavior.move_to_block']
    self.assertEqual(g['target_offset'][1],1)
    self.assertIn('jump',g['control_flags'])
 def test_washing_paw_reaches_muzzle(self):
  b=A['animation.katt.spa']['bones']
  head=r.rot((0,6.5,-9.5),(0,7,-5),sample(b['head']['rotation'],1.2))
  paw=r.rot((-2,0,-4),(-2,4,-4),sample(b['leg2']['rotation'],1.2))
  self.assertLess(math.dist(head,paw),2.2)
  self.assertLess(paw[2],-7);self.assertGreater(paw[1],4)
if __name__=='__main__':unittest.main()
