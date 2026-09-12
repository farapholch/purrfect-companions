"""Prevent intersections in supported outfit combinations and validate the audit."""
import sys,unittest
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'tools'))
import review_outfit_combinations as q

class OutfitCombinations(unittest.TestCase):
    def test_reviewed_combinations_clear_in_all_four_poses(self):
        for name,scene in q.SCENES.items():
            with self.subTest(combination=name):
                self.assertEqual(q.audit(scene),{})

    def test_cart_stays_on_ground_in_sit_and_sleep(self):
        count=len(next(b for b in q.r.GEO['geometry.katt.vagn1']['bones'] if b['name']=='cart')['cubes'])
        rest=q.boxes('vagn1',{}, {})[:count]
        for pose,positions in q.poses().values():
            self.assertEqual(q.boxes('vagn1',pose,positions)[:count],rest)

    def test_harness_follows_body_when_cat_lowers_itself(self):
        rest=q.boxes('vagn1',{}, {})[-11:]
        for name,drop in [('sit',1.2),('sleep',2.2)]:
            moved=q.boxes('vagn1',{},q.poses()[name][1])[-11:]
            for a,b in zip(rest,moved):
                self.assertAlmostEqual(a[0][1]-b[0][1],drop)

    def test_intersection_check_detects_overlap_but_allows_contact(self):
        axes=[(1,0,0),(0,1,0),(0,0,1)]
        box=([0,0,0],axes,[1,1,1])
        self.assertTrue(q.intersects(box,([1.9,0,0],axes,[1,1,1])))
        self.assertFalse(q.intersects(box,([2,0,0],axes,[1,1,1])))
        turned=[q.r.rot(v,(0,0,0),(0,45,0)) for v in axes]
        self.assertTrue(q.intersects(box,([2,0,0],turned,[1,1,1])))
        self.assertFalse(q.intersects(box,([3,0,0],turned,[1,1,1])))

    def test_pose_positions_come_from_sit_and_sleep_animation(self):
        poses=q.poses()
        self.assertEqual(poses['sit'][1]['body'],[0,-1.2,0])
        self.assertEqual(poses['sleep'][1]['body'],[0,-2.2,0])
        rest=q.boxes('mantel1',{},{});sleep=q.boxes('mantel1',*poses['sleep'])
        self.assertAlmostEqual(rest[0][0][1]-sleep[0][0][1],2.2)

if __name__=='__main__':unittest.main()
