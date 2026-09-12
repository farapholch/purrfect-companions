"""Check packing isolation and attachment pivots for every accessory color."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build_accessories as b
import render_regression as r

class AccessoryLayout(unittest.TestCase):
    def test_tiles_do_not_overlap(self):
        occupied={}
        for name,cfg in b.ACC.items():
            for variant,(u,v) in cfg['uv'].items():
                unique={(tuple(size),tuple(offset)) for _,size,offset in cfg['cubes']}
                for size,(du,dv) in unique:
                    w,h=b.uv_footprint(size)
                    for y in range(v+dv,v+dv+h):
                        for x in range(u+du,u+du+w):
                            self.assertTrue(0 <= x < b.TEX and 0 <= y < b.TEX)
                            self.assertNotIn((x,y),occupied,f'{name}{variant} overlaps {occupied.get((x,y))}')
                            occupied[x,y]=(name,variant)

    def test_generated_uvs_and_pivots(self):
        base={bone['name']:bone['pivot'] for bone in r.GEO['geometry.katt']['bones']}
        base['cart'] = [0, 0, 0]
        for name,cfg in b.ACC.items():
            for variant,(u,v) in cfg['uv'].items():
                bones=r.GEO[f'geometry.katt.{name}{variant}']['bones']
                expected = [f'leg{i}' for i in range(4)] if name == 'tossor' else ['cart','body'] if name == 'vagn' else [cfg['bone']]
                self.assertEqual([bone['name'] for bone in bones],expected)
                for bone in bones:
                    self.assertEqual(bone['pivot'],base[bone['name']])
                cubes=[cube for bone in bones for cube in bone['cubes']]
                self.assertEqual(len(cubes),len(cfg['cubes']))
                for actual,(origin,size,(du,dv)) in zip(cubes,cfg['cubes']):
                    self.assertEqual(actual['uv'],[u+du,v+dv])
                    self.assertEqual(actual['origin'],list(origin))
                    self.assertEqual(actual['size'],list(size))

if __name__=='__main__': unittest.main()
