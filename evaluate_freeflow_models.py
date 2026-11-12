"""Populate matched dev evaluations; the comparison script summarizes these files."""
import argparse
import json
from pathlib import Path
import torch
from stable_baselines3 import DQN, PPO
from rl_freeflow.evaluation import evaluate
from rl_freeflow.freeze import PILOT, verify, digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--controller', choices=['fixed', 'DQN', 'PPO'], required=True)
    args = parser.parse_args()
    config = verify()
    torch.set_num_threads(1)
    for seed in ([None] if args.controller == 'fixed' else config['training_seeds']):
        model = None
        if seed is not None:
            folder = PILOT / 'training' / f'{args.controller.lower()}_{seed}'
            completed = json.loads((folder / 'completed.json').read_text())
            assert digest(folder / 'model.zip') == completed['model_sha256']
            model = (DQN if args.controller == 'DQN' else PPO).load(folder / 'model.zip', device='cpu')
        for flow in config['dev_demand_seeds']:
            folder = PILOT / 'dev' / f'{args.controller.lower()}_{seed}' / f'flow_{flow}'
            if (folder / 'metrics.json').exists():
                continue
            record = evaluate(args.controller, seed, flow, folder, model)
            print(args.controller, seed, flow, record['eligible_delay_comparison'], flush=True)


if __name__ == '__main__':
    main()
