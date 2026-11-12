"""Evaluate saved checkpoints on dev only and keep incomplete demand visible."""
import json
from pathlib import Path
import statistics
import xml.etree.ElementTree as ET
from .environment import IntersectionEnv


def read_metrics(folder,audit):
    folder=Path(folder)
    vehicles=ET.parse(folder/'tripinfo.xml').getroot().findall('tripinfo')
    people=ET.parse(folder/'personinfo.xml').getroot().findall('personinfo')
    completed=[v for v in vehicles if float(v.get('arrival'))>=0]
    walks=[p.find('walk') for p in people]
    walks=[w for w in walks if w is not None and float(w.get('arrival'))>=0]
    stats=ET.parse(folder/'statistics.xml').getroot()
    def mean(values):
        values=list(values)
        return statistics.mean(values) if values else None
    record={'vehicles_generated':audit['vehicles'],'vehicles_completed':len(completed),
        'pedestrians_generated':audit['pedestrians'],'pedestrians_completed':len(walks),
        'unfinished_vehicles':audit['vehicles']-len(completed),
        'unfinished_pedestrians':audit['pedestrians']-len(walks),
        'vehicle_time_loss_s':mean(float(v.get('timeLoss')) for v in completed),
        'vehicle_depart_delay_s':mean(float(v.get('departDelay')) for v in completed),
        'vehicle_combined_delay_proxy_s':mean(float(v.get('timeLoss'))+float(v.get('departDelay')) for v in completed),
        'pedestrian_time_loss_s':mean(float(w.get('timeLoss')) for w in walks),
        'collisions':int(stats.find('safety').get('collisions')),
        'teleports':int(stats.find('teleports').get('total')),
        'emergency_braking':int(stats.find('safety').get('emergencyBraking'))}
    record['complete']=record['unfinished_vehicles']==record['unfinished_pedestrians']==0
    record['eligible_delay_comparison']=record['complete'] and record['collisions']==record['teleports']==0
    return record


def evaluate(controller,training_seed,flow_seed,folder,model=None):
    folder=Path(folder)
    env=IntersectionEnv('dev',flow_seed=flow_seed,output=folder,fixed=(controller=='fixed'))
    obs,_=env.reset(seed=flow_seed)
    audit=env.audit
    actions=[]
    try:
        done=False
        while not done:
            action=3 if model is None else int(model.predict(obs,deterministic=True)[0])
            actions.append({'time':env.time,'action':action,'ew_walk':env.phase_durations(action)[3],
                'ns_walk':env.phase_durations(action)[7]})
            obs,_,done,_,info=env.step(action)
    finally:
        env.close()
    record=read_metrics(folder,audit)
    record.update(controller=controller,training_seed=training_seed,flow_seed=flow_seed,
        simulated_seconds=info['simulated_seconds'],reward=info['episode_reward'])
    (folder/'actions.json').write_text(json.dumps(actions,indent=2))
    (folder/'metrics.json').write_text(json.dumps(record,indent=2))
    return record
