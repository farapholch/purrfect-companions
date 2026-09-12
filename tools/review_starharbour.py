#!/usr/bin/env python3
"""Diagnostic cutaway of generated Star Harbour blocks, not a game screenshot."""
import sys,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build_spaceworld as s
import render_world as r

def voxels():
 cats={n:n for n in ['misty','hazel','mocha','snow']};disp={n:n.capitalize() for n in cats}
 base=Path('/tmp/harbour-review-structures');s.build_structures(str(base),s.TEXTS['public'],disp,cats)
 vox={(x,s.G,z):'tuff' for x in range(-40,79) for z in range(-15,45)}
 for cmd in s.build_commands(cats,disp,s.TEXTS['public']):
  if not isinstance(cmd,str):continue
  parts=cmd.split();kind=parts[0]
  if kind=='fill':
   x1,y1,z1,x2,y2,z2=map(int,parts[1:7]);block=parts[7];hollow=parts[-1]=='hollow'
   for x in range(x1,x2+1):
    for y in range(y1,y2+1):
     for z in range(z1,z2+1):
      b='air' if hollow and x1<x<x2 and y1<y<y2 and z1<z<z2 else block
      if b=='air':vox.pop((x,y,z),None)
      else:vox[x,y,z]=b
  elif kind=='setblock':
   pos=tuple(map(int,parts[1:4]));block=parts[4]
   if block=='air':vox.pop(pos,None)
   else:vox[pos]=block
  elif kind=='structure' and parts[1]=='load':
   key=parts[2].replace(':','/');data=(base/'structures'/f'{key}.mcstructure').read_bytes()
   root,_=s.nbt._read(data,3,s.nbt.TAG_COMPOUND);st=root.v
   sizes=[v.v for v in st['size'].v[1]];pal=st['structure'].v['palette'].v['default'].v['block_palette'].v[1]
   indices=st['structure'].v['block_indices'].v[1][0].v[1];origin=list(map(int,parts[3:6]));i=0
   for x in range(sizes[0]):
    for y in range(sizes[1]):
     for z in range(sizes[2]):
      index=indices[i].v;i+=1
      if index>=0:vox[origin[0]+x,origin[1]+y,origin[2]+z]=pal[index].v['name'].v
 return vox
if __name__=='__main__':
 v=voxels();r.VANILLA.update({'iron_block':(175,182,188),'glass':(143,190,203),'blackstone':(57,54,65),'light_gray_concrete':(145,148,147),'ladder':(147,108,61),'standing_sign':(158,121,71),'wall_sign':(158,121,71),'tuff':(89,94,83),'light_blue_concrete':(48,167,202),'lime_concrete':(106,170,39),'water':(49,111,204),'farmland':(101,65,36),'wheat':(208,182,71),'carrots':(94,158,47),'potatoes':(106,144,46),'quartz_block':(217,213,202),'sea_lantern':(162,228,222)})
 r.render_topdown(v,r._custom_colors(),'/tmp/harbour-expansion-map.png',ymax=s.F+2,area=((-40,79),(-15,45)),scale=8)
