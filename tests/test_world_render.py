import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import render_world as world


class WorldRenderTests(unittest.TestCase):
    def test_topdown_includes_highest_and_deepest_blocks(self):
        for height in (-20, -70):
            with self.subTest(height=height), patch.object(world, "save") as save:
                world.render_topdown({(0, height, 0): "snow"}, {}, "unused.png",
                                     area=((0, 1), (0, 1)), scale=1)
                pixels = save.call_args.args[1]
                self.assertEqual(pixels[0][0], world.shade(world.VANILLA["snow"],
                                                         1 + (height + 60) * 0.02))

    def test_extended_ground_preserves_excavation(self):
        commands = ["setblock 101 -60 1 stone", "setblock 100 -61 1 air"]
        with patch.object(world.bw, "build_structures"), \
             patch.object(world.bw, "build_commands", return_value=commands), \
             patch.object(world.os.path, "exists", return_value=False):
            voxels = world.build_voxels()
        self.assertEqual(voxels[(101, -61, 1)], "minecraft:grass_block")
        self.assertNotIn((100, -61, 1), voxels)
        self.assertEqual(voxels[(100, -62, 1)], "minecraft:dirt")

    def test_namespaced_palette(self):
        self.assertEqual(world.color_of("minecraft:spruce_log", {}),
                         world.VANILLA["spruce_log"])


if __name__ == "__main__":
    unittest.main()
