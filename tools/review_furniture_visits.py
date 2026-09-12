#!/usr/bin/env python3
"""Sample actual action keyframes and clothed small/large cats; software renders."""
import sys,json,argparse,math
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE))
import render_regression as r
RP=BASE/'PurrfectCompanions_RP'
ANIM=json.loads((RP/'animations/katt.animation.json').read_text())['animations']
BONES=r.bones_for;TEXTURES=r.texturer

def sample(value,t):
 if not isinstance(value,dict):return value
 keys=sorted((float(k),v) for k,v in value.items())
 if t<=keys[0][0]:return keys[0][1]
 for (a,av),(b,bv) in zip(keys,keys[1:]):
  if t<=b:return [x+(y-x)*(t-a)/(b-a) for x,y in zip(av,bv)]
 return keys[-1][1]

def render(kind='basket',t=0,clothed=True,action_name=None,yaw=28,visitor=None):
 block={'basket':'sovkorg','spa':'kattspa','tv':'katt_tv','scratch':'klosbrada','window':'fonsterbadd','fountain':'kattfontan'}[kind]
 geo=json.loads((RP/f'models/blocks/{block}.geo.json').read_text())['minecraft:geometry'][0]
 bones=[('furniture',[0,0,0],geo['bones'][0]['cubes'],'furniture')]
 w,h,px=r.read_png(str(RP/f'textures/blocks/pc_{block}.png'))
 if kind in ('spa','tv'):
  w,strip_h,strip=r.read_png(str(RP/f'textures/blocks/pc_{block}_animated.png'))
  h=w;frame=int(t/.4)%4;px=strip[frame*h:(frame+1)*h]
 tex={'furniture':(px,w,h,1)};poses={};positions={};transforms={}
 action=ANIM['animation.katt.'+(action_name or ('korgvila' if kind=='basket' else kind))]
 posed=action['bones'];time=t%action['animation_length'] if action.get('loop') is True else min(t,action['animation_length'])
 visitors=[('mocha',.85,['doktorsrock1','tossor1']),('snow',1.15,['ryggsack1','mantel1'])] if kind=='basket' else [('mocha' if kind=='spa' else 'snow',.85 if kind=='spa' else 1.15,['doktorsrock1','tossor1'] if kind=='spa' else ['regnrock1','ryggsack1'])]
 if visitor is not None:visitors=[visitor]
 for slot,(cat,scale,outfit) in enumerate(visitors):
  ts=TEXTURES(cat)
  if kind=='basket' or (kind=='window' and action_name in ('windowlagg','korgvila')):
   w,h,px=r.read_png(str(RP/f'textures/entity/{cat}_sleep.png'));ts['pals']=(px,w,h,4)
  for mat,value in ts.items():tex[f'{slot}_{mat}']=value
  for item in BONES(outfit if clothed else []):
   name,pivot,cubes=item[:3];mat=item[3] if len(item)>3 else 'default';key=f'{slot}_{name}'
   bones.append((key,pivot,cubes,f'{slot}_{mat}'))
   poses[key]=sample(posed.get(name,{}).get('rotation',[0,0,0]),time)
   positions[key]=sample(posed.get(name,{}).get('position',[0,0,0]),time)
   offset=[-7.36 if slot==0 else 7.36,3,0] if kind=='basket' else [0,16,-4] if kind=='window' else [0,1,0] if kind=='spa' else [0,0,-17.6 if kind=='fountain' else -15.2 if kind=='scratch' else -20.8]
   transforms[key]=(scale,0 if kind=='basket' else 180,offset)
 tex['default']=tex['furniture'];r.bones_for=lambda *args:bones;r.texturer=lambda *args:tex
 try:return r.render('mocha',[],poses,W=480,H=360,yaw=yaw,pitch=-24,positions=positions,transforms=transforms,ram=((-18,18),(0,34 if kind=='window' else 22),(-32,15)))
 finally:r.bones_for=BONES;r.texturer=TEXTURES

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default='/tmp/pc-furniture-visits.png');parser.add_argument('--frames',type=int,default=0);args=parser.parse_args()
 out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
 count=args.frames or 1
 for frame in range(count):
  imgs=[render(kind,frame*12/count) for kind in ('basket','spa','tv')]
  canvas=[sum((im[y] for im in imgs),[]) for y in range(360)]
  path=out if not args.frames else out.parent/f'frame-{frame:03}.png'
  r.write_png(str(path),1440,360,canvas)
 print(out.parent if args.frames else out)
