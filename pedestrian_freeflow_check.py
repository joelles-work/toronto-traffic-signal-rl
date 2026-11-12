"""Matched dev sensitivity check at SUMO's 1.39 m/s desired walking speed.

The original 1.2 m/s experiment and its trained checkpoints stay immutable.
This evaluates those saved policies in a revised walking-speed environment;
it does not claim they were retrained at 1.39 m/s.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'experiments/pedestrian_freeflow_v1'
SPEED = 1.39


def worker(controller):
    import torch
    from stable_baselines3 import DQN, PPO
    import rl.environment as environment
    from rl.demand import generate as original_generate
    from rl.evaluation import evaluate
    from rl.freeze import PILOT, digest, verify
    torch.set_num_threads(1)
    verify()

    def generate(split, seed):
        if split != 'dev':
            raise ValueError('This sensitivity check exposes dev only.')
        source, audit = original_generate(split, seed)
        target = OUT / 'demand' / controller / f'dev_{seed}.rou.xml.gz'
        target.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(source, 'rb') as f:
            tree = ET.parse(f)
        ped = tree.getroot().find("vType[@id='pedestrian']")
        assert ped.get('maxSpeed') == '1.2'
        ped.set('maxSpeed', str(SPEED))
        ped.set('desiredMaxSpeed', str(SPEED))
        with gzip.open(target, 'wb') as f:
            tree.write(f, encoding='utf-8', xml_declaration=True)
        return target, audit

    environment.generate = generate
    seeds = [None] if controller == 'fixed' else [101, 202, 303]
    records = []
    for seed in seeds:
        model = None
        if seed is not None:
            folder = PILOT / 'training' / f'{controller.lower()}_{seed}'
            complete = json.loads((folder / 'completed.json').read_text())
            assert digest(folder / 'model.zip') == complete['model_sha256']
            model = (DQN if controller == 'DQN' else PPO).load(folder / 'model.zip', device='cpu')
        for flow in [11, 22, 33, 44, 55]:
            folder = OUT / 'dev' / f'{controller.lower()}_{seed}' / f'flow_{flow}'
            started = time.perf_counter()
            record = evaluate(controller, seed, flow, folder, model)
            record['pedestrian_desired_speed_m_s'] = SPEED
            record['training_pedestrian_speed_m_s'] = None if seed is None else 1.2
            record['wall_seconds'] = time.perf_counter() - started
            (folder / 'metrics.json').write_text(json.dumps(record, indent=2))
            records.append(record)
            print(controller, seed, flow, 'vehicle delay', round(record['vehicle_combined_delay_proxy_s'], 2), 'pedestrian delay', round(record['pedestrian_time_loss_s'], 2), flush=True)
    return records


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    plan = {
        'name': 'pedestrian_freeflow_v1', 'split': 'dev', 'test_evaluated': False,
        'desired_walking_speed_m_s': SPEED, 'speedFactor': 1, 'speedDev': 0,
        'source': 'https://sumo.dlr.de/docs/Specification/Persons.html',
        'interpretation': 'SUMO default desired unconstrained walking speed; not measured at this site. Actual speed may be lower due to signals or interactions.',
        'change': 'Walking speed only; observed counts, exact departures and routes, signal clearance durations, vehicle parameters and checkpoints unchanged.',
        'policy_status': 'Saved policies trained at 1.2 m/s; transfer/sensitivity evaluation, not retraining at 1.39 m/s.',
        'flow_seeds': [11, 22, 33, 44, 55], 'training_seeds': [101, 202, 303],
        'implementation_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (OUT / 'experiment.json').write_text(json.dumps(plan, indent=2))
    with ProcessPoolExecutor(max_workers=3) as pool:
        groups = list(pool.map(worker, ['fixed', 'DQN', 'PPO']))
    records = [r for group in groups for r in group]
    controllers = {}
    for name in ['fixed', 'DQN', 'PPO']:
        rr = [r for r in records if r['controller'] == name]
        controllers[name] = {
            'runs': len(rr), 'all_runs_eligible': all(r['eligible_delay_comparison'] for r in rr),
            'vehicle_delay_mean_s': statistics.mean(r['vehicle_combined_delay_proxy_s'] for r in rr),
            'pedestrian_delay_mean_s': statistics.mean(r['pedestrian_time_loss_s'] for r in rr),
            'by_training_seed': {str(seed): {
                key: {'mean': statistics.mean(r[key] for r in rr if r['training_seed'] == seed),
                      'std_across_demand': statistics.stdev(r[key] for r in rr if r['training_seed'] == seed)}
                for key in ['vehicle_combined_delay_proxy_s', 'pedestrian_time_loss_s']}
                for seed in sorted({r['training_seed'] for r in rr}, key=str)},
        }
    summary = {'experiment': plan, 'controllers': controllers, 'runs': records}
    (OUT / 'dev_summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(controllers, indent=2), flush=True)


if __name__ == '__main__':
    main()
