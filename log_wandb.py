"""Record completed baseline outputs in offline W&B runs for later account sync."""
import json
import argparse
import hashlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for key, suffix in [('WANDB_DATA_DIR','data'),('WANDB_CACHE_DIR','cache'),('WANDB_CONFIG_DIR','config')]:
    directory=ROOT/'wandb'/suffix
    directory.mkdir(parents=True,exist_ok=True)
    os.environ[key]=str(directory)

import wandb


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--revised',action='store_true')
    args=parser.parse_args()
    base=ROOT/'results'/('revised_fixed_dev' if args.revised else 'baseline_dev')
    summary = json.loads((base/'summary.json').read_text())
    group='revised-fixed-dev-v2' if args.revised else 'baseline-dev-v1'
    index=[]
    for metrics in summary['runs']:
        seed=metrics['seed']
        with wandb.init(project='toronto-tcs379', mode='offline',
            name=f'{group}-seed-{seed}', group=group,
            dir=str(ROOT), config={
                'controller':summary.get('label',summary.get('controller')),'split':'dev','seed':seed,
                'geometry':summary.get('geometry',summary.get('network')),'pedestrians_simulated':args.revised,
                'network_sha256':hashlib.sha256((ROOT/'models/eglinton_danforth/intersection.net.xml').read_bytes()).hexdigest() if args.revised else None,
                'logging':'post-hoc import of saved SUMO results',
                'demand_seconds':3600,'maximum_end_seconds':7200,
                'warmup_seconds':0,'cycle_seconds':120,
            }) as run:
            run.log(metrics)
            for key,value in metrics.items():
                run.summary[key]=value
            artifact=wandb.Artifact(f'{group}-seed-{seed}',type='evaluation')
            folder=base/f'seed_{seed}'
            paths=[folder/'metrics.json',folder/'sumo.log',folder/'statistics.xml',
                ROOT/'data/split_manifest.json',ROOT/('run_revised_baseline.py' if args.revised else 'run_baseline.py')]
            if args.revised:
                paths += [folder/'routes.rou.audit.json',ROOT/'evidence/signal_validation.json',
                    ROOT/'evidence/signal_runtime_validation.json',ROOT/'models/eglinton_danforth/provenance.json']
            for path in paths:
                artifact.add_file(str(path),name=path.name)
            run.log_artifact(artifact)
            index.append({'seed':seed,'id':run.id,'directory':str(Path(run.dir).parent),'mode':'offline','hosted_url':None})
    target=base/'wandb_runs.json' if args.revised else ROOT/'results/wandb_runs.json'
    target.write_text(json.dumps(index,indent=2))


if __name__=='__main__':
    main()
