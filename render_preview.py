#!/usr/bin/env python3
"""Renderar förhandsbilder av katterna (med valfria tillbehör) — ren stdlib.

Används för MCPEDL-inskickning och för att syna ändringar utan att starta spelet.
OBS: renderaren har samplingsbrus — för att granska SMÅ detaljer, dumpa
texturregionen pixelvis i stället (se README, fallgrop om renderaren).

    python3 render_preview.py            # skriver alla bilder till publish/
"""
import json, math, zlib, struct, os

BASE = "/opt/purrfect-companions"; RP = f"{BASE}/PurrfectCompanions_RP"; OUT = f"{BASE}/publish"

def read_png(path):
    d=open(path,'rb').read(); pos=8; idat=b''; w=h=None
    while pos<len(d):
        ln=struct.unpack(">I",d[pos:pos+4])[0]; typ=d[pos+4:pos+8]; data=d[pos+8:pos+8+ln]
        if typ==b'IHDR': w,h=struct.unpack(">II",data[:8])
        elif typ==b'IDAT': idat+=data
        pos+=12+ln
    raw=zlib.decompress(idat); px=[]; stride=w*4; prev=bytearray(stride); i=0
    for y in range(h):
        f=raw[i]; i+=1; line=bytearray(raw[i:i+stride]); i+=stride
        for x in range(stride):
            a=line[x-4] if x>=4 else 0; b=prev[x]; cc=prev[x-4] if x>=4 else 0
            if f==1: line[x]=(line[x]+a)&255
            elif f==2: line[x]=(line[x]+b)&255
            elif f==3: line[x]=(line[x]+(a+b)//2)&255
            elif f==4:
                p=a+b-cc; pa,pb,pc=abs(p-a),abs(p-b),abs(p-cc)
                line[x]=(line[x]+(a if(pa<=pb and pa<=pc) else (b if pb<=pc else cc)))&255
        prev=line; px.append([tuple(line[x*4:x*4+4]) for x in range(w)])
    return w,h,px

def write_png(p,w,h,px):
    def ch(t,d):
        c=t+d; return struct.pack(">I",len(d))+c+struct.pack(">I",zlib.crc32(c)&0xffffffff)
    raw=bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w): raw+=bytes(px[y][x])
    open(p,"wb").write(b"\x89PNG\r\n\x1a\n"+ch(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0))
        +ch(b"IDAT",zlib.compress(bytes(raw),9))+ch(b"IEND",b""))

GEO={g["description"]["identifier"]:g
     for g in json.load(open(f"{RP}/models/entity/katt.geo.json"))["minecraft:geometry"]}

def cubes_for(accessories):
    """Kattens kuber + valda tillbehörs kuber."""
    out=[(c["origin"],c["size"],c["uv"]) for b in GEO["geometry.katt"]["bones"] for c in b.get("cubes",[])]
    for a in accessories:
        g=GEO.get(f"geometry.katt.{a}")
        if g: out+=[(c["origin"],c["size"],c["uv"]) for b in g["bones"] for c in b.get("cubes",[])]
    return out

def faces(U,V,w,h,d):
    return dict(top=(U+d,V,w,d),bottom=(U+d+w,V,w,d),west=(U,V+d,d,h),
                north=(U+d,V+d,w,h),east=(U+d+w,V+d,d,h),south=(U+2*d+w,V+d,w,h))

C=math.cos(math.radians(30)); Sn=math.sin(math.radians(30))
def proj(x,y,z): return ((x-z)*C,(x+z)*Sn-y)

