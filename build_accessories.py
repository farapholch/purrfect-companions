#!/usr/bin/env python3
"""Genererar ALLA tillbehör till Mjau Mods från en enda definition nedan.

Lägg till ett nytt plagg genom att lägga till en post i ACC — skriptet skapar
geometri, textur, render controller, entity-property, event, interaktion,
föremål, ikon, recept och språksträng. Kör sedan `purrfect-test`.

Varje plagg är en EGEN liten geometri (inte inbakad i kattmodellen) — annars
exploderar antalet kombinationer. Läget styrs av entity properties, så alla
plagg är oberoende av varandra.
"""
import json, shutil, zlib, struct, glob, os

BASE = "/opt/purrfect-companions"; BP = f"{BASE}/PurrfectCompanions_BP"; RP = f"{BASE}/PurrfectCompanions_RP"
TEX = 256

# ---------------------------------------------------------------- definition
# uv: startpunkt i texturen. cubes: (origin, size, uv-offset från plaggets uv)
ACC = {
 "sadel": dict(label="Cat Saddle", bone="body", sound="saddle", rideable=True,
   uv={1:(24,26),2:(56,26),3:(88,26)},
   colors={1:("brun",(122,79,45)),2:("svart",(58,52,48)),3:("ljus",(206,190,160))},
   names={1:"Brown",2:"Black",3:"Light"},
   cubes=[([-3.25,9,-3],[6.5,1,6],(0,0)), ([-1.5,10,-3],[3,1,1],(0,8))],
   recipe=lambda mat: dict(pattern=["LLL","S S"] if not mat else ["LLL","SDS"],
       key={"L":{"item":"minecraft:leather"},"S":{"item":"minecraft:string"}} if not mat
           else {"L":{"item":"minecraft:leather"},"S":{"item":"minecraft:string"},"D":{"item":mat}},
       unlock=[{"item":"minecraft:leather"}]+([{"item":mat}] if mat else [])),
   mats={1:None,2:"minecraft:black_dye",3:"minecraft:white_dye"}),

 "keps": dict(label="Cat Cap", bone="head", sound="armor.equip_leather",
   uv={1:(24,40),2:(56,40),3:(24,56),4:(56,56)},
   colors={1:("cyan",(0,168,214)),2:("rod",(198,62,55)),3:("gron",(76,168,84)),4:("gul",(238,196,62))},
   names={1:"Cyan",2:"Red",3:"Green",4:"Yellow"},
   cubes=[([-3.25,9.8,-9.25],[6.5,2,4.5],(0,0)), ([-2.5,9.9,-11.5],[5,0.5,2.5],(0,8))],
   recipe=lambda mat: dict(pattern=["WWW"," L "],
       key={"W":{"item":mat},"L":{"item":"minecraft:leather"}},
       unlock=[{"item":mat},{"item":"minecraft:leather"}]),
   mats={1:"minecraft:cyan_wool",2:"minecraft:red_wool",3:"minecraft:green_wool",4:"minecraft:yellow_wool"}),

 "halsduk": dict(label="Cat Scarf", bone="body", sound="armor.equip_leather",
   uv={1:(0,72),2:(24,72),3:(48,72),4:(72,72)},
   colors={1:("rod",(198,62,55)),2:("bla",(64,116,200)),3:("gron",(76,168,84)),4:("gul",(238,196,62))},
   names={1:"Red",2:"Blue",3:"Green",4:"Yellow"},
   cubes=[([-3.4,7.5,-5.6],[6.8,2,1.6],(0,0)), ([-1,5,-5.7],[2,2.5,1],(0,6))],
   recipe=lambda mat: dict(pattern=["WW","WW"], key={"W":{"item":mat}}, unlock=[{"item":mat}]),
   mats={1:"minecraft:red_wool",2:"minecraft:blue_wool",3:"minecraft:green_wool",4:"minecraft:yellow_wool"}),

 "ryggsack": dict(label="Cat Backpack", bone="body", sound="armor.equip_leather",
   uv={1:(0,88),2:(24,88),3:(48,88)},
   colors={1:("brun",(122,79,45)),2:("gron",(76,140,84)),3:("bla",(64,104,168))},
   names={1:"Brown",2:"Green",3:"Blue"},
   cubes=[([-3.25,9,1],[6.5,2.5,3],(0,0)), ([-3.4,9.5,1.5],[6.9,0.5,2],(0,8))],
   recipe=lambda mat: dict(pattern=["S S","LDL","LLL"],
       key={"L":{"item":"minecraft:leather"},"S":{"item":"minecraft:string"},"D":{"item":mat}},
       unlock=[{"item":"minecraft:leather"},{"item":mat}]),
   mats={1:"minecraft:brown_dye",2:"minecraft:green_dye",3:"minecraft:blue_dye"}),

 "glasogon": dict(label="Cat Glasses", bone="head", sound="armor.equip_generic",
   uv={1:(0,100),2:(16,100),3:(32,100)},
   colors={1:("svart",(38,38,42)),2:("guld",(212,175,60)),3:("rosa",(232,130,180))},
   names={1:"Black",2:"Gold",3:"Pink"},
   cubes=[([-3.2,7.8,-9.5],[6.4,1.4,0.5],(0,0))],
   recipe=lambda mat: dict(pattern=["GDG"],
       key={"G":{"item":"minecraft:glass_pane"},"D":{"item":mat}},
       unlock=[{"item":"minecraft:glass_pane"},{"item":mat}]),
   mats={1:"minecraft:black_dye",2:"minecraft:gold_nugget",3:"minecraft:pink_dye"}),

 # fyra tossor delar samma UV-region (som benen gör i grundmodellen)
 "tossor": dict(label="Cat Booties", bone="body", sound="armor.equip_leather",
   uv={1:(0,118),2:(12,118),3:(24,118),4:(36,118)},
   colors={1:("vit",(240,240,238)),2:("svart",(52,50,56)),3:("rod",(198,62,55)),4:("gul",(238,196,62))},
   names={1:"White",2:"Black",3:"Red",4:"Yellow"},
   cubes=[([-3.2,-0.05,2.8],[2.4,1.6,2.4],(0,0)),   # bak vänster
          ([0.8,-0.05,2.8],[2.4,1.6,2.4],(0,0)),    # bak höger
          ([-3.2,-0.05,-5.2],[2.4,1.6,2.4],(0,0)),  # fram vänster
          ([0.8,-0.05,-5.2],[2.4,1.6,2.4],(0,0))],  # fram höger
   recipe=lambda mat: dict(pattern=["W W","W W"], key={"W":{"item":mat}}, unlock=[{"item":mat}]),
   mats={1:"minecraft:white_wool",2:"minecraft:black_wool",3:"minecraft:red_wool",4:"minecraft:yellow_wool"}),

 "vagn": dict(label="Cat Cart", bone="body", sound="armor.equip_leather",
   uv={1:(0,128),2:(32,128),3:(64,128)},
   colors={1:("tra",(150,108,64)),2:("rod",(178,58,52)),3:("bla",(58,102,172))},
   names={1:"Wood",2:"Red",3:"Blue"},
   # uppskalad ~35 % efter Xbox-test ("för liten") — flaket rymmer en spelare
   cubes=[([-4,2,8],[8,5,7],(0,0)),          # flaket
          ([-4.9,0,10],[1,4,4],(0,13)),      # hjul vänster
          ([3.9,0,10],[1,4,4],(0,13)),       # hjul höger
          ([-0.5,4.5,5],[1,1,3],(12,13))],   # dragstång till katten
   # seat 0 = I VAGNEN (styr som en släde), seat 1 = på ryggen. Xbox-testet:
   # med ryggen som seat 0 gick vagnen aldrig att sitta i — ensam spelare får
   # alltid första lediga sätet.
   seats=[[0.0,0.55,0.72],[0.0,0.562,-0.22]],
   recipe=lambda mat: dict(pattern=["S S","PPP","W W"],
       key={"P":{"item":mat},"S":{"item":"minecraft:stick"},"W":{"item":"minecraft:wooden_slab"}},
       unlock=[{"item":mat},{"item":"minecraft:stick"}]),
   mats={1:"minecraft:oak_planks",2:"minecraft:red_terracotta",3:"minecraft:blue_terracotta"}),

 "halsband": dict(label="Cat Collar", bone="body", sound="armor.equip_leather",
   uv={1:(0,176),2:(24,176),3:(48,176)},
   colors={1:("red",(196,58,52)),2:("blue",(58,102,178)),3:("green",(72,158,80))},
   names={1:"Red",2:"Blue",3:"Green"},
   cubes=[([-3.4,7.6,-5.5],[6.8,1.2,1.4],(0,0)), ([-0.5,6.9,-5.6],[1,1,1],(0,4))],
   recipe=lambda mat: dict(pattern=["LLL"," I "],
       key={"L":{"item":mat},"I":{"item":"minecraft:iron_nugget"}},
       unlock=[{"item":mat},{"item":"minecraft:iron_nugget"}]),
   mats={1:"minecraft:red_wool",2:"minecraft:blue_wool",3:"minecraft:green_wool"}),

 "rosett": dict(label="Cat Bow", bone="head", sound="armor.equip_leather",
   uv={1:(0,186),2:(16,186),3:(32,186),4:(48,186)},
   colors={1:("pink",(238,138,186)),2:("red",(198,62,55)),3:("blue",(64,116,200)),4:("yellow",(238,196,62))},
   names={1:"Pink",2:"Red",3:"Blue",4:"Yellow"},
   cubes=[([-1.5,10.2,-7.6],[3,1.6,1],(0,0))],
   recipe=lambda mat: dict(pattern=["WWW"], key={"W":{"item":mat}}, unlock=[{"item":mat}]),
   mats={1:"minecraft:pink_wool",2:"minecraft:red_wool",3:"minecraft:blue_wool",4:"minecraft:yellow_wool"}),

 "vingar": dict(label="Cat Wings", bone="body", sound="armor.equip_leather",
   uv={1:(0,192),2:(20,192),3:(40,192)},
   colors={1:("white",(242,242,240)),2:("black",(48,46,54)),3:("gold",(226,190,84))},
   names={1:"White",2:"Black",3:"Gold"},
   cubes=[([-4.4,7,0],[0.6,5,5],(0,0)), ([3.8,7,0],[0.6,5,5],(0,0))],
   recipe=lambda mat: dict(pattern=["F F","FWF"],
       key={"F":{"item":"minecraft:feather"},"W":{"item":mat}},
       unlock=[{"item":"minecraft:feather"},{"item":mat}]),
   mats={1:"minecraft:white_wool",2:"minecraft:black_wool",3:"minecraft:gold_ingot"}),

 "horn": dict(label="Unicorn Horn", bone="head", sound="armor.equip_generic",
   uv={1:(96,128),2:(112,128),3:(128,128)},
   colors={1:("vit",(244,240,232)),2:("guld",(238,198,72)),3:("rosa",(238,150,196))},
   names={1:"White",2:"Gold",3:"Pink"},
   # avsmalnande spira mitt i pannan — enhörningskatt (kombinera med vingarna!)
   cubes=[([-0.6,11.5,-7.1],[1.2,1.6,1.2],(0,0)),
          ([-0.45,13.1,-6.95],[0.9,1.4,0.9],(0,4)),
          ([-0.3,14.5,-6.8],[0.6,1.3,0.6],(0,8))],
   recipe=lambda mat: dict(pattern=["N","I","M"],
       key={"N":{"item":"minecraft:gold_nugget"},"I":{"item":mat},
            "M":{"item":"minecraft:bone"}},
       unlock=[{"item":mat}]),
   mats={1:"minecraft:quartz",2:"minecraft:gold_ingot",3:"minecraft:amethyst_shard"}),

 "rustning": dict(label="Cat Armor", bone="body", sound="armor.equip_iron",
   uv={1:(0,224),2:(64,224),3:(128,224),4:(192,224)},
   colors={1:("jarn",(202,206,212)),2:("guld",(238,198,72)),
           3:("diamant",(108,220,214)),4:("netherit",(72,64,70))},
   names={1:"Iron",2:"Gold",3:"Diamond",4:"Netherite"},
   # ryggplåt + sidoplåtar + nackskydd, som hästrustning
   cubes=[([-3.6,8.8,-5.2],[7.2,1,10.4],(0,0)),
          ([-3.7,4.5,-4.5],[0.7,4.5,9],(0,13)),
          ([3.0,4.5,-4.5],[0.7,4.5,9],(0,13)),
          ([-2.5,6.5,-6.2],[5,3,1],(22,13))],
   recipe=lambda mat: dict(pattern=["I I","III","I I"],
       key={"I":{"item":mat}},
       unlock=[{"item":mat}]),
   mats={1:"minecraft:iron_ingot",2:"minecraft:gold_ingot",
         3:"minecraft:diamond",4:"minecraft:netherite_ingot"}),

 "haxhatt": dict(label="Witch Hat", bone="head", sound="armor.equip_leather",
   uv={1:(176,30),2:(216,30)},
   colors={1:("svart",(38,34,44)),2:("lila",(96,56,140))},
   names={1:"Black",2:"Purple"},
   cubes=[([-3,11.5,-8.5],[6,0.8,6],(0,0)),        # brätte
          ([-1.8,12.3,-7.3],[3.6,2.2,3.6],(0,8)),  # kupa
          ([-1,14.5,-6.5],[2,2,2],(0,15))],        # topp
   recipe=lambda mat: dict(pattern=[" W ","WWW"],
       key={"W":{"item":mat}},
       unlock=[{"item":mat}]),
   mats={1:"minecraft:black_wool",2:"minecraft:purple_wool"}),

 "tomteluva": dict(label="Santa Hat", bone="head", sound="armor.equip_leather",
   uv={1:(176,60),2:(216,60)},
   colors={1:("rod",(196,44,44)),2:("gron",(46,128,62))},
   names={1:"Red",2:"Green"},
   cubes=[([-2.6,11.4,-8.1],[5.2,1,5.2],(0,0)),    # vit kant
          ([-1.8,12.4,-7.3],[3.6,2.4,3.6],(0,7)),  # luva
          ([-0.8,14.8,-6.3],[1.6,1.6,1.6],(0,14))],# tofs
   recipe=lambda mat: dict(pattern=[" S ","WWW"],
       key={"W":{"item":mat},"S":{"item":"minecraft:snowball"}},
       unlock=[{"item":mat}]),
   mats={1:"minecraft:red_wool",2:"minecraft:green_wool"}),

 "doktorsrock": dict(label="Doctor Coat", bone="body", sound="armor.equip_leather",
   uv={1:(176,90)},
   colors={1:("vit",(238,240,242))},
   names={1:"White"},
   cubes=[([-3.5,4.2,-4.8],[0.6,4.6,9.4],(0,0)),
          ([2.9,4.2,-4.8],[0.6,4.6,9.4],(0,0)),
          ([-3.5,8.8,-4.8],[7,0.8,9.4],(0,15))],
   recipe=lambda mat: dict(pattern=["W W","WWW","W W"],
       key={"W":{"item":mat}},
       unlock=[{"item":mat}]),
   mats={1:"minecraft:white_wool"}),

 "batvingar": dict(label="Bat Wings", bone="body", sound="armor.equip_leather",
   uv={1:(176,110),2:(216,110)},
   colors={1:("svart",(30,28,34)),2:("lila",(74,44,104))},
   names={1:"Black",2:"Purple"},
   cubes=[([-8.5,8.6,-1],[5,0.7,6],(0,0)),
          ([3.5,8.6,-1],[5,0.7,6],(0,0)),
          ([-9.5,8.4,1],[1.6,3,1.6],(0,8)),
          ([7.9,8.4,1],[1.6,3,1.6],(0,8))],
   recipe=lambda mat: dict(pattern=["L L","LLL"],
       key={"L":{"item":mat}},
       unlock=[{"item":mat}]),
   mats={1:"minecraft:leather",2:"minecraft:phantom_membrane"}),

 "krona": dict(label="Cat Crown", bone="head", sound="armor.equip_generic",
   uv={1:(0,206),2:(24,206)},
   colors={1:("gold",(232,196,72)),2:("silver",(206,210,216))},
   names={1:"Gold",2:"Silver"},
   cubes=[([-2.5,11.6,-8.4],[5,1.6,3.4],(0,0))],
   recipe=lambda mat: dict(pattern=["GEG","GGG"],
       key={"G":{"item":mat},"E":{"item":"minecraft:emerald"}},
       unlock=[{"item":mat},{"item":"minecraft:emerald"}]),
   mats={1:"minecraft:gold_ingot",2:"minecraft:iron_ingot"}),

 "mantel": dict(label="Cat Cape", bone="body", sound="armor.equip_leather",
   uv={1:(0,150),2:(40,150),3:(80,150),4:(120,150)},
   colors={1:("rod",(178,48,44)),2:("bla",(56,96,178)),3:("lila",(122,64,178)),4:("svart",(44,42,48))},
   names={1:"Red",2:"Blue",3:"Purple",4:"Black"},
   cubes=[([-3.3,9.6,-5.6],[6.6,1,0.6],(0,0)),      # krage vid halsen
          ([-3.4,9.9,-5.5],[6.8,0.5,11],(0,3)),      # drapering över ryggen
          ([-3.4,4,5.2],[6.8,6,0.6],(0,16))],        # hängande bakstycke
   recipe=lambda mat: dict(pattern=["S S","WWW","WWW"],
       key={"W":{"item":mat},"S":{"item":"minecraft:string"}},
       unlock=[{"item":mat},{"item":"minecraft:string"}]),
   mats={1:"minecraft:red_wool",2:"minecraft:blue_wool",3:"minecraft:purple_wool",4:"minecraft:black_wool"}),
}

