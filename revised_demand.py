"""Observed dev demand on the revised geometry, without touching test periods."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent


def write_routes(seed,target):
    model=ROOT/'models/eglinton_danforth'
    meta=json.loads((model/'provenance.json').read_text())
    manifest=json.loads((ROOT/'data/split_manifest.json').read_text())
    data=ROOT/'data/dev.csv'
    assert hashlib.sha256(data.read_bytes()).hexdigest()==manifest['splits']['dev']['sha256']
    old=ET.parse(ROOT/f'results/baseline_dev/seed_{seed}/routes.rou.xml').getroot()
    result=ET.Element('routes')
    for vt in old.findall('vType'):
        result.append(vt)
    # A constant walk speed makes the clearance assumption explicit and testable.
    ET.SubElement(result,'vType',id='pedestrian',vClass='pedestrian',maxSpeed='1.2',speedFactor='1',speedDev='0')
    elements=[]
    vehicle_counts={}
    for v in old.findall('vehicle'):
        route=v.find('route').get('edges').split()
        a,b=route[0][0],route[-1][0]
        attrs=dict(v.attrib)
        attrs['departLane']='best'
        new=ET.Element('vehicle',attrs)
        ET.SubElement(new,'route',edges=meta['route_pairs'][f'{a}_{b}'])
        elements.append(new)
        vehicle_counts[f'{a}_{b}']=vehicle_counts.get(f'{a}_{b}',0)+1
    rng=random.Random(seed+100000)
    ped_counts={a:0 for a in 'nsew'}
    direction_counts={a:[0,0] for a in 'nsew'}
    with data.open(newline='') as f:
        rows=list(csv.DictReader(f))
    for interval,row in enumerate(rows):
        for arm in 'nsew':
            count=int(row[f'{arm}_appr_peds'])
            ped_counts[arm]+=count
            directions=[i%2 for i in range(count)]
            if rng.randrange(2):
                directions=[1-d for d in directions]
            rng.shuffle(directions)
            for i,direction in enumerate(directions):
                incoming=meta['incoming'][arm][-1]
                outgoing=meta['outgoing'][arm][0]
                a,b=(incoming,outgoing) if direction==0 else (outgoing,incoming)
                p=ET.Element('person',id=f'ped_{arm}_{interval}_{i}',type='pedestrian',
                    depart=f'{interval*900+rng.random()*900:.6f}',
                    departPos='-0.5' if direction==0 else '0.5')
                ET.SubElement(p,'walk',{'from':a,'to':b,'arrivalPos':'0.5' if direction==0 else '-0.5'})
                elements.append(p)
                direction_counts[arm][direction]+=1
    assert sum(ped_counts.values())==manifest['splits']['dev']['pedestrians']==518
    assert len(old.findall('vehicle'))==manifest['splits']['dev']['vehicles']==3594
    for element in sorted(elements,key=lambda e:float(e.get('depart'))):
        result.append(element)
    target=Path(target)
    target.parent.mkdir(parents=True,exist_ok=True)
    ET.indent(result)
    ET.ElementTree(result).write(target,encoding='utf-8',xml_declaration=True)
    audit={'seed':seed,'split':'dev','vehicles':3594,'pedestrians':518,
        'pedestrians_by_leg':ped_counts,'modeled_direction_counts':direction_counts,
        'vehicle_route_pairs':vehicle_counts,
        'assumptions':['Uniform arrivals within observed 15-minute intervals',
            'Pedestrian direction split approximately 50/50 per interval; source has no direction split',
            'Pedestrian approach/departure 0.5 m from junction; fixed 1.2 m/s walking speed'],
        'dictionary':'evidence/traffic_count_dictionary.json',
        'source_dev_sha256':manifest['splits']['dev']['sha256']}
    target.with_suffix('.audit.json').write_text(json.dumps(audit,indent=2))
    print(json.dumps(audit,indent=2))
    return audit


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--seed',type=int,default=11,choices=[11,22,33,44,55])
    parser.add_argument('--output',type=Path,default=ROOT/'models/eglinton_danforth/traffic.rou.xml')
    args=parser.parse_args()
    write_routes(args.seed,args.output)
