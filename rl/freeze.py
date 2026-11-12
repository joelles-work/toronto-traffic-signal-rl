"""Freeze and verify pilot inputs before learning or model selection."""
import hashlib
import json
import platform
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
PILOT=ROOT/'experiments/pilot_v1'
ASSETS=PILOT/'assets'
WALK_ALLOCATIONS=[7,19,25,31,32]
SEEDS=[101,202,303]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def freeze():
    manifest=PILOT/'experiment.json'
    if manifest.exists():
        verify()
        return json.loads(manifest.read_text())
    ASSETS.mkdir(parents=True,exist_ok=True)
    sources={
        'intersection.net.xml':ROOT/'models/eglinton_danforth/intersection.net.xml',
        'provenance.json':ROOT/'models/eglinton_danforth/provenance.json',
        'split_manifest.json':ROOT/'data/split_manifest.json',
        'train.csv':ROOT/'data/train.csv','dev.csv':ROOT/'data/dev.csv',
        'signal_validation.json':ROOT/'evidence/signal_validation.json',
        'signal_runtime_validation.json':ROOT/'evidence/signal_runtime_validation.json',
    }
    for name,source in sources.items():
        shutil.copy2(source,ASSETS/name)
    # Retain the exact vehicle/pedestrian definitions used in the current baseline.
    traffic=ET.parse(ROOT/'models/eglinton_danforth/traffic.rou.xml').getroot()
    types=ET.Element('routes')
    for vt in traffic.findall('vType'):
        types.append(vt)
    ET.ElementTree(types).write(ASSETS/'types.rou.xml',encoding='utf-8',xml_declaration=True)
    data={
        'name':'pilot_v1','status':'initial bounded pilot; not final model selection',
        'training_split':'June 19 2024 15:00-17:00',
        'dev_split':'June 19 2024 17:00-18:00',
        'test_policy':'No test data are copied, generated, simulated, or scored by this experiment.',
        'assets':{p.name:digest(p) for p in ASSETS.iterdir() if p.is_file()},
        'training_seeds':SEEDS,'dev_demand_seeds':[11,22,33,44,55],
        'decision_budget_per_model':2048,'algorithms':['DQN','PPO'],
        'observation':'Per-leg approach count, queue, pending entry count, pedestrian waiting count, pedestrian maximum waiting time, plus previous action one-hot; fixed scales, no fitted dev statistics.',
        'actions':{'east_west_walk_seconds':WALK_ALLOCATIONS,'north_south_walk_seconds':[39-x for x in WALK_ALLOCATIONS],
            'fixed_time_action':3,'cycle_seconds':120,'minimum_walk_seconds':7},
        'reward':'Negative integral of approach vehicle queues + pending vehicle insertions + stopped pedestrians, sampled every 5 s, divided by 1200 per cycle; equal weight per road user.',
        'constraints':'Fixed stage order; 7 s protected EW-left advance, 3 s advance yellow, 1 s red; 22/34 s pedestrian clearances; 4 s main yellows and 3 s all-reds.',
        'training_window_seconds':7200,'dev_window_seconds':3600,'maximum_drain_seconds':3600,
        'DQN':{'learning_rate':0.0003,'buffer_size':20000,'learning_starts':180,'batch_size':64,'gamma':0.99,'train_freq':1,'gradient_steps':1,'target_update_interval':256,'exploration_fraction':0.6,'exploration_final_eps':0.05,'policy_kwargs':{'net_arch':[64,64]}},
        'PPO':{'learning_rate':0.0003,'n_steps':256,'batch_size':64,'n_epochs':10,'gamma':0.99,'gae_lambda':0.95,'ent_coef':0.01,'policy_kwargs':{'net_arch':[64,64]}},
        'comparison':'Last checkpoints only; deterministic dev inference. Fixed-time and every saved policy share the five dev demand realizations. No search over architectures or training budgets in this pilot.',
        'metrics':'Vehicle timeLoss and departDelay separately and combined; pedestrian walk timeLoss; completion, collisions, teleports, emergency braking. Unfinished demand invalidates an all-demand delay comparison.',
        'statistics':'Mean and sample SD across five demand seeds for each training seed; training variability reported separately across three policy seeds.',
        'python':platform.python_version(),
    }
    manifest.write_text(json.dumps(data,indent=2))
    return data


def verify():
    manifest=PILOT/'experiment.json'
    data=json.loads(manifest.read_text())
    for name,expected in data['assets'].items():
        if digest(ASSETS/name)!=expected:
            raise RuntimeError(f'Frozen input changed: {name}')
    split=json.loads((ASSETS/'split_manifest.json').read_text())
    for name in ('train','dev'):
        assert digest(ASSETS/f'{name}.csv')==split['splits'][name]['sha256']
    return data


if __name__=='__main__':
    print(json.dumps(freeze(),indent=2))
