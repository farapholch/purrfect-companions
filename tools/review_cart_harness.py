#!/usr/bin/env python3
"""Diagnostic render: three cart colors on small/large cats, bare and with cape."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import render_regression as r
page=[]
for variant in [1,2,3]:
    tiles=[]
    for cat,scale,acc,pose,yaw in [('mocha',.85,[f'vagn{variant}'],{},65),('snow',1.15,[f'vagn{variant}','mantel1'],r.POSE,-45)]:
        transforms={bone[0]:(scale,0,(0,0,0)) for bone in r.bones_for(acc)}
        tiles.append(r.render(cat,acc,pose,W=280,H=240,yaw=yaw,transforms=transforms,ram=((-10,10),(0,20),(-11,18))))
    page.extend([a+b for a,b in zip(*tiles)])
r.write_png(sys.argv[1] if len(sys.argv)>1 else '/tmp/pc-harness-final.png',560,720,page)