def render(cat, accessories, W, H, bg=(30,33,41,255), pad=18):
    tw,th,tex=read_png(f"{RP}/textures/entity/{cat}.png")
    cubes=cubes_for(accessories)
    pts=[proj(o[0]+dx,o[1]+dy,o[2]+dz) for (o,s,_) in cubes
         for dx in(0,s[0]) for dy in(0,s[1]) for dz in(0,s[2])]
    minx,maxx=min(p[0] for p in pts),max(p[0] for p in pts)
    miny,maxy=min(p[1] for p in pts),max(p[1] for p in pts)
    scale=min((W-2*pad)/(maxx-minx),(H-2*pad)/(maxy-miny))
    offx=pad-minx*scale+(W-2*pad-(maxx-minx)*scale)/2
    offy=pad-miny*scale+(H-2*pad-(maxy-miny)*scale)/2
    cv=[[bg]*W for _ in range(H)]
    fl=[]
    for (o,sz,uv) in cubes:
        ox,oy,oz=o; w,h,d=sz; U,V=uv; F=faces(U,V,w,h,d)
        for reg,shd,fn in [
            (F["top"],1.00,lambda a,b,ox=ox,oy=oy,oz=oz,w=w,h=h,d=d:(ox+a*w,oy+h,oz+b*d)),
            (F["north"],0.80,lambda a,b,ox=ox,oy=oy,oz=oz,w=w,h=h,d=d:(ox+a*w,oy+(1-b)*h,oz)),
            (F["east"],0.62,lambda a,b,ox=ox,oy=oy,oz=oz,w=w,h=h,d=d:(ox+w,oy+(1-b)*h,oz+a*d))]:
            cx,cy,cz=fn(0.5,0.5); fl.append((cx+cy-cz,reg,shd,fn))
    fl.sort(key=lambda f:f[0])
    for _,(u0,v0,fw,fh),shd,fn in fl:
        steps=max(int(max(fw,fh)*scale*2.6),12)
        for i in range(steps+1):
            for j in range(steps+1):
                a,b=i/steps,j/steps
                x,y,z=fn(a,b); sx,sy=proj(x,y,z)
                px=int(sx*scale+offx); py=int(sy*scale+offy)
                if not(0<=px<W and 0<=py<H): continue
                col=tex[min(th-1,max(0,int(v0+b*fh)))][min(tw-1,max(0,int(u0+a*fw)))]
                if col[3]<8: continue
                cv[py][px]=(int(col[0]*shd),int(col[1]*shd),int(col[2]*shd),255)
    return cv


def render3d(cat, acc, W, H, yaw_deg=32, pitch_deg=20, bg=(24,27,36,255), pad_frac=0.09):
    """Z-buffrad rendering med fri kameravinkel (yaw 0 = rakt framifrån).
    Ersätter den gamla painter's-algoritmen: den ritade ben ÖVER tossor."""
    import math
    tw,th,tex=read_png(f"{RP}/textures/entity/{cat}.png")
    cubes=cubes_for(acc)
    ya=math.radians(yaw_deg); pa=math.radians(pitch_deg)
    def pj(x,y,z):
        xr=x*math.cos(ya)+z*math.sin(ya); zr=-x*math.sin(ya)+z*math.cos(ya)
        return (xr, y*math.cos(pa)-zr*math.sin(pa), zr*math.cos(pa)+y*math.sin(pa))
    pts=[pj(o[0]+dx,o[1]+dy,o[2]+dz) for (o,s,_) in cubes
         for dx in(0,s[0]) for dy in(0,s[1]) for dz in(0,s[2])]
    minx=min(p[0] for p in pts); maxx=max(p[0] for p in pts)
    miny=min(p[1] for p in pts); maxy=max(p[1] for p in pts)
    pad=int(min(W,H)*pad_frac)
    sc=min((W-2*pad)/(maxx-minx),(H-2*pad)/(maxy-miny))
    offx=pad-minx*sc+(W-2*pad-(maxx-minx)*sc)/2
    offy=pad-miny*sc+(H-2*pad-(maxy-miny)*sc)/2
    cv=[[bg]*W for _ in range(H)]; zb=[[9e9]*W for _ in range(H)]
    SH={"top":1.00,"bottom":0.45,"north":0.92,"south":0.55,"east":0.72,"west":0.66}
    for (o,s,uv) in cubes:
        ox,oy,oz=o; w,h,d=s; U,V=uv; F=faces(U,V,w,h,d)
        fns={"top":lambda a,b:(ox+a*w,oy+h,oz+b*d), "bottom":lambda a,b:(ox+a*w,oy,oz+b*d),
             "north":lambda a,b:(ox+a*w,oy+(1-b)*h,oz), "south":lambda a,b:(ox+a*w,oy+(1-b)*h,oz+d),
             "east":lambda a,b:(ox+w,oy+(1-b)*h,oz+a*d), "west":lambda a,b:(ox,oy+(1-b)*h,oz+a*d)}
        for name,fn in fns.items():
            u0,v0,fw,fh=F[name]; shd=SH[name]
            steps=max(int(max(fw,fh)*sc*1.5),12)
            for i in range(steps+1):
                for j in range(steps+1):
                    a,b=i/steps,j/steps
                    X,Y,Z=pj(*fn(a,b))
                    px=int(X*sc+offx); py=int(H-(Y*sc+offy))
                    if not(0<=px<W and 0<=py<H): continue
                    if Z>=zb[py][px]: continue
                    col=tex[min(th-1,max(0,int(v0+b*fh)))][min(tw-1,max(0,int(u0+a*fw)))]
                    if col[3]<8: continue
                    cv[py][px]=(int(col[0]*shd),int(col[1]*shd),int(col[2]*shd),255)
                    zb[py][px]=Z
    return cv

