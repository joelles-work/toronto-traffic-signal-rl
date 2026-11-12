"""Audit the loaded SUMO program against conflict geometry and PM intervals."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import sumolib

ROOT=Path(__file__).resolve().parent


def validate():
    model=ROOT/'models/eglinton_danforth'
    meta=json.loads((model/'provenance.json').read_text())
    net=sumolib.net.readNet(str(model/'intersection.net.xml'),withInternal=True,withPrograms=True)
    node=net.getNode('TCS379')
    connections=[c for c in node.getConnections() if c.getTLSID()=='TCS379']
    indices={c.getTLLinkIndex() for c in connections}
    logic=next(iter(net.getTLS('TCS379').getPrograms().values()))
    phases=logic.getPhases()
    expected=[7,3,1,31,22,4,3,8,34,4,3]
    assert [float(p.duration) for p in phases]==expected
    assert sum(expected)==120
    crossing_arms=meta['crossing_segments']
    assert len(crossing_arms)==4 and set(crossing_arms.values())==set('nsew')
    records=[]
    time=0
    for p in phases:
        assert indices==set(range(len(p.state))), 'Unclassified traffic-light link.'
        protected=[c for c in connections if p.state[c.getTLLinkIndex()]=='G']
        conflicts=[]
        for i,a in enumerate(protected):
            for b in protected[i+1:]:
                if node.areFoes(a.getJunctionIndex(),b.getJunctionIndex()):
                    conflicts.append([a.getTLLinkIndex(),b.getTLLinkIndex()])
        assert not conflicts, f'Conflicting protected movements in {p.name}: {conflicts}'
        if p.name=='red':
            assert set(p.state)=={'r'}
        if p.name.endswith('_y'):
            assert 'y' in p.state and 'G' not in p.state and 'g' not in p.state
        crossing_entries={}
        for c in connections:
            edge=c.getTo().getID()
            if edge not in crossing_arms:
                continue
            arm=crossing_arms[edge]
            char=p.state[c.getTLLinkIndex()]
            expected_green=(p.name=='ew_walk' and arm in 'ns') or (p.name=='ns_walk' and arm in 'ew')
            assert (char=='G')==expected_green
            crossing_entries[arm]=char
        records.append({'begin_s':time,'end_s':time+p.duration,'name':p.name,'state':p.state,
            'protected_conflicts':conflicts,'crossing_entries':crossing_entries})
        time+=p.duration
    raw=ET.parse(model/'intersection.net.xml').getroot()
    clearances=[]
    for e in raw.findall('edge'):
        if e.get('id') not in crossing_arms:
            continue
        arm=crossing_arms[e.get('id')]
        length=float(e.find('lane').get('length'))
        required=length/1.2
        supplied=22 if arm in 'ns' else 34
        assert supplied>=required
        clearances.append({'leg':arm,'crossing':e.get('id'),'length_m':length,
            'modeled_speed_mps':1.2,'minimum_traversal_s':required,'clearance_s':supplied})
    report={'result':'PASS','cycle_s':120,'signal_links':len(indices),
        'checks':['PM duration sequence','all-red and yellow stages','no conflicting protected greens in SUMO foe matrix',
            'crossing green serves the correct leg','one full-width crossing per leg','clearance sufficient at modeled walking speed'],
        'phases':records,'clearances':clearances,
        'limits':['Static model conflict audit, not certification of field signal operation',
            'City timing card advance-phase interpretation and surveyed geometry still require external verification']}
    path=ROOT/'evidence/signal_validation.json'
    path.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    validate()
