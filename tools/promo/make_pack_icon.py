#!/usr/bin/env python3
"""Paketikonen (pack_icon.png i BP+RP): de fyra katternas ansikten i 2x2
på sajtens gradient — renderade med regressionsmotorn via make_logo.

    python3 tools/promo/make_pack_icon.py
"""
import sys, os
BASE=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0,f"{BASE}/tools/promo"); sys.path.insert(0,BASE)
import render_regression as rr, make_video as mv, make_logo as ml

def bg(w,h):
    top,bot=(26,26,46),(48,32,84)
    return [[(top[0]+(bot[0]-top[0])*y//h, top[1]+(bot[1]-top[1])*y//h,
              top[2]+(bot[2]-top[2])*y//h,255) for _ in range(w)] for y in range(h)]

def head_sprite(cat,size=240):
    img,bgpix=ml.head_render(cat,size)
    def near(p): return abs(p[0]-bgpix[0])+abs(p[1]-bgpix[1])+abs(p[2]-bgpix[2])<18
    return [[(p[0],p[1],p[2],0 if near(p) else 255) for p in row] for row in img]

W=H=256
mv.W,mv.H=W,H
img=bg(W,H)
# SEX ANSIKTEN I 3x2 sedan Ginger och Domino kom. Ikonen låg kvar på fyra i
# 2x2 och visades så varje gång någon valde paketet i spelet — den bilden är
# det man ser oftast av hela projektet. Huvudena är mindre (104 -> 82) men
# fortfarande läsbara i 64 px, vilket är storleken de faktiskt visas i.
for i,cat in enumerate(("misty","hazel","mocha","snow","ginger","domino")):
    s=head_sprite(cat); sh,sw=len(s),len(s[0])
    x,y=[(48,70),(128,70),(208,70),(48,176),(128,176),(208,176)][i]
    mv.paste(img,s,sw,sh,x,y,82)
out=[[(p[0],p[1],p[2],255) for p in r] for r in img]
for pack in ("PurrfectCompanions_BP","PurrfectCompanions_RP"):
    rr.write_png(f"{BASE}/{pack}/pack_icon.png",W,H,out)
print("pack_icon.png skriven till BP+RP")
