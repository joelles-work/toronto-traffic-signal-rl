"""Upload only the seven indexed check-in runs, then verify their hosted URLs."""
import json
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
for name, suffix in [('WANDB_CACHE_DIR', 'cache'), ('WANDB_CONFIG_DIR', 'config'), ('WANDB_DATA_DIR', 'data')]:
    os.environ[name] = str(ROOT / 'wandb' / suffix)
os.environ['WANDB_MODE'] = 'online'
import wandb


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment', choices=['pilot_v1', 'freeflow_pilot_v1'], default='pilot_v1')
    args = parser.parse_args()
    index_path = ROOT / 'experiments' / args.experiment / 'wandb_runs.json'
    index = json.loads(index_path.read_text())
    api = wandb.Api(timeout=30)
    entity = api.viewer.entity
    project = 'toronto-tcs379'
    for record in index['training'] + [index['evaluation']]:
        directory = Path(record['directory']).resolve()
        if directory.parent != (ROOT / 'wandb').resolve() or not directory.is_dir():
            raise RuntimeError('Indexed run directory is outside the project or missing.')
        print('Uploading indexed run:', record['id'], flush=True)
        subprocess.run([sys.executable, '-m', 'wandb', 'sync', '--entity', entity,
                        '--project', project, str(directory)], cwd=ROOT, check=True)
        api.flush()
        run = api.run(f'{entity}/{project}/{record["id"]}')
        record['hosted_url'] = run.url
        record['hosted_state'] = run.state
        index['entity'] = entity
        index['project'] = project
        index_path.write_text(json.dumps(index, indent=2))
        print('Verified:', run.url, 'state:', run.state, flush=True)
    print('All seven check-in runs uploaded and verified.', flush=True)


if __name__ == '__main__':
    main()
