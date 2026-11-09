"""Check the installed stack using a synthetic network, not the research site."""
import os
from pathlib import Path
import subprocess
import tempfile

import sumo

os.environ['SUMO_HOME'] = sumo.SUMO_HOME

import sumolib
import traci


def main():
    from stable_baselines3 import DQN, PPO
    import sumo_rl
    import torch

    print(f'SUMO_HOME: {sumo.SUMO_HOME}')
    print(f'PyTorch: {torch.__version__}; CUDA available: {torch.cuda.is_available()}')
    print(f'Learning libraries: {DQN.__name__}, {PPO.__name__}, {sumo_rl.__name__}')
    with tempfile.TemporaryDirectory(prefix='sumo_setup_') as directory:
        network = Path(directory) / 'check.net.xml'
        subprocess.run([
            sumolib.checkBinary('netgenerate'), '--grid', '--grid.number', '3',
            '--output-file', str(network),
        ], check=True)
        traci.start([
            sumolib.checkBinary('sumo'), '--net-file', str(network),
            '--no-step-log', 'true', '--end', '10',
        ])
        try:
            for _ in range(10):
                traci.simulationStep()
            assert traci.simulation.getTime() == 10
            print('PASS: Python controlled SUMO through TraCI for 10 simulated seconds.')
        finally:
            traci.close()
    print('This empty synthetic-network check is not a Toronto simulation or research result.')


if __name__ == '__main__':
    main()
