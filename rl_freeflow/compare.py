"""Matched dev comparison of the last checkpoints; never opens test data."""
import json
from pathlib import Path
import statistics
import time
import numpy as np
import torch
from stable_baselines3 import DQN,PPO
from .freeze import PILOT,SEEDS,verify,digest
from .evaluation import evaluate

METRICS=['vehicle_time_loss_s','vehicle_depart_delay_s','vehicle_combined_delay_proxy_s','pedestrian_time_loss_s']


def main():
    config=verify()
    torch.set_num_threads(1)
    out=PILOT/'dev'
    out.mkdir(exist_ok=True)
    records=[]
    for algorithm in ['fixed','DQN','PPO']:
        training_seeds=[None] if algorithm=='fixed' else SEEDS
        for training_seed in training_seeds:
            model=None
            if algorithm!='fixed':
                folder=PILOT/'training'/f'{algorithm.lower()}_{training_seed}'
                complete=json.loads((folder/'completed.json').read_text())
                assert digest(folder/'model.zip')==complete['model_sha256']
                cls=DQN if algorithm=='DQN' else PPO
                model=cls.load(folder/'model.zip',device='cpu')
            for flow_seed in config['dev_demand_seeds']:
                folder=out/f'{algorithm.lower()}_{training_seed}'/f'flow_{flow_seed}'
                if (folder/'metrics.json').exists():
                    record=json.loads((folder/'metrics.json').read_text())
                else:
                    start=time.perf_counter()
                    record=evaluate(algorithm,training_seed,flow_seed,folder,model)
                    record['wall_seconds']=time.perf_counter()-start
                    (folder/'metrics.json').write_text(json.dumps(record,indent=2))
                records.append(record)
                print(json.dumps(record),flush=True)
    summaries={}
    for algorithm in ['fixed','DQN','PPO']:
        rr=[r for r in records if r['controller']==algorithm]
        valid=all(r['eligible_delay_comparison'] for r in rr)
        item={'runs':len(rr),'all_runs_eligible':valid,
            'total_unfinished_vehicles':sum(r['unfinished_vehicles'] for r in rr),
            'total_unfinished_pedestrians':sum(r['unfinished_pedestrians'] for r in rr),
            'total_collisions':sum(r['collisions'] for r in rr),
            'total_teleports':sum(r['teleports'] for r in rr),
            'total_emergency_braking':sum(r['emergency_braking'] for r in rr)}
        if valid:
            item['pooled_case_metrics']={key:{'mean':statistics.mean(r[key] for r in rr),
                'sample_std':statistics.stdev(r[key] for r in rr)} for key in METRICS}
            if algorithm!='fixed':
                by_seed={str(seed):{key:{'mean':statistics.mean(r[key] for r in rr if r['training_seed']==seed),
                    'sample_std_across_demand':statistics.stdev(r[key] for r in rr if r['training_seed']==seed)}
                    for key in METRICS} for seed in SEEDS}
                item['by_training_seed']=by_seed
                item['between_training_seed_metrics']={key:{'mean':statistics.mean(by_seed[str(seed)][key]['mean'] for seed in SEEDS),
                    'sample_std_of_five_demand_seed_means':statistics.stdev(by_seed[str(seed)][key]['mean'] for seed in SEEDS)} for key in METRICS}
                fixed={r['flow_seed']:r for r in records if r['controller']=='fixed'}
                rng=np.random.default_rng(5420)
                intervals={}
                for key in ['vehicle_combined_delay_proxy_s','pedestrian_time_loss_s']:
                    matrix=np.array([[next(r[key] for r in rr if r['training_seed']==seed and r['flow_seed']==flow)-fixed[flow][key]
                        for flow in config['dev_demand_seeds']] for seed in SEEDS])
                    samples=[]
                    for _ in range(4000):
                        i=rng.integers(0,3,3)
                        j=rng.integers(0,5,5)
                        samples.append(float(matrix[np.ix_(i,j)].mean()))
                    intervals[key]={'paired_difference_mean_s':float(matrix.mean()),
                        'two_way_bootstrap_95_percent_interval_s':[float(x) for x in np.quantile(samples,[.025,.975])],
                        'note':'Exploratory crossed resampling of training seeds and paired demand seeds; only three training replicates.'}
                item['paired_comparison_to_fixed']=intervals
        else:
            item['note']='No all-demand mean-delay ranking: at least one policy left unfinished demand or had collisions/teleports. Per-run completed-trip means are retained with this limitation.'
        summaries[algorithm]=item
    summary={'experiment':'freeflow_pilot_v1','split':'dev','test_evaluated':False,
        'decision_budget_per_model':config['decision_budget_per_model'],
        'training_seeds':SEEDS,'demand_seeds':config['dev_demand_seeds'],
        'controllers':summaries,'runs':records,
        'limitations':['Initial bounded training budget; no architecture/reward search.',
            'Model geometry, boundary queues, transit operations, initial conditions, and 2024 fidelity remain uncalibrated.',
            'Dev comparison is for model development, not held-out test performance.']}
    (PILOT/'dev_summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summaries,indent=2),flush=True)


if __name__=='__main__':
    main()
