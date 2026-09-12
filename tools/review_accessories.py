#!/usr/bin/env python3
"""Render every accessory independently, in rest and pose, for visual review."""
import argparse
import html
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import build_accessories as accessories
import render_regression as renderer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("/tmp/purrfect-accessory-review"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    tiles = []
    entries = []
    for name, cfg in accessories.ACC.items():
        variant = min(cfg["colors"])
        frames = []
        for index, pose in enumerate(({}, renderer.POSE)):
            pixels = renderer.render("misty", [f"{name}{variant}"], pose, W=240, H=240)
            frames.append(pixels)
        tile = [left + right for left, right in zip(*frames)]
        renderer.write_png(str(args.output / f"{name}.png"), 480, 240, tile)
        tiles.append(tile)
        entries.append(f'<figure><img src="{name}.png" width="480" height="240"><figcaption>'
                       f'{html.escape(name)} / {html.escape(cfg["label"])} - rest | pose</figcaption></figure>')
        print(name, flush=True)
    for start in range(0, len(tiles), 8):
        page = [[(20, 22, 28, 255)] * 960 for _ in range(960)]
        for index, tile in enumerate(tiles[start:start + 8]):
            x, y = (index % 2) * 480, (index // 2) * 240
            for row, pixels in enumerate(tile):
                page[y + row][x:x + 480] = pixels
        path = args.output / f"overview-{start // 8 + 1}.png"
        renderer.write_png(str(path), 960, 960, page)
        print(path, flush=True)
    (args.output / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Accessory Review</title>'
        '<style>body{background:#14161c;color:white;font:16px sans-serif;display:flex;flex-wrap:wrap}'
        'figure{margin:12px}img{max-width:100%;height:auto}</style>' + ''.join(entries), encoding="utf-8")


if __name__ == "__main__":
    main()
