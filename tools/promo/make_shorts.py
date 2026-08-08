#!/usr/bin/env python3
"""Tre vertikala shorts (9:16, 1080x1920) för YouTube Shorts/TikTok.

Samma motor som trailern. Varje klipp ~15 s, loopbart, tyst med flit —
ljud läggs på i appen vid uppladdning (standard för formatet, och licensrent).

  1. unicorn  — enhörningskatten i gångcykel, kamerasvep
  2. cart     — katt med vagnen, "SIT IN THE CART"
  3. sleepy   — ihoprullad sovande katt, pulserande Zzz

Rutor 270x480 -> 1080x1920 med närmsta granne (pixellooken är estetiken).
"""
import math, multiprocessing, os, shutil, subprocess, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_regression as rr
from make_video import FONT

W, H, FPS = 270, 480, 30
DUR = 15 * FPS


def text(img, s, cx, y, scale, col=(235, 240, 250, 255)):
    w = len(s) * 6 * scale - scale
    x0 = cx - w // 2
    for i, ch in enumerate(s.upper()):
        for ry, row in enumerate(FONT.get(ch, FONT[" "])):
            for rx, c in enumerate(row):
                if c != "#": continue
                for dy in range(scale):
                    for dx in range(scale):
                        px, py = x0 + (i * 6 + rx) * scale + dx, y + ry * scale + dy
                        if 0 <= px < W and 0 <= py < H:
                            img[py][px] = col


def walk(t):
    a = math.cos(t * 9.0) * 38
    return {"leg0": (a, 0, 0), "leg3": (a, 0, 0), "leg1": (-a, 0, 0), "leg2": (-a, 0, 0),
            "head": (0, math.sin(t * 1.7) * 10, 0),
            "tail": (-18, 0, math.sin(t * 2.3) * 14)}


SLEEP = {"leg0": (88, 0, 0), "leg1": (88, 0, 0), "leg2": (-88, 0, 0), "leg3": (-88, 0, 0),
         "head": (24, 20, 0), "tail": (6, 0, -55)}

CYAN = (0, 212, 255, 255)
DIM = (150, 200, 255, 255)

def pose_sleepy(t):
    return {**SLEEP, "tail": (6, 0, -55 + math.sin(t * 1.2) * 6)}


# pose anges med NAMN — lambdas kan inte picklas till arbetarprocesserna
POSES = {"walk": walk, "sleepy": pose_sleepy}
SHORTS = {
    "unicorn": dict(cat="mocha", acc=["horn2", "vingar1"],
                    hook="UNICORN CAT?", sub="YES. IN MINECRAFT.",
                    pose="walk", orbit=1.6),
    "cart": dict(cat="hazel", acc=["vagn1", "tomteluva1"],
                 hook="YOUR CAT PULLS", sub="AND YOU SIT IN THE CART",
                 pose="walk", orbit=1.2),
    "sleepy": dict(cat="misty", acc=[],
                   hook="SHHH...", sub="CATS NAP FOR REAL",
                   pose="sleepy", orbit=0.35),
}


def frame(name, cfg, i):
    t = i / FPS
    img = rr.render(cfg["cat"], cfg["acc"], POSES[cfg["pose"]](t),
                    W=W, H=H, yaw=20 + i * cfg["orbit"], pitch=12)
    # krok överst, budskap under — stora ytor säljer i flödet
    text(img, cfg["hook"], W // 2, 46, 3, CYAN)
    text(img, cfg["sub"], W // 2, 84, 1)
    # avsändare i botten hela tiden (shorts klipps ofta utan slut-kort)
    text(img, "PURRFECT COMPANIONS", W // 2, H - 64, 1)
    text(img, "CURSEFORGE . MCPEDL", W // 2, H - 48, 1, DIM)
    text(img, "PURRFECT.PELLEOPS.SE", W // 2, H - 32, 1, DIM)
    # mjuk in-/uttoning för loopkänsla
    k = min(1.0, (i + 1) / 6, (DUR - i) / 6)
    if k < 1.0:
        img = [[(int(p[0] * k), int(p[1] * k), int(p[2] * k), 255) for p in row] for row in img]
    return img


def worker(arg):
    name, cfg, i, outdir = arg
    rr.write_png(f"{outdir}/{i:05d}.png", W, H, frame(name, cfg, i))


def main():
    for name, cfg in SHORTS.items():
        outdir = f"/tmp/short-{name}"
        shutil.rmtree(outdir, ignore_errors=True); os.makedirs(outdir)
        jobs = [(name, cfg, i, outdir) for i in range(DUR)]
        with multiprocessing.Pool(min(4, multiprocessing.cpu_count())) as pool:
            list(pool.imap_unordered(worker, jobs, chunksize=8))
        out = f"/tmp/purrfect-short-{name}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                        "-i", f"{outdir}/%05d.png",
                        "-vf", "scale=1080:1920:flags=neighbor",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out],
                       check=True)
        print(f"{name}: {out} ({os.path.getsize(out) // 1024} kB)")


if __name__ == "__main__":
    main()