# ---------------------------------------------------------------- hjälpare
def sh(c, f):
    return tuple(max(0, min(255, int(v*f))) for v in c[:3]) + (255,)

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

def uv_footprint(size):
    w,h,d = size
    import math
    return math.ceil(2*(d+w)), math.ceil(d+h)

# ---------------------------------------------------------------- geometri
def build_geometry():
    p=f"{RP}/models/entity/katt.geo.json"
    g=json.load(open(p))
    base=[x for x in g["minecraft:geometry"] if x["description"]["identifier"]=="geometry.katt"][0]
    for b in base["bones"]:
        b["cubes"]=[c for c in b.get("cubes",[]) if c["uv"][1] < 26]   # bara katten själv
    # KRITISKT: bas-geometrin måste deklarera samma texturstorlek som filen.
    # Missas det läses alla UV i fel skala och katten blir obegriplig i spelet
    # (tillbehören såg rätt ut eftersom de byggs om med rätt TEX varje gång).
    base["description"]["texture_width"]=TEX
    base["description"]["texture_height"]=TEX
    desc=lambda i:{"identifier":i,"texture_width":TEX,"texture_height":TEX,
                   "visible_bounds_width":2,"visible_bounds_height":1.5,"visible_bounds_offset":[0,0.5,0]}
    geos=[base,{"description":desc("geometry.katt.empty"),"bones":[{"name":"tom","pivot":[0,0,0]}]}]
    # Ett tillbehörsben roterar kring SIN egen pivot. Har den inte exakt samma
    # pivot som benet med samma namn i grundmodellen svänger plagget kring en
    # annan punkt än kroppsdelen och far ut vid sidan om katten när den rör sig.
    PIVOTS={b["name"]:b["pivot"] for b in base["bones"]}
    for a,cfg in ACC.items():
        for i in cfg["colors"]:
            u,v=cfg["uv"][i]
            cubes=[{"origin":list(o),"size":list(s),"uv":[u+du,v+dv]} for o,s,(du,dv) in cfg["cubes"]]
            geos.append({"description":desc(f"geometry.katt.{a}{i}"),
                         "bones":[{"name":cfg["bone"],
                                   "pivot":PIVOTS[cfg["bone"]],"cubes":cubes}]})
    g["minecraft:geometry"]=geos
    json.dump(g,open(p,"w"),indent=2)
    return len(geos)

