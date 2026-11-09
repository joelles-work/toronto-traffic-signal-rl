"""Vehicle-only fixed-cycle prototype. Geometry is idealized, not Toronto-calibrated."""
import csv
import hashlib
import json
import random
import statistics
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import sumolib

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results' / 'baseline_dev'
DEST = {
    'n': {'r':'w', 't':'s', 'l':'e'},
    's': {'r':'e', 't':'n', 'l':'w'},
    'e': {'r':'n', 't':'w', 'l':'s'},
    'w': {'r':'s', 't':'e', 'l':'n'},
}


def save_xml(root, path):
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def network():
    OUT.mkdir(parents=True, exist_ok=True)
    nodes = ET.Element('nodes')
    ET.SubElement(nodes, 'node', id='C', x='0', y='0', type='traffic_light')
    for name, (x,y) in {'n':(0,500),'s':(0,-500),'e':(500,0),'w':(-500,0)}.items():
        ET.SubElement(nodes, 'node', id=name, x=str(x), y=str(y), type='priority')
    edges = ET.Element('edges')
    connections = ET.Element('connections')
    for arm in DEST:
        for incoming in (True, False):
            ET.SubElement(edges, 'edge', {'id':arm+('_in' if incoming else '_out'),
                'from':arm if incoming else 'C', 'to':'C' if incoming else arm,
                'numLanes':'3', 'speed':'13.89'})
        for lane, movement in enumerate(('r','t','l')):
            ET.SubElement(connections, 'connection', {
                'from':arm+'_in', 'to':DEST[arm][movement]+'_out',
                'fromLane':str(lane), 'toLane':str(lane)})
    for name, root in [('nodes',nodes),('edges',edges),('connections',connections)]:
        save_xml(root, OUT / f'{name}.xml')
    net = OUT / 'idealized.net.xml'
    result = subprocess.run([sumolib.checkBinary('netconvert'),
        '--node-files', str(OUT/'nodes.xml'), '--edge-files', str(OUT/'edges.xml'),
        '--connection-files', str(OUT/'connections.xml'), '--output-file',str(net),
        '--no-turnarounds','true'], capture_output=True, text=True, check=True)
    (OUT/'network.log').write_text(result.stdout+result.stderr, encoding='utf-8')
    tree = ET.parse(net)
    controlled = {int(c.attrib['linkIndex']):c.attrib for c in tree.getroot().findall('connection') if c.get('tl')=='C'}
    assert len(controlled)==12
    phases = []
    # PM card duration sequence, using its simultaneous EW-left advance option.
    # Walk/clearance stages are combined into vehicle green; pedestrians are absent.
    for duration, mode in [(7,'ew_left'),(3,'ew_left_y'),(1,'red'),(53,'ew'),(4,'ew_y'),(3,'red'),(42,'ns'),(4,'ns_y'),(3,'red')]:
        state = []
        for i in range(len(controlled)):
            c = controlled[i]
            arm, direction = c['from'][0], c['dir']
            ew = arm in ('e','w')
            value = 'r'
            if mode.startswith('ew_left') and ew and direction=='l':
                value = 'y' if mode.endswith('_y') else 'G'
            elif mode in ('ew','ew_y','ns','ns_y') and (ew == mode.startswith('ew')):
                value = 'y' if mode.endswith('_y') else ('g' if direction=='l' else 'G')
            state.append(value)
        phases.append((duration, ''.join(state)))
    assert sum(d for d,_ in phases)==120
    additional = ET.Element('additional')
    logic = ET.SubElement(additional, 'tlLogic', id='C', type='static', programID='prototype_PM', offset='0')
    for duration,state in phases:
        ET.SubElement(logic,'phase',duration=str(duration),state=state)
    save_xml(additional, OUT/'fixed.add.xml')
    return net


