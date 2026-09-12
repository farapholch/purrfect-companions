"""New public activities must preserve old interaction points and cart clearance."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import render_world as r

class HavenExpansion(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.v=r.build_voxels()
 def block(self,x,y,z):return self.v.get((x,y,z),'air').replace('minecraft:','')
 def test_entire_three_wide_cart_loop_is_clear(self):
  for xa,za,xb,zb in [(-34,-20,24,-18),(-34,-4,24,-2),(-34,-17,-32,-5),(22,-17,24,-5)]:
   for x in range(xa,xb+1):
    for z in range(za,zb+1):
     self.assertEqual(self.block(x,-61,z),'gravel')
     for y in range(-60,-57):self.assertEqual(self.block(x,y,z),'air',(x,y,z))
 def test_existing_trade_post_welcome_and_garden_survive(self):
  for x,y,z,b in [(10,-60,-11,'barrel'),(1,-60,1,'standing_sign'),(-3,-60,-13,'wheat'),(-15,-60,11,'mjau:kattspa')]:
   self.assertEqual(self.block(x,y,z),b)
 def test_pond_has_shallow_exit_and_clear_pier(self):
  self.assertEqual(self.block(13,-62,-12),'water')
  self.assertEqual(self.block(12,-62,-12),'clay')
  self.assertEqual(self.block(12,-61,-12),'water')
  for z in range(-10,-5):
   for x in range(14,17):
    self.assertEqual(self.block(x,-61,z),'spruce_planks')
    for y in [-60,-59]:self.assertEqual(self.block(x,y,z),'air')
if __name__=='__main__':unittest.main()