# ---------------------------------------------------------------- textur
def paint_accessories():
    for cid in ("misty","hazel","mocha","snow"):
        p=f"{RP}/textures/entity/{cid}.png"; w,h,px=read_png(p)
        def rect(x0,y0,ww,hh,c):
            for y in range(y0,y0+hh):
                for x in range(x0,x0+ww):
                    if 0<=x<w and 0<=y<h: px[y][x]=c
        for a,cfg in ACC.items():
            for i,(slug,col) in cfg["colors"].items():
                u,v=cfg["uv"][i]
                for (o,s,(du,dv)) in cfg["cubes"]:
                    fw,fh=uv_footprint(s)
                    rect(u+du,v+dv,fw,fh,sh(col,1.0))
                    rect(u+du,v+dv,fw,1,sh(col,1.2))          # ljus ovankant
                    rect(u+du,v+dv+fh-1,fw,1,sh(col,0.68))    # mörk underkant
                    for x in range(u+du,u+du+fw):
                        if (x-u-du)%4==0: rect(x,v+dv,1,fh,sh(col,0.86))   # tyg-/läderstruktur
        write_png(p,w,h,px)

# ---------------------------------------------------------------- ikoner
def icon(a,col,path):
    S=16; T=(0,0,0,0); px=[[T]*S for _ in range(S)]
    def sp(x,y,c):
        if 0<=x<S and 0<=y<S: px[y][x]=c
    if a=="glasogon":
        for x in range(1,15): sp(x,7,sh(col,0.8)); sp(x,8,sh(col,1.0)); sp(x,9,sh(col,0.8))
        for y in range(6,11):
            for x in (2,3,4,11,12,13): sp(x,y,sh(col,1.0))
        for y in range(7,10):
            for x in (3,12): sp(x,y,(150,200,230,255))
    elif a=="mantel":
        for y in range(3,14):
            wsp=1 if y<5 else 0
            for x in range(3+wsp,13-wsp): sp(x,y,sh(col,1.0))
        for x in range(4,12): sp(x,3,sh(col,1.2))
        for y in range(3,14): sp(3,y,sh(col,0.7)); sp(12,y,sh(col,0.7))
        for x in range(3,13):
            if x%3==0:
                for y in range(5,14): sp(x,y,sh(col,0.86))
    elif a=="vagn":
        for y in range(5,11):
            for x in range(2,14): sp(x,y,sh(col,1.0))
        for x in range(2,14): sp(x,5,sh(col,1.22))
        for x in range(2,14): sp(x,10,sh(col,0.7))
        for x in range(3,13):
            if x%3==0:
                for y in range(6,10): sp(x,y,sh(col,0.86))
        for (wx) in (4,11):                      # hjul
            for y in range(11,15):
                for x in range(wx-1,wx+2): sp(x,y,(72,60,48,255))
            sp(wx,12,(140,124,100,255)); sp(wx,13,(140,124,100,255))
    elif a=="tossor":
        for (bx,by) in ((2,4),(9,4),(2,10),(9,10)):      # fyra små tossor
            for y in range(by,by+4):
                for x in range(bx,bx+5):
                    if y==by and x in (bx,bx+4): continue
                    sp(x,y,sh(col,1.0))
            for x in range(bx+1,bx+4): sp(x,by,sh(col,1.2))
            for x in range(bx,bx+5): sp(x,by+3,sh(col,0.68))
    else:
        for y in range(5,12):
            for x in range(3,13): sp(x,y,sh(col,1.0))
        for x in range(3,13): sp(x,5,sh(col,1.2)); sp(x,11,sh(col,0.7))
    write_png(path,S,S,px)

