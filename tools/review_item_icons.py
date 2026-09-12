#!/usr/bin/env python3
"""Show generated inventory textures at native size and crisp enlarged scale."""
import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from build_accessories import read_png, write_png

NAMES = ("kattbok", "godis", "vissla", "pokal", "garnboll")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="/tmp/purrfect-item-icons.png")
    args = parser.parse_args()
    width, height = 200 * len(NAMES), 232
    canvas = [[(28, 31, 38, 255)] * width for _ in range(height)]
    for index, name in enumerate(NAMES):
        w, h, pixels = read_png(str(BASE / f"PurrfectCompanions_RP/textures/items/pc_{name}.png"))
        assert w == h and w in (16, 32)
        for size, top in ((160, 16), (w, 194)):
            left = index * 200 + (200 - size) // 2
            for y in range(size):
                for x in range(size):
                    pixel = pixels[y * h // size][x * w // size]
                    if pixel[3]:
                        canvas[top + y][left + x] = pixel
    write_png(args.output, width, height, canvas)
    print(args.output)
    print("Left to right: " + ", ".join(NAMES))


if __name__ == "__main__":
    main()
