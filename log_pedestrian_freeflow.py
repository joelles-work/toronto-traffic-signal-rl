"""Publish the completed walking-speed sensitivity check, not new training."""
import json
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parent
for name, suffix in [('WANDB_CACHE_DIR', 'cache'), ('WANDB_CONFIG_DIR', 'config'), ('WANDB_DATA_DIR', 'data')]:
    os.environ[name] = str(ROOT / 'wandb' / suffix)
import wandb


def main():
    folder = ROOT / 'experiments/pedestrian_freeflow_v1'
    summary = json.loads((folder / 'dev_summary.json').read_text())
    assert len(summary['runs']) == 35
    assert all(r['eligible_delay_comparison'] for r in summary['runs'])
    with wandb.init(entity='joelle1-york-university', project='toronto-tcs379',
                    mode='online', dir=str(ROOT), name='pedestrian-freeflow-1.39-dev-sensitivity',
                    job_type='sensitivity-evaluation', config=summary['experiment']) as run:
        cols = ['controller', 'training_seed', 'flow_seed', 'vehicle_combined_delay_proxy_s',
                'pedestrian_time_loss_s', 'vehicles_completed', 'pedestrians_completed',
                'collisions', 'teleports', 'emergency_braking']
        run.log({'freeflow_dev_comparison': wandb.Table(columns=cols, data=[[r[c] for c in cols] for r in summary['runs']])})
        for name, values in summary['controllers'].items():
            run.summary[f'{name}/vehicle_delay_s'] = values['vehicle_delay_mean_s']
            run.summary[f'{name}/pedestrian_delay_s'] = values['pedestrian_delay_mean_s']
        evidence = wandb.Artifact('pedestrian-freeflow-dev-evidence', type='evaluation')
        for name in ['dev_summary.json', 'experiment.json', 'input_checks.json']:
            evidence.add_file(str(folder / name), name=name)
        run.log_artifact(evidence)
        url, run_id = run.url, run.id
    verified = wandb.Api().run(f'joelle1-york-university/toronto-tcs379/{run_id}')
    (folder / 'wandb_run.json').write_text(json.dumps({'id': run_id, 'url': verified.url, 'state': verified.state}, indent=2))
    print('Verified hosted sensitivity run:', verified.url)


if __name__ == '__main__':
    main()
