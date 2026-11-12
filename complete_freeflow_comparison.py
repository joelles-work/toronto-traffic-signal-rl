"""Evaluate each algorithm as its three training runs finish, then summarize."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
PILOT = ROOT / 'experiments/freeflow_pilot_v1'


def wait_and_evaluate(algorithm):
    deadline = time.monotonic() + 3600
    while not all((PILOT / 'training' / f'{algorithm.lower()}_{seed}' / 'completed.json').exists() for seed in [101, 202, 303]):
        if time.monotonic() > deadline:
            raise TimeoutError(f'Training did not finish: {algorithm}')
        time.sleep(5)
    subprocess.run([sys.executable, 'evaluate_freeflow_models.py', '--controller', algorithm], cwd=ROOT, check=True)


def main():
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(wait_and_evaluate, name) for name in ['DQN', 'PPO']]
        for future in futures:
            future.result()
    subprocess.run([sys.executable, '-m', 'rl_freeflow.compare'], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    summary = json.loads((PILOT / 'dev_summary.json').read_text())
    for name, item in summary['controllers'].items():
        print(name, item['all_runs_eligible'], item.get('pooled_case_metrics'), flush=True)


if __name__ == '__main__':
    main()
