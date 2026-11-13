"""Publish the completed small dev validation, including unsuccessful cases."""
import json
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parent
for name, suffix in [('WANDB_CACHE_DIR','cache'),('WANDB_CONFIG_DIR','config'),('WANDB_DATA_DIR','data')]:
    os.environ[name] = str(ROOT/'wandb'/suffix)
import wandb


def main():
    folder = ROOT/'experiments/dev_assumptions_v1'
    summary = json.loads((folder/'summary.json').read_text())
    assert len(summary['runs']) == 25
    with wandb.init(entity='joelle1-york-university', project='toronto-tcs379',
                    mode='online', dir=str(ROOT), name='dev-assumptions-constant-plans-and-clipping',
                    job_type='dev-validation', config=summary['plan']) as run:
        keys = ['action','flow_seed','ew_walk_s','ns_walk_s','eligible_delay_comparison',
                'vehicle_combined_delay_proxy_s','pedestrian_time_loss_s','unfinished_vehicles',
                'unfinished_pedestrians','collisions','teleports']
        run.log({'constant_plan_cases':wandb.Table(columns=keys,data=[[r[k] for k in keys] for r in summary['runs']])})
        for action, item in summary['actions'].items():
            run.summary[f'action_{action}/all_cases_eligible'] = item['all_cases_eligible']
            run.summary[f'action_{action}/unfinished_vehicles_total'] = item['unfinished_vehicles']
            for key, value in item['metrics'].items():
                run.summary[f'action_{action}/{key}'] = value['mean']
        artifact = wandb.Artifact('dev-assumptions-validation-evidence',type='evaluation')
        for path in [folder/'plan.json',folder/'summary.json',folder/'derived_checks.json',ROOT/'validate_pilot_assumptions.py']:
            artifact.add_file(str(path),name=path.name)
        run.log_artifact(artifact)
        run_id = run.id
    api_run = wandb.Api().run(f'joelle1-york-university/toronto-tcs379/{run_id}')
    (folder/'wandb_run.json').write_text(json.dumps({'id':run_id,'url':api_run.url,'state':api_run.state},indent=2))
    print('Verified validation run:',api_run.url)


if __name__ == '__main__':
    main()
