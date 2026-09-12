"""Access and sustainable crops in the generated station, independent of landmark list."""
import sys,unittest
from pathlib import Path
from collections import deque
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import review_starharbour as review

class HarbourExpansion(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.v=review.voxels()
 def block(self,x,y,z):return self.v.get((x,y,z),'air').replace('minecraft:','')
 def test_walk_from_spawn_to_each_new_activity(self):
  f=review.s.F;queue=deque([(0,4)]);seen={(0,4)}
  def walk(x,z):
   return self.block(x,f-1,z) not in ['air','water'] and all(self.block(x,y,z) in ['air','standing_sign'] for y in [f,f+1])
  while queue:
   x,z=queue.popleft()
   for nx,nz in [(x-1,z),(x+1,z),(x,z-1),(x,z+1)]:
    if -40<=nx<=78 and -15<=nz<=44 and (nx,nz) not in seen and walk(nx,nz):seen.add((nx,nz));queue.append((nx,nz))
  for target in [(-26,0),(-22,6),(23,21),(-26,18),(-32,38)]:
   with self.subTest(target=target):self.assertIn(target,seen)
 def test_all_crop_cells_have_water_and_overhead_light(self):
  g,f=review.s.G,review.s.F
  crops=[(x,z) for (x,y,z),b in self.v.items() if y==f and b in ['wheat','carrots','potatoes']]
  self.assertEqual(len(crops),40)
  for x,z in crops:
   self.assertEqual(self.block(x,g,z),'farmland')
   self.assertTrue(any(self.block(x+dx,g,z+dz)=='water' for dx in range(-4,5) for dz in range(-4,5)))
   self.assertTrue(any(b=='sea_lantern' and abs(lx-x)+abs(lz-z)<=4 and ly==f+3 for (lx,ly,lz),b in self.v.items()))
 def test_jump_gaps_and_water_catch(self):
  f,g=review.s.F,review.s.G
  # Last occupied row/next landing row; no jump rises more than one block.
  for end,start,oldheight,newheight in [(20,22,f,f),(23,25,f,f+1),(26,28,f+1,f+1),(29,31,f+1,f+2),(32,35,f+2,f+2)]:
   self.assertLessEqual(start-end,3);self.assertLessEqual(newheight-oldheight,1)
   self.assertNotEqual(self.block(-26,oldheight,end),'air')
   self.assertNotEqual(self.block(-26,newheight,start),'air')
   for z in range(end+1,start):self.assertEqual(self.block(-26,g,z),'water')
if __name__=='__main__':unittest.main()
