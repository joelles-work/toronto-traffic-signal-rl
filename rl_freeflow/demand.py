"""Generate paired train/dev realizations from frozen observed counts only."""
import csv
import gzip
import json
import os
from pathlib import Path
import random
import xml.etree.ElementTree as ET
from .freeze import ASSETS, PILOT, verify

DEST={'n':{'r':'w','t':'s','l':'e'},'s':{'r':'e','t':'n','l':'w'},
      'e':{'r':'n','t':'w','l':'s'},'w':{'r':'s','t':'e','l':'n'}}


def generate(split,seed):
    if split not in ('train','dev'):
        raise ValueError('Only train and dev are available; test evaluation is sealed.')
    verify()
    target=PILOT/'demand'/f'{split}_{seed}.rou.xml.gz'
    audit_path=target.with_suffix('.audit.json')
    if target.exists() and audit_path.exists():
        return target,json.loads(audit_path.read_text())
    meta=json.loads((ASSETS/'provenance.json').read_text())
    manifest=json.loads((ASSETS/'split_manifest.json').read_text())['splits'][split]
    with (ASSETS/f'{split}.csv').open(newline='') as f:
        rows=list(csv.DictReader(f))
    rng=random.Random(seed)
    arrivals=[]
    for interval,row in enumerate(rows):
        for arm in DEST:
            for kind in ('cars','truck','bus'):
                for move in ('r','t','l'):
                    for _ in range(int(row[f'{arm}_appr_{kind}_{move}'])):
                        arrivals.append((interval*900+rng.random()*900,arm,DEST[arm][move],kind))
    arrivals.sort()
    result=ET.Element('routes')
    for vt in ET.parse(ASSETS/'types.rou.xml').getroot():
        result.append(vt)
    elements=[]
    vehicle_arms={}
    for i,(depart,arm,dest,kind) in enumerate(arrivals):
        pid=f'v{i}'
        vehicle_arms[pid]=arm
        vehicle=ET.Element('vehicle',id=pid,type=kind,depart=f'{depart:.6f}',departLane='best')
        ET.SubElement(vehicle,'route',edges=meta['route_pairs'][f'{arm}_{dest}'])
        elements.append(vehicle)
    rng=random.Random(seed+100000)
    ped_counts={arm:0 for arm in 'nsew'}
    for interval,row in enumerate(rows):
        for arm in 'nsew':
            count=int(row[f'{arm}_appr_peds'])
            ped_counts[arm]+=count
            directions=[i%2 for i in range(count)]
            if rng.randrange(2):
                directions=[1-d for d in directions]
            rng.shuffle(directions)
            for i,direction in enumerate(directions):
                a,b=meta['incoming'][arm][-1],meta['outgoing'][arm][0]
                if direction:
                    a,b=b,a
                person=ET.Element('person',id=f'ped_{arm}_{interval}_{i}',type='pedestrian',
                    depart=f'{interval*900+rng.random()*900:.6f}',departPos='0.5' if direction else '-0.5')
                ET.SubElement(person,'walk',{'from':a,'to':b,'arrivalPos':'-0.5' if direction else '0.5'})
                elements.append(person)
    assert len(arrivals)==manifest['vehicles'] and sum(ped_counts.values())==manifest['pedestrians']
    for e in sorted(elements,key=lambda e:float(e.get('depart'))):
        result.append(e)
    target.parent.mkdir(parents=True,exist_ok=True)
    ET.indent(result)
    temporary=target.with_name(target.name+f'.{os.getpid()}.tmp')
    with gzip.open(temporary,'wb') as f:
        ET.ElementTree(result).write(f,encoding='utf-8',xml_declaration=True)
    os.replace(temporary,target)
    audit={'split':split,'seed':seed,'vehicles':len(arrivals),'pedestrians':sum(ped_counts.values()),
        'pedestrians_by_leg':ped_counts,'vehicle_arms':vehicle_arms,'duration':len(rows)*900,
        'source_sha256':manifest['sha256']}
    temporary_audit=audit_path.with_name(audit_path.name+f'.{os.getpid()}.tmp')
    temporary_audit.write_text(json.dumps(audit,indent=2))
    os.replace(temporary_audit,audit_path)
    return target,audit
