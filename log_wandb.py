"""Record completed baseline outputs in offline W&B runs for later account sync."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for key, suffix in [('WANDB_DATA_DIR','data'),('WANDB_CACHE_DIR','cache'),('WANDB_CONFIG_DIR','config')]:
    directory=ROOT/'wandb'/suffix
    directory.mkdir(parents=True,exist_ok=True)
    os.environ[key]=str(directory)

import wandb


def main():
    summary = json.loads((ROOT/'results/baseline_dev/summary.json').read_text())
    index=[]
    for metrics in summary['runs']:
        seed=metrics['seed']
        with wandb.init(project='toronto-tcs379', mode='offline',
            name=f'prototype-fixed-dev-seed-{seed}', group='baseline-dev-v1',
            dir=str(ROOT), config={
                'controller':summary['label'],'split':'dev','seed':seed,
                'geometry':summary['geometry'],'pedestrians_simulated':False,
                'logging':'post-hoc import of saved SUMO results',
                'demand_seconds':3600,'maximum_end_seconds':7200,
                'warmup_seconds':0,'cycle_seconds':120,
            }) as run:
            run.log(metrics)
            for key,value in metrics.items():
                run.summary[key]=value
            artifact=wandb.Artifact(f'baseline-dev-seed-{seed}',type='evaluation')
            folder=ROOT/'results/baseline_dev'/f'seed_{seed}'
            for path in [folder/'metrics.json',folder/'sumo.log',folder/'statistics.xml',
                ROOT/'data/split_manifest.json',ROOT/'run_baseline.py']:
                artifact.add_file(str(path),name=path.name)
            run.log_artifact(artifact)
            index.append({'seed':seed,'id':run.id,'directory':str(Path(run.dir).parent),'mode':'offline','hosted_url':None})
    (ROOT/'results/wandb_runs.json').write_text(json.dumps(index,indent=2))


if __name__=='__main__':
    main()