def sheet(panels, cols, PW, PH, gap=2):
    rows=(len(panels)+cols-1)//cols
    W=cols*PW+(cols-1)*gap; H=rows*PH+(rows-1)*gap
    out=[[(18,20,26,255)]*W for _ in range(H)]
    for i,p in enumerate(panels):
        ox=(i%cols)*(PW+gap); oy=(i//cols)*(PH+gap)
        for y in range(PH):
            for x in range(PW): out[oy+y][ox+x]=p[y][x]
    return W,H,out

if __name__=="__main__":
    os.makedirs(OUT,exist_ok=True)
    CATS=["misty","hazel","mocha","snow","ginger","domino"]
    PW=PH=300
    # 1) alla katterna — tre i bredd så sex ryms utan att rutorna krymper
    W,H,img=sheet([render3d(c,[],PW,PH) for c in CATS],3,PW,PH)
    write_png(f"{OUT}/01-katterna.png",W,H,img); print("01-katterna.png")
    # 2) tillbehör: sex ROLLER, inte sex slumpvisa plaggkombinationer, och en
    #    av dem fullt utrustad så bredden syns i samma bild som variationen.
    #    Alla sex bär olika saker — den som bara visar hela kittet på allihop
    #    döljer pälsarna och säger inget om vad plaggen är till för.
    looks=[("misty",  ["rustning1","horn1","vingar1","halsduk1","ryggsack1","tossor2","vagn1"]),  # FULLT UTRUSTAD
           ("hazel",  ["sadel1","tomteluva1","halsduk2"]),        # riddjuret
           ("mocha",  ["horn2","vingar1","halsband1"]),           # enhörningskatten
           ("snow",   ["doktorsrock1","glasogon2","ryggsack2"]),  # doktorn
           ("ginger", ["krona1","mantel2","halsband2"]),          # kungligheten
           ("domino", ["rustning4","energisvard1","tossor1"])]    # krigaren med bladet
    W,H,img=sheet([render3d(c,a,PW,PH) for c,a in looks],3,PW,PH)
    write_png(f"{OUT}/02-tillbehor.png",W,H,img); print("02-tillbehor.png")
    # 3) en fullt utrustad katt, stor
    img=render3d("misty",["rustning1","horn1","vingar1","halsduk1","ryggsack1","tossor2","vagn1"],640,440)
    write_png(f"{OUT}/03-fullt-utrustad.png",640,440,img); print("03-fullt-utrustad.png")
    # 4) alla katterna i FULL utrustning — begärd bild till butikssidan.
    #    Med hela kittet (rustning + vagn + vingar) försvinner pälsen bakom
    #    utrustningen och de sex ser nästan lika ut, därför finns även 05:
    #    samma katter utstyrda, men med plagg som lämnar pälsen synlig.
    FULL_KIT=["rustning1","horn1","vingar1","halsduk1","ryggsack1","tossor2","vagn1"]
    LATT_KIT=["horn1","vingar1","halsduk1","tossor2","halsband1"]
    W,H,img=sheet([render3d(c,FULL_KIT,PW,PH) for c in CATS],3,PW,PH)
    write_png(f"{OUT}/04-alla-fullt-utrustade.png",W,H,img); print("04-alla-fullt-utrustade.png")
    W,H,img=sheet([render3d(c,LATT_KIT,PW,PH) for c in CATS],3,PW,PH)
    write_png(f"{OUT}/05-alla-utstyrda.png",W,H,img); print("05-alla-utstyrda.png")
    # (projektloggan flyttad till tools/promo/make_logo.py: den bygger ur
    #  head_render och gör ett stort ansikte, som håller i avatarstorlek)

