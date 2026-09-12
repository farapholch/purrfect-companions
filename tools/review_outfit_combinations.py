#!/usr/bin/env python3
"""Render real accessory combinations in rest, walk, sit and sleep; audit intersections."""
import argparse,json,sys,itertools,math
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
if not (BASE/'build_accessories.py').exists(): BASE=Path('/opt/purrfect-companions')
sys.path.insert(0,str(BASE))
import render_regression as r
SCENES={
 'backpack_cape':('ryggsack1','mantel1'),
 'backpack_star_cloak':('ryggsack1','rymdmantel1'),
 'saddle_cape':('sadel1','mantel1'),
 'armor_cape':('rustning1','mantel1'),
 'coat_backpack':('doktorsrock1','ryggsack1'),
 'raincoat_backpack':('regnrock1','ryggsack1'),
 'cart_cape':('vagn1','mantel1'),
 'cap_glasses':('keps1','glasogon1'),
 'witch_glasses':('haxhatt1','glasogon1'),
 'santa_glasses':('tomteluva1','glasogon1'),
 'crown_glasses':('krona1','glasogon1'),
 'lamp_glasses':('gruvlampa1','glasogon1'),
 'wings_backpack':('vingar1','ryggsack1'),
 'coat_booties':('doktorsrock1','tossor1'),
}
def poses():
    result={'rest':({},{}),'walk':(r.POSE,{})}
    data=json.loads((BASE/'PurrfectCompanions_RP/animations/katt.animation.json').read_text())['animations']
    for name,key in (('sit','sit'),('sleep','sova')):
        bones=data[f'animation.katt.{key}']['bones']
        result[name]=({b:v.get('rotation',[0,0,0]) for b,v in bones.items()},
                      {b:v.get('position',[0,0,0]) for b,v in bones.items()})
    return result

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def boxes(accessory,pose,positions):
    result=[]
    for bone in r.GEO[f'geometry.katt.{accessory}']['bones']:
        deg=pose.get(bone['name'],[0,0,0]);shift=positions.get(bone['name'],[0,0,0])
        axes=[r.rot(v,[0,0,0],deg) for v in ((1,0,0),(0,1,0),(0,0,1))]
        for cube in bone['cubes']:
            center=r.rot([o+s/2 for o,s in zip(cube['origin'],cube['size'])],bone['pivot'],deg)
            result.append(([v+t for v,t in zip(center,shift)],axes,[s/2 for s in cube['size']]))
    return result

def intersects(a,b):
    ca,aa,ha=a;cb,ab,hb=b;delta=[v-u for u,v in zip(ca,cb)]
    for axis in aa+ab+[cross(x,y) for x in aa for y in ab]:
        if dot(axis,axis)<1e-10:continue
        reach=sum(abs(dot(axis,v))*h for v,h in zip(aa,ha))+sum(abs(dot(axis,v))*h for v,h in zip(ab,hb))
        if abs(dot(delta,axis)) >= reach-1e-5:return False
    return True

def audit(scene):
    result={}
    for name,(pose,positions) in poses().items():
        hits=[]
        for a,b in itertools.combinations(scene,2):
            hits += [(a,i,b,j) for i,x in enumerate(boxes(a,pose,positions)) for j,y in enumerate(boxes(b,pose,positions)) if intersects(x,y)]
        if hits:result[name]=hits
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('/tmp/pc-outfit-combinations'))
    parser.add_argument('--names',nargs='*',choices=SCENES)
    parser.add_argument('--audit-only',action='store_true')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    report={}
    for name in args.names or SCENES:
        scene=SCENES[name];report[name]=audit(scene)
        if not args.audit_only:
            frames=[r.render('misty',scene,pose,W=150,H=160,positions=positions,ram=((-10,10),(-1,18),(-12,16))) for pose,positions in poses().values()]
            pixels=[sum((frame[y] for frame in frames),[]) for y in range(160)]
            r.write_png(str(args.output/f'{name}.png'),600,160,pixels)
        print(name, 'intersections='+str(sum(map(len,report[name].values()))),flush=True)
    (args.output/'intersections.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':main()
