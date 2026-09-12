import sys,json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_blocks as b
from build_accessories import read_png
for bid,material in [('kattspa','vatten'),('katt_tv','skarm')]:
    w,h,p=read_png(f'{b.RP}/textures/blocks/pc_{bid}_animated.png')
    assert h==w*4
    bw,bh,base=read_png(f'{b.RP}/textures/blocks/pc_{bid}.png')
    assert bw==bh==w and base==p[:w]
    cfg=b.BLOCKS[bid];uv=b.packa_kuber(cfg['cubes']);allowed=set()
    for i,(_,size,mat) in enumerate(cfg['cubes']):
        if mat!=material: continue
        u,v=uv[i];x,y,z=size
        allowed.update((xx,yy) for yy in range(v,v+int(z+y+.999)) for xx in range(u,u+int(2*(z+x)+.999)))
    changes=set()
    for phase in range(1,4):
        changes.update((x,y) for y in range(w) for x in range(w) if p[phase*w+y][x]!=base[y][x])
    assert changes and changes<=allowed,(bid,len(changes))
    geo=json.load(open(f'{b.RP}/models/blocks/{bid}.geo.json'))['minecraft:geometry'][0]['description']
    assert geo['texture_width']==geo['texture_height']==w
    print(f'PASS {bid}: four square frames; only {material} changes; UV dimensions match')
