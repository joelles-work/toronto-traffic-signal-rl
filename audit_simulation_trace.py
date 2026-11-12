"""Record and audit actual signal states and pedestrian crossing paths."""
from collections import defaultdict
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
MODEL=ROOT/'models/eglinton_danforth'
OUT=ROOT/'evidence/signal_trace_audit'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    args=json.loads((ROOT/'results/revised_fixed_dev/seed_11/command.json').read_text())
    for flag,name in [('--tripinfo-output','tripinfo.xml'),('--personinfo-output','personinfo.xml'),
        ('--statistic-output','statistics.xml'),('--person-fcd-output','pedestrian_trace.xml')]:
        args[args.index(flag)+1]=str(OUT/name)
    if '--fcd-output' not in args:
        args+=['--fcd-output',str(OUT/'vehicle_trace.xml'),'--device.fcd.probability','0']
    else:
        args[args.index('--fcd-output')+1]=str(OUT/'vehicle_trace.xml')
    additional=ET.Element('additional')
    ET.SubElement(additional,'timedEvent',type='SaveTLSStates',source='TCS379',dest=str(OUT/'signal_trace.xml'))
    ET.ElementTree(additional).write(OUT/'trace.add.xml',encoding='utf-8',xml_declaration=True)
    args[args.index('-a')+1]=str(OUT/'trace.add.xml')
    (OUT/'command.json').write_text(json.dumps(args,indent=2))
    run=subprocess.run(args,capture_output=True,text=True)
    (OUT/'sumo.log').write_text(run.stdout+run.stderr)
    if run.returncode:
        raise RuntimeError(run.stderr)
    signal=json.loads((ROOT/'evidence/signal_validation.json').read_text())
    phases=signal['phases']
    states={}
    for e in ET.parse(OUT/'signal_trace.xml').getroot().findall('tlsState'):
        t=int(float(e.get('time')))
        expected=next(p for p in phases if p['begin_s']<=t%120<p['end_s'])
        assert e.get('state')==expected['state'],f'Unexpected signal state at {t}'
        states[t]=e.get('state')
    assert len(states)==7200
    meta=json.loads((MODEL/'provenance.json').read_text())
    crossings=meta['crossing_segments']
    crossing_signal={}
    root=ET.parse(MODEL/'intersection.net.xml').getroot()
    for c in root.findall('connection'):
        if c.get('tl')=='TCS379' and c.get('to') in crossings:
            crossing_signal[c.get('to')]=int(c.get('linkIndex'))
    seen=defaultdict(set)
    entry_times={}
    person_ids=set()
    invalid_entries=[]
    for step in ET.parse(OUT/'pedestrian_trace.xml').getroot().findall('timestep'):
        t=int(float(step.get('time')))
        for p in step.findall('person'):
            pid=p.get('id')
            person_ids.add(pid)
            edge=p.get('edge')
            if edge not in crossings:
                continue
            expected_arm=pid.split('_')[1]
            assert crossings[edge]==expected_arm,f'{pid} used the wrong leg: {edge}'
            seen[pid].add(edge)
            if pid not in entry_times:
                entry_times[pid]=t
                idx=crossing_signal[edge]
                if not any(states.get(k,'r'*30)[idx]=='G' for k in [t,max(0,t-1)]):
                    invalid_entries.append({'person':pid,'time':t,'crossing':edge})
    assert len(person_ids)==len(seen)==518,(len(person_ids),len(seen))
    assert all(len(edges)==1 for edges in seen.values()), 'A pedestrian used more than its intended full-width crossing.'
    assert not invalid_entries,invalid_entries[:10]
    counts={arm:sum(pid.split('_')[1]==arm for pid in seen) for arm in 'nsew'}
    expected=json.loads((ROOT/'results/revised_fixed_dev/seed_11/routes.rou.audit.json').read_text())['pedestrians_by_leg']
    assert counts==expected
    report={'result':'PASS','signal_states_checked':len(states),'cycles_checked':60,
        'pedestrians_traced':len(seen),'correct_crossing_leg_counts':counts,
        'invalid_crossing_entries':invalid_entries,
        'entry_check':'Crossing entry must match a WALK green in the current or immediately preceding 1-second state sample.',
        'scope':'SUMO model and route audit; not an assertion of field calibration or road-safety certification.'}
    (ROOT/'evidence/signal_runtime_validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