def icon_treat():
    """Kattgodis: liten fiskformad godbit."""
    S=16; T=(0,0,0,0); px=[[T]*S for _ in range(S)]
    BODY=(226,150,92,255); DARK=(186,116,66,255); LIGHT=(242,190,140,255)
    def sp(x,y,c):
        if 0<=x<S and 0<=y<S: px[y][x]=c
    for y in range(6,11):
        for x in range(4,12): sp(x,y,BODY)
    for x in range(4,12): sp(x,6,LIGHT); sp(x,10,DARK)
    for k in range(3):                      # stjärtfena
        for y in range(6+k,11-k): sp(12+k,y,BODY)
    sp(6,8,DARK)                            # öga
    for x in range(5,11):
        if x%2==0: sp(x,8,DARK)             # mönster
    write_png(f"{RP}/textures/items/pc_godis.png",S,S,px)

# ---------------------------------------------------------------- allt övrigt
def build_rest():
    # render controllers
    rcs={"controller.render.katt":{"geometry":"Geometry.default",
         "materials":[{"*":"Material.default"}],"textures":["Texture.default"]}}
    for a,cfg in ACC.items():
        arr=["Geometry.empty"]+[f"Geometry.{a}{i}" for i in sorted(cfg["colors"])]
        rcs[f"controller.render.katt_{a}"]={
          "arrays":{"geometries":{f"Array.{a}":arr}},
          "geometry":f"Array.{a}[query.property('mjau:{a}')]",
          "materials":[{"*":"Material.default"}],"textures":["Texture.default"]}
    json.dump({"format_version":"1.10.0","render_controllers":rcs},
              open(f"{RP}/render_controllers/katt.render_controllers.json","w"),indent=2)

    gmap={"default":"geometry.katt","empty":"geometry.katt.empty"}
    for a,cfg in ACC.items():
        for i in cfg["colors"]: gmap[f"{a}{i}"]=f"geometry.katt.{a}{i}"
    # SÄKERHETSFIX 2026-08-13: loopen tog ALLA RP-entiteter och tvingade på dem
    # kattgeometrin — vakthunden (varg-geometri, varg-textur) renderades som en
    # katt. Bara klädbara katter ska röras; de känns igen på att deras
    # BP-motsvarighet har mjau:saddled (dvs. kan bära plagg).
    _katter=set()
    for bf in glob.glob(f"{BP}/entities/*.json"):
        be=json.load(open(bf))["minecraft:entity"]
        if "mjau:saddled" in be.get("component_groups",{}):
            _katter.add(be["description"]["identifier"])
    for f in glob.glob(f"{RP}/entity/*.json"):
        d=json.load(open(f)); desc=d["minecraft:client_entity"]["description"]
        if desc.get("identifier") not in _katter: continue   # t.ex. vakthunden
        desc["geometry"]=gmap
        desc["render_controllers"]=["controller.render.katt"]+[f"controller.render.katt_{a}" for a in ACC]
        # animationer: gångcykel, svanssvaj, huvudet följer spelaren, hopkurad sittpose
        desc["animations"]={
            "walk":"animation.katt.walk", "look":"animation.katt.look",
            "tail":"animation.katt.tail", "sit":"animation.katt.sit",
            "ctrl":"controller.animation.katt.move"}
        desc["animations"]["sova"]="animation.katt.sova"
        desc["sound_effects"]={"purr":"mob.cat.purr"}
        desc["particle_effects"]={"hjarta":"minecraft:heart_particle"}
        desc["scripts"]={"animate":["ctrl"]}
        json.dump(d,open(f,"w"),indent=2)

    # föremål, ikoner, recept, språk
    # SÄKERHETSFIX 2026-08-13: raderade tidigare ALLA items/*.json och
    # recipes/*.json — även möblernas (kattbadd, matskal, fiskdamm ...) som
    # ägs av build_blocks.py. Ett fristående körning slog alltså ut åtta
    # orelaterade recept. Nu raderas bara det HÄR skriptet självt återskapar.
    _mina = {f"{a}_{slug}" for a, cfg in ACC.items() for slug, _ in cfg["colors"].values()} | {"godis"}
    for d_ in (f"{BP}/items", f"{BP}/recipes"):
        for f in glob.glob(f"{d_}/*.json"):
            if os.path.splitext(os.path.basename(f))[0] in _mina: os.remove(f)
    for f in glob.glob(f"{RP}/textures/items/pc_*.png"):
        if not any(f.endswith(f"pc_{c}.png") for c in ("misty","hazel","mocha","snow")): os.remove(f)
    it=json.load(open(f"{RP}/textures/item_texture.json"))
    it["texture_data"]={k:v for k,v in it["texture_data"].items()
                        if k in ("pc_misty","pc_hazel","pc_mocha","pc_snow")}
    lang=[]
    for a,cfg in ACC.items():
        for i,(slug,col) in cfg["colors"].items():
            ident=f"mjau:{a}_{slug}"; tex=f"pc_{a}_{slug}"
            icon(a,col,f"{RP}/textures/items/{tex}.png")
            it["texture_data"][tex]={"textures":f"textures/items/{tex}"}
            nm=f"{cfg['label']} ({cfg['names'][i]})"
            json.dump({"format_version":"1.20.50","minecraft:item":{"description":{"identifier":ident,
              "menu_category":{"category":"equipment"}},"components":{"minecraft:icon":{"texture":tex},
              "minecraft:display_name":{"value":nm},"minecraft:max_stack_size":1}}},
              open(f"{BP}/items/{a}_{slug}.json","w"),indent=2)
            r=cfg["recipe"](cfg["mats"][i])
            json.dump({"format_version":"1.20.10","minecraft:recipe_shaped":{
              "description":{"identifier":ident},"tags":["crafting_table"],
              "pattern":r["pattern"],"key":r["key"],"unlock":r["unlock"],"result":{"item":ident}}},
              open(f"{BP}/recipes/{a}_{slug}.json","w"),indent=2)
            lang.append(f"item.{ident}={nm}")
    json.dump(it,open(f"{RP}/textures/item_texture.json","w"),indent=2)

    # föremål UTAN geometri (inget plagg) — t.ex. kattgodis
    icon_treat()
    it["texture_data"]["pc_godis"]={"textures":"textures/items/pc_godis"}
    json.dump({"format_version":"1.20.50","minecraft:item":{"description":{"identifier":"mjau:godis",
      "menu_category":{"category":"nature"}},"components":{"minecraft:icon":{"texture":"pc_godis"},
      "minecraft:display_name":{"value":"Cat Treat"},"minecraft:max_stack_size":16}}},
      open(f"{BP}/items/godis.json","w"),indent=2)
    json.dump({"format_version":"1.20.10","minecraft:recipe_shaped":{
      "description":{"identifier":"mjau:godis"},"tags":["crafting_table"],
      "pattern":["FW"],"key":{"F":{"item":"minecraft:cod"},"W":{"item":"minecraft:wheat"}},
      "unlock":[{"item":"minecraft:cod"}],"result":{"item":"mjau:godis","count":3}}},
      open(f"{BP}/recipes/godis.json","w"),indent=2)
    lang.append("item.mjau:godis=Cat Treat")
    # Prompten som visas när man riktar mot katten med ett plagg i handen.
    # Utan den här raden visar spelet nyckeln i klartext ("action.interact.equip").
    lang.append("action.interact.mjau_equip=Put on")
    lang.append("action.interact.ride=Ride")          # visas när man sitter upp
    lang.append("action.interact.mount=Mount")
    # Bedrock bygger avstigningsprompten som action.hint.exit.<entity-id>; utan
    # egna nycklar visas den råa nyckeln på skärmen.
    # SÄKERHETSFIX 2026-08-13: listan var hårdkodad till de fyra grundkatterna,
    # så de hemliga (midnight, aurora) och spökkatten tappade sina hint-rader
    # varje gång generatorn kördes. Härleds nu ur BP-filerna i stället.
    for _bf in sorted(glob.glob(f"{BP}/entities/*.json")):
        _be=json.load(open(_bf))["minecraft:entity"]
        if "mjau:saddled" not in _be.get("component_groups",{}): continue
        c=_be["description"]["identifier"].split(":")[-1]
        lang.append(f"action.hint.exit.mjau:{c}=Dismount")
        lang.append(f"action.hint.exit.{c}=Dismount")
    json.dump(it,open(f"{RP}/textures/item_texture.json","w"),indent=2)  # skrivs om: godis-ikonen tillkom efter första dumpen

    # entiteter: properties, events, interaktioner
    for f in sorted(glob.glob(f"{BP}/entities/*.json")):
        d=json.load(open(f)); e=d["minecraft:entity"]
        if "component_groups" not in e: continue   # inte en klädbar katt (t.ex. vakthund.json)
        g=e["component_groups"]; ev=e["events"]
        # client_sync ÄR NÖDVÄNDIG: utan den finns propertyn bara på servern och
        # render controllers (som körs på klienten) kan inte läsa query.property
        # → plaggen sätts på men syns aldrig. Ridning fungerade ändå, eftersom den
        # kommer från en komponentgrupp och inte från en property.
        e["description"]["properties"]={
            f"mjau:{a}": {"type":"int","range":[0,len(cfg["colors"])],"default":0,"client_sync":True}
            for a,cfg in ACC.items()}
        # mjau:tam gor tamjningen OBSERVERBAR server-side (is_tamed syns inte i
        # selektorer). Ingen render controller laser den -> ingen client_sync.
        e["description"]["properties"]["mjau:tam"]={"type":"int","range":[0,1],"default":0}
        # humor: 0=hungrig (hängande svans), 1=neutral, 2=glad (hög svans).
        # Godis höjer, timern sänker. client_sync: svans-animationen läser den.
        e["description"]["properties"]["mjau:humor"]={"type":"int","range":[0,2],"default":1,"client_sync":True}
        for k in [k for k in ev if k.startswith("mjau:on_") and k not in ("mjau:on_tame",)]: del ev[k]
        g.pop("mjau:vagnsplats",None)   # gammal grupp: rideable bor numera bara i mjau:saddled
        inter=[]
        def entry(item,event,sound):
            return {"on_interact":{"filters":{"all_of":[
                      {"test":"is_family","subject":"other","value":"player"},
                      {"test":"is_owner","subject":"other"},
                      {"test":"has_equipment","domain":"hand","subject":"other","value":item}]},
                    "event":event,"target":"self"},
                    "use_item":True,"play_sounds":sound,"interact_text":"action.interact.mjau_equip"}
        for a,cfg in ACC.items():
            for i,(slug,col) in cfg["colors"].items():
                evn=f"mjau:on_{a}_{i}"
                ev[evn]={"set_property":{f"mjau:{a}":i}}
                if a=="rustning":
                    # inte bara kosmetik: pansar ger liv efter nivå — järn 20,
                    # guld 22, diamant 25, netherit 30 hjärtan (bas 10). Byte av
                    # rustning tar bort de andra nivågrupperna, annars avgör
                    # gruppernas tilläggning vilken hälsa som vinner.
                    _hp={1:40,2:44,3:50,4:60}[i]
                    g[f"mjau:armored_{i}"]={"minecraft:health":{"value":_hp,"max":_hp}}
                    # health-gruppen höjer bara MAX — nuvarande hälsa följer inte
                    # med (uppmätt i live-testet). Låt påsättningen läka katten
                    # fullt via spell_effects, annars är extra-hjärtana tomma.
                    g["mjau:pansarkur"]={"minecraft:spell_effects":{"add_effects":[
                        {"effect":"instant_health","duration":1,"amplifier":5,
                         "display_on_screen_animation":False}]}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append("mjau:pansarkur")
                    ev[evn].setdefault("remove",{}).setdefault("component_groups",[]).append("mjau:pansarkur")
                    # legacy: <=2.6.1 sparade "mjau:armored" i världsdata — behåll
                    # definitionen (annars okänd aktör vid uppgradering) men låt
                    # varje rustningsbyte städa bort den
                    g["mjau:armored"]={"minecraft:health":{"value":30,"max":30}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append(f"mjau:armored_{i}")
                    ev[evn].setdefault("remove",{}).setdefault("component_groups",[]).extend(
                        [f"mjau:armored_{j}" for j in (1,2,3,4) if j!=i]+["mjau:armored"])
                if a=="mantel":
                    # SUPERKRAFTER (speltest-önskemål): manteln är inte bara stil —
                    # en ridd katt blir snabbare och hoppar högre (samma charged-
                    # jump-mekanik som redan bär katten upp fyrkullen/kattbanan,
                    # bara starkare). Alla fyra färger ger samma kraft — manteln
                    # är kraften, färgen är bara stilen. Ingen mutual exclusion
                    # behövs mellan färgerna (samma grupp läggs bara till igen).
                    g["mjau:supermantel"]={
                        "minecraft:movement":{"value":0.68},
                        "minecraft:horse.jump_strength":{"value":1.8}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append("mjau:supermantel")
                if a in ("vingar","batvingar"):
                    # VINGKRAFT (speltest-önskemål "bygg alla"): aldrig fallskada,
                    # oavsett höjd — utökar samma damage_sensor-knep som redan gör
                    # sadlade/förspända katter fallskadefria, fast permanent.
                    g["mjau:vingkraft"]={"minecraft:damage_sensor":{"triggers":[
                        {"cause":"fall","deals_damage":False}]}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append("mjau:vingkraft")
                if a=="doktorsrock":
                    # LÄKARROCKEN: konstant sakta läkning (regeneration, mycket
                    # lång varaktighet i praktiken permanent).
                    g["mjau:lakarrock"]={"minecraft:spell_effects":{"add_effects":[
                        {"effect":"regeneration","duration":999999,"amplifier":0,
                         "display_on_screen_animation":False}]}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append("mjau:lakarrock")
                if a=="krona":
                    # KRONAN: alltid synlig (glowing genom väggar) — kungligt och
                    # lätt att hitta katten i mörkret.
                    g["mjau:kunglig_glod"]={"minecraft:spell_effects":{"add_effects":[
                        {"effect":"glowing","duration":999999,"amplifier":0,
                         "display_on_screen_animation":False}]}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append("mjau:kunglig_glod")
                # ÖVRIGA SUPERKRAFTER (speltest-önskemål: "jag vill fortsätta" —
                # samma effektmönster (spell_effects, mycket lång varaktighet i
                # praktiken permanent), en distinkt vanilla-effekt per plagg.
                _EXTRA_POWERS={
                    "keps":("mjau:kepskraft","jump_boost"),
                    "halsduk":("mjau:halsdukvarme","fire_resistance"),
                    "glasogon":("mjau:glasogonskarpa","resistance"),
                    "tossor":("mjau:tossorfart","speed"),
                    "halsband":("mjau:halsbandssken","absorption"),
                    "rosett":("mjau:rosettmod","strength"),
                    "horn":("mjau:hornsvavning","slow_falling"),
                    "haxhatt":("mjau:haxbrygd","water_breathing"),
                    "tomteluva":("mjau:tomtegava","health_boost"),
                }
                if a in _EXTRA_POWERS:
                    _grp,_eff=_EXTRA_POWERS[a]
                    g[_grp]={"minecraft:spell_effects":{"add_effects":[
                        {"effect":_eff,"duration":999999,"amplifier":0,
                         "display_on_screen_animation":False}]}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append(_grp)
                if cfg.get("rideable"):
                    # SADEL: ryttare på ryggen. Utesluter vagnläget — två aktiva
                    # rideable-definitioner ger odefinierat beteende.
                    g["mjau:saddled"]["minecraft:rideable"]={
                        "seat_count":1,"family_types":["player"],
                        "interact_text":"action.interact.ride",
                        "seats":[{"position":[0.0,0.562,-0.22]}]}
                    ev[evn]["add"]={"component_groups":["mjau:saddled"]}
                    # jagar + fri måste av när riddjuret sätts — annars styr
                    # katten sig själv under ryttaren (sköts av statisk check)
                    ev[evn]["remove"]={"component_groups":["mjau:sittable","mjau:carted","mjau:jagar","mjau:fri"]}
                if cfg.get("seats"):
                    # VAGN: seat 0 I vagnen (styrbar som en släde), seat 1 på ryggen
                    # för en vän. Egen grupp med egna styr-/lastkomponenter; sadel-
                    # och vagnläget tar bort varandra så bara EN rideable är aktiv.
                    sad=g["mjau:saddled"]
                    g["mjau:carted"]={
                        "minecraft:is_saddled":{},
                        "minecraft:input_ground_controlled":{},
                        "minecraft:movement":dict(sad.get("minecraft:movement",{"value":0.5})),
                        "minecraft:horse.jump_strength":dict(sad.get("minecraft:horse.jump_strength",{"value":1.2})),
                        "minecraft:can_power_jump":{},
                        "minecraft:is_chested":{},
                        "minecraft:inventory":{"container_type":"horse",
                                               "inventory_size":15,"private":False},
                        "minecraft:rideable":{
                            "seat_count":2,"family_types":["player"],
                            "interact_text":"action.interact.ride",
                            "seats":[{"position":cfg["seats"][0]},{"position":cfg["seats"][1]}]}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append("mjau:carted")
                    ev[evn].setdefault("remove",{}).setdefault("component_groups",[]).extend(["mjau:sittable","mjau:saddled","mjau:jagar","mjau:fri"])
                inter.append(entry(f"mjau:{a}_{slug}",evn,cfg["sound"]))   # namnrymd krävs för EGNA föremål
        inter.append(entry("saddle","mjau:on_sadel_1","saddle"))
        # SPINNA/MATA: godis på tam katt höjer humöret
        inter.append(entry("mjau:godis","mjau:on_matad","eat"))
        ev["mjau:on_matad"]={"set_property":{"mjau:humor":2}}
        # humöret sjunker med tiden (ordningen 1->0 före 2->1 hindrar kaskad)
        e["components"]["minecraft:timer"]={"time":[180,360],"looping":True,
            "time_down_event":{"event":"mjau:hungrigare","target":"self"}}
        ev["mjau:hungrigare"]={"sequence":[
            {"filters":{"test":"int_property","domain":"mjau:humor","value":1},
             "set_property":{"mjau:humor":0}},
            {"filters":{"test":"int_property","domain":"mjau:humor","value":2},
             "set_property":{"mjau:humor":1}}]}
        # (behavior.nap togs bort i 2.6.1 — katterna "bara låg och sov";
        #  statisk check förbjuder den, så återinför den inte här)
        # KATTFISKE: sadlad/förspänd katt i vatten fångar fisk
        for _rg in ("mjau:saddled","mjau:carted"):
            # RIDDJURET tar fallskadan i Bedrock — nolla 'fall' så katten
            # inte dör när ryttaren hoppar ner (2.6.1-fix)
            g[_rg]["minecraft:damage_sensor"]={"triggers":[
                {"cause":"fall","deals_damage":False}]}
            g[_rg]["minecraft:spawn_entity"]={"entities":[
                {"min_wait_time":12,"max_wait_time":40,"spawn_item":"minecraft:cod",
                 "spawn_sound":"splash","filters":{"test":"in_water","value":True}}]}
        # SKATTLETANDE: ryggsäckskatter gräver fram småsaker (sällsynt en diamant)
        g["mjau:skattletare"]={"minecraft:spawn_entity":{"entities":[
            {"min_wait_time":300,"max_wait_time":900,"spawn_item":"minecraft:string","spawn_sound":"drop.slot"},
            {"min_wait_time":420,"max_wait_time":1200,"spawn_item":"minecraft:feather","spawn_sound":"drop.slot"},
            {"min_wait_time":2400,"max_wait_time":4800,"spawn_item":"minecraft:diamond","spawn_sound":"random.levelup"}]}}
        for _i in (1,2,3):
            _evn=f"mjau:on_ryggsack_{_i}"
            if _evn in ev:
                ev[_evn].setdefault("add",{}).setdefault("component_groups",[]).append("mjau:skattletare")
        # KATTUNGAR föds ibland med rosett
        _born=ev["minecraft:entity_born"]
        _born.setdefault("sequence",[]).append({"randomize":[
            {"weight":60},
            {"weight":10,"set_property":{"mjau:rosett":1}},
            {"weight":10,"set_property":{"mjau:rosett":2}},
            {"weight":10,"set_property":{"mjau:rosett":3}},
            {"weight":10,"set_property":{"mjau:rosett":4}}]})
        # ...och mer sällan med ett halsband (speltest-önskemål: "bygg alla" —
        # kitten-trait-idén, varje kull lite unik utöver bara namn+antal)
        _born.setdefault("sequence",[]).append({"randomize":[
            {"weight":88},
            {"weight":4,"set_property":{"mjau:halsband":1}},
            {"weight":4,"set_property":{"mjau:halsband":2}},
            {"weight":4,"set_property":{"mjau:halsband":3}}]})
        g["mjau:tamed"]["minecraft:interact"]={"interactions":inter}
        json.dump(d,open(f,"w"),indent=2)

    # Bedrock läser INTE en .lang-fil utan texts/languages.json som deklarerar
    # vilka språk paketet har. Saknas den faller allt tillbaka på råa nycklar —
    # och våra identifierare är svenska (sadel_brun, keps_cyan, ryggsack...), så
    # spelaren fick svenska namn och råa hint-nycklar trots engelsk lang-fil.
    # sv_SE finns med och innehåller SAMMA engelska text, så en svenskspråkig
    # konsol inte hamnar i fallback igen.
    for pack in ("PurrfectCompanions_BP","PurrfectCompanions_RP"):
        json.dump(["en_US","sv_SE"],open(f"{BASE}/{pack}/texts/languages.json","w"))
    # SÄKERHETSFIX 2026-08-13: sv_SE.lang KOPIERADES tidigare rakt av från
    # en_US, vilket raderade ALLA svenska rader skriptet inte äger — hela
    # achievement-listan (Trippelskatten, Kattbanemästaren ...) blev engelsk.
    # Nu behandlas filerna var för sig: bara plagg-/hint-raderna byts ut,
    # allt annat står kvar som det är. (Plaggnamnen är engelska även i
    # sv_SE — familjevarianten döper om dem via variants.private.json.)
    for pack in ("PurrfectCompanions_BP","PurrfectCompanions_RP"):
        for spr in ("en_US","sv_SE"):
            lp=f"{BASE}/{pack}/texts/{spr}.lang"
            if not os.path.exists(lp): shutil.copyfile(f"{BASE}/{pack}/texts/en_US.lang", lp)
            keep=[l for l in open(lp).read().rstrip("\n").split("\n")
                  if not l.startswith(("item.mjau:","action."))]
            open(lp,"w").write("\n".join(dict.fromkeys(keep+lang))+"\n")
    return len(lang), len(inter)

if __name__ == "__main__":
    n = build_geometry()
    paint_accessories()
    items, inters = build_rest()
    print(f"{len(ACC)} plagg · {n} geometrier · {items} föremål · {inters} interaktioner")
    for a,cfg in ACC.items():
        print(f"  {a:9s} {len(cfg['colors'])} färger  ({cfg['label']})")