def main():
    manifest = json.loads((ROOT/'data/split_manifest.json').read_text())
    source = ROOT/'data/dev.csv'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['splits']['dev']['sha256']
    with source.open(newline='') as f:
        rows = list(csv.DictReader(f))
    net = network()
    results=[]
    for seed in manifest['seeds']:
        folder = OUT/f'seed_{seed}'
        folder.mkdir(exist_ok=True)
        rng=random.Random(seed)
        arrivals=[]
        for interval,r in enumerate(rows):
            for arm in DEST:
                for kind in ('cars','truck','bus'):
                    for move in ('r','t','l'):
                        count=int(r[f'{arm}_appr_{kind}_{move}'])
                        for _ in range(count):
                            arrivals.append((interval*900+rng.random()*900,arm,move,kind))
        arrivals.sort()
        assert len(arrivals)==manifest['splits']['dev']['vehicles']
        routes=ET.Element('routes')
        for kind,cls,length in [('cars','passenger','5'),('truck','truck','10'),('bus','bus','12')]:
            ET.SubElement(routes,'vType',id=kind,vClass=cls,length=length,sigma='0.5')
        for index,(depart,arm,move,kind) in enumerate(arrivals):
            vehicle=ET.SubElement(routes,'vehicle',id=f'v{index}',type=kind,depart=f'{depart:.6f}',departLane=str(('r','t','l').index(move)))
            ET.SubElement(vehicle,'route',edges=f'{arm}_in {DEST[arm][move]}_out')
        save_xml(routes,folder/'routes.rou.xml')
        command=[sumolib.checkBinary('sumo'),'-n',str(net),'-r',str(folder/'routes.rou.xml'),
            '-a',str(OUT/'fixed.add.xml'),'--seed',str(seed),'--end','7200',
            '--time-to-teleport','-1','--no-step-log','true','--duration-log.statistics','true',
            '--tripinfo-output',str(folder/'tripinfo.xml'),'--tripinfo-output.write-unfinished','true',
            '--statistic-output',str(folder/'statistics.xml')]
        (folder/'command.json').write_text(json.dumps(command,indent=2))
        run=subprocess.run(command,capture_output=True,text=True,check=True)
        (folder/'sumo.log').write_text(run.stdout+run.stderr,encoding='utf-8')
        trips=ET.parse(folder/'tripinfo.xml').getroot().findall('tripinfo')
        complete=[t for t in trips if float(t.get('arrival'))>=0]
        stats=ET.parse(folder/'statistics.xml').getroot()
        safety=stats.find('safety')
        teleports=stats.find('teleports')
        record={'seed':seed,'generated':len(arrivals),'completed':len(complete),
            'unfinished_or_uninserted':len(arrivals)-len(complete),
            'mean_time_loss_s':statistics.mean(float(t.get('timeLoss')) for t in complete),
            'mean_depart_delay_s':statistics.mean(float(t.get('departDelay')) for t in complete),
            'mean_total_delay_proxy_s':statistics.mean(float(t.get('timeLoss'))+float(t.get('departDelay')) for t in complete),
            'collisions':int(safety.get('collisions','0')) if safety is not None else None,
            'teleports':int(teleports.get('total','0')) if teleports is not None else None}
        (folder/'metrics.json').write_text(json.dumps(record,indent=2))
        print(json.dumps(record),flush=True)
        results.append(record)
    summary={'label':'vehicle_only_idealized_fixed_cycle_PM','split':'dev',
        'geometry':'Uncalibrated four-arm orthogonal junction; 500 m arms, three dedicated movement lanes per approach, 13.89 m/s.',
        'pedestrians_simulated':False,'warmup_seconds':0,'demand_seconds':3600,'maximum_end_seconds':7200,
        'tuning':'One preset configuration; no parameter search, no DQN/PPO training, no test simulations.',
        'runs':results}
    for key in ('mean_time_loss_s','mean_depart_delay_s','mean_total_delay_proxy_s'):
        summary[key]={'mean':statistics.mean(r[key] for r in results),'sample_std':statistics.stdev(r[key] for r in results)}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
