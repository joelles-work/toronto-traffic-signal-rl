"""Five-seed dev evaluation of the revised fixed-time multimodal model."""
import json
from pathlib import Path
import statistics
import subprocess
import xml.etree.ElementTree as ET

import sumolib
from revised_demand import write_routes
from validate_signal import validate

ROOT=Path(__file__).resolve().parent
MODEL=ROOT/'models/eglinton_danforth'
OUT=ROOT/'results/revised_fixed_dev'


def main():
    validate()
    OUT.mkdir(parents=True,exist_ok=True)
    meta=json.loads((MODEL/'provenance.json').read_text())
    runs=[]
    for seed in [11,22,33,44,55]:
        folder=OUT/f'seed_{seed}'
        folder.mkdir(exist_ok=True)
        audit=write_routes(seed,folder/'routes.rou.xml')
        args=[sumolib.checkBinary('sumo'),'-n',str(MODEL/'intersection.net.xml'),
            '-r',str(folder/'routes.rou.xml'),'--seed',str(seed),'--end','7200',
            '--time-to-teleport','-1','--no-step-log','true',
            '--tripinfo-output',str(folder/'tripinfo.xml'),
            '--tripinfo-output.write-unfinished','true',
            '--personinfo-output',str(folder/'personinfo.xml'),
            '--statistic-output',str(folder/'statistics.xml')]
        if seed==11:
            trace=ET.Element('additional')
            ET.SubElement(trace,'timedEvent',type='SaveTLSStates',source='TCS379',dest=str(folder/'signal_trace.xml'))
            ET.ElementTree(trace).write(folder/'trace.add.xml',encoding='utf-8',xml_declaration=True)
            args+=['-a',str(folder/'trace.add.xml'),
                '--fcd-output',str(folder/'vehicle_trace.xml'),'--device.fcd.probability','0',
                '--person-fcd-output',str(folder/'pedestrian_trace.xml'),
                '--person-device.fcd.probability','1','--fcd-output.attributes','id,edge,pos,speed']
        (folder/'command.json').write_text(json.dumps(args,indent=2))
        run=subprocess.run(args,capture_output=True,text=True)
        (folder/'sumo.log').write_text(run.stdout+run.stderr,encoding='utf-8')
        if run.returncode:
            raise RuntimeError(run.stderr)
        trips=ET.parse(folder/'tripinfo.xml').getroot().findall('tripinfo')
        people=ET.parse(folder/'personinfo.xml').getroot().findall('personinfo')
        completed=[t for t in trips if float(t.get('arrival'))>=0]
        walks=[p.find('walk') for p in people]
        walks=[w for w in walks if w is not None and float(w.get('arrival'))>=0]
        stats=ET.parse(folder/'statistics.xml').getroot()
        assert len(completed)==3594 and len(walks)==518, 'Unfinished demand must not be silently excluded.'
        assert int(stats.find('teleports').get('total'))==0
        assert int(stats.find('safety').get('collisions'))==0
        record={'seed':seed,'split':'dev','vehicles_generated':audit['vehicles'],'vehicles_completed':len(completed),
            'pedestrians_generated':audit['pedestrians'],'pedestrians_completed':len(walks),
            'vehicle_time_loss_s':statistics.mean(float(t.get('timeLoss')) for t in completed),
            'vehicle_depart_delay_s':statistics.mean(float(t.get('departDelay')) for t in completed),
            'vehicle_combined_delay_proxy_s':statistics.mean(float(t.get('timeLoss'))+float(t.get('departDelay')) for t in completed),
            'pedestrian_time_loss_s':statistics.mean(float(w.get('timeLoss')) for w in walks),
            'pedestrian_walk_duration_s':statistics.mean(float(w.get('duration')) for w in walks),
            'collisions':int(stats.find('safety').get('collisions')),
            'teleports':int(stats.find('teleports').get('total')),
            'emergency_braking':int(stats.find('safety').get('emergencyBraking'))}
        (folder/'metrics.json').write_text(json.dumps(record,indent=2))
        print(json.dumps(record),flush=True)
        runs.append(record)
    summary={'controller':'fixed_PM_geometry_revision','split':'dev','seeds':[11,22,33,44,55],
        'network':'models/eglinton_danforth/intersection.net.xml','runs':runs,
        'assumptions':audit['assumptions'],
        'limitations':['Source-aligned model geometry is uncalibrated for field delay and 2024 conditions',
            'Pedestrian directional balance, within-interval arrival times, and walking speeds are modeled',
            'No warm-up; empty initial traffic state; up to 3600 s drain after 3600 s demand',
            'Delay proxies include route effects; transit lane permissions and stops are not validated']}
    for key in ['vehicle_time_loss_s','vehicle_depart_delay_s','vehicle_combined_delay_proxy_s','pedestrian_time_loss_s','pedestrian_walk_duration_s']:
        summary[key]={'mean':statistics.mean(r[key] for r in runs),'sample_std':statistics.stdev(r[key] for r in runs)}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
