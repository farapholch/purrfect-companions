"""Authored furniture actions; called by build_accessories.py. Units are pixels/degrees."""
import json
from copy import deepcopy
from pathlib import Path


def build(rp):
    rp=Path(rp)
    path=rp/'animations/katt.animation.json'
    doc=json.loads(path.read_text()); anim=doc['animations']
    rest=deepcopy(anim['animation.katt.sova'])
    rest['bones']['tail']['position']=[0,-2.2,0]
    # A slow breath lifts chest, neck and tail together; attached clothing follows.
    for bone,amount in [('body',.16),('head',.10),('tail',.16)]:
        base=rest['bones'][bone]['position']
        rest['bones'][bone]['position']={str(t):[base[0],base[1]+dy,base[2]]
            for t,dy in [(0,0),(1.5,amount),(3,0),(4.5,amount),(6,0)]}
    anim['animation.katt.korgvila']=rest
    settle=deepcopy(rest);settle['loop']='hold_on_last_frame';settle['animation_length']=1.2
    settle.pop('sound_effects',None)
    for bone,channels in settle['bones'].items():
        for channel,value in list(channels.items()):
            end=value['0'] if isinstance(value,dict) else value
            start=[0,0,0]
            mid=[v*.9 for v in end]
            if bone=='head' and channel=='rotation':mid=[18,8,-5]
            channels[channel]={'0':start,'0.7':mid,'1.2':end}
    anim['animation.katt.korglagg']=settle
    for kind in ('spa','tv'):
        action=deepcopy(anim['animation.katt.sit'])
        action.pop('particle_effects',None);action.pop('sound_effects',None)
        action['animation_length']=4
        bones=action['bones']
        if kind=='spa':
            # Front right paw lifts toward the lowered muzzle, twice per wash.
            bones['leg2']['rotation']={'0':[-6,0,0],'0.7':[95,0,12],
                '1.2':[106,0,12],'1.5':[95,0,12],'1.9':[106,0,12],
                '2.3':[95,0,12],'3':[-6,0,0],'4':[-6,0,0]}
            bones['head']['rotation']={'0':[16,0,0],'0.7':[-18,12,-5],
                '1.2':[-24,12,-5],'1.5':[-18,12,-5],'1.9':[-24,12,-5],
                '2.3':[-18,12,-5],'3':[16,0,0],'4':[16,0,0]}
        else:
            # Small, unhurried head turns keep the screen inside the field of view.
            bones['head']['rotation']={'0':[8,-10,0],'1':[5,0,-2],
                '2':[8,10,0],'3':[5,0,2],'4':[8,-10,0]}
        anim['animation.katt.'+kind]=action
    # Lower the muzzle toward the bowl and lap; feet remain on the ground.
    anim['animation.katt.fountain']={'loop':True,'animation_length':2,'bones':{
        'head':{'position':[0,-2,-3], 'rotation':{
            '0':[28,0,0],'.25':[33,0,0],'.5':[28,0,0],'.75':[33,0,0],
            '1':[28,0,0],'1.25':[33,0,0],'1.5':[28,0,0],'1.75':[33,0,0],'2':[28,0,0]}},
        'tail':{'rotation':{'0':[0,0,-4],'1':[0,0,4],'2':[0,0,-4]}}}}
    # Alternate front paws over the low sisal ramp; clothes inherit limb motion.
    scratch={'loop':True,'animation_length':1,'bones':{}}
    for leg,angles in [('leg2',[60,85,60,60,60]),('leg3',[60,60,60,85,60])]:
        scratch['bones'][leg]={'position':[0,0,-3.8],
            'rotation':{str(i*.25):[a,0,0] for i,a in enumerate(angles)}}
    scratch['bones']['head']={'rotation':{'0':[12,0,0],'.25':[16,0,0],'.5':[12,0,0],'.75':[16,0,0],'1':[12,0,0]}}
    scratch['bones']['tail']={'rotation':{'0':[0,0,-8],'.5':[0,0,8],'1':[0,0,-8]}}
    anim['animation.katt.scratch']=scratch
    watch=deepcopy(anim['animation.katt.tv']);watch['animation_length']=6
    watch['bones']['head']['rotation']={'0':[5,-18,0],'1.5':[-4,0,-3],
        '3':[5,18,0],'4.5':[10,0,3],'6':[5,-18,0]}
    watch['bones']['tail']['rotation']={'0':[0,0,-8],'3':[0,0,8],'6':[0,0,-8]}
    anim['animation.katt.window']=watch
    lower=deepcopy(settle)
    for bone,channels in lower['bones'].items():
        for channel,value in channels.items():
            first=watch['bones'].get(bone,{}).get(channel,[0,0,0])
            value['0']=first.get('0',[0,0,0]) if isinstance(first,dict) else first
            value['0.7']=[(a+b)*.5 for a,b in zip(value['0'],value['1.2'])]
    anim['animation.katt.windowlagg']=lower
    path.write_text(json.dumps(doc,indent=2)+'\n')
    # Small, short-lived sisal fibres use the existing particle sprite.
    dust=json.loads((rp/'particles/blad_gron.json').read_text())
    fx=dust['particle_effect'];fx['description']['identifier']='mjau:sisal_dust'
    c=fx['components'];c['minecraft:emitter_rate_instant']['num_particles']=3
    c['minecraft:particle_lifetime_expression']['max_lifetime']=.35
    c['minecraft:particle_initial_speed']=.18
    c['minecraft:particle_appearance_billboard']['size']=[.025,.012]
    c['minecraft:particle_appearance_tinting']['color']=[.84,.76,.56,1]
    (rp/'particles/sisal_dust.json').write_text(json.dumps(dust,indent=2)+'\n')
    path=rp/'animation_controllers/katt.animation_controllers.json'
    doc=json.loads(path.read_text())
    states=doc['animation_controllers']['controller.animation.katt.move']['states']
    for name,state in list(states.items()):
        if name.startswith('furniture_'):del states[name];continue
        state['transitions']=[{dest:f"q.property('mjau:mobel') == {mode} && q.modified_move_speed <= 0.02"}
            for mode,dest in [(5,'furniture_settle'),(6,'furniture_spa'),(7,'furniture_tv'),(8,'furniture_scratch'),(11,'furniture_window'),(12,'furniture_window_settle'),(14,'furniture_fountain')]]+[
            t for t in state['transitions'] if not any(k.startswith('furniture_') for k in t)]
    for name,action,mode in [('settle','korglagg',5),('sleep','korgvila',5),('spa','spa',6),('tv','tv',7),('scratch','scratch',8),('window','window',11),('window_settle','windowlagg',12),('window_sleep','korgvila',12),('fountain','fountain',14)]:
        state={'blend_transition':.3,'animations':[action],
            'transitions':[{'walking':'q.modified_move_speed > 0.12'},
                           {'standing':f"q.property('mjau:mobel') != {mode}"}]}
        if name=='settle':state['transitions'].append({'furniture_sleep':'q.any_animation_finished'})
        if name=='window_settle':state['transitions'].append({'furniture_window_sleep':'q.any_animation_finished'})
        states['furniture_'+name]=state
    path.write_text(json.dumps(doc,indent=2)+'\n')
