"""Replay a trained pilot policy in SUMO-GUI using its frozen dev inputs."""
import argparse
from pathlib import Path
import torch
import sumolib
import traci
from stable_baselines3 import DQN,PPO
from rl.freeze import ROOT,PILOT,verify
import rl.environment as environment


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--algorithm',choices=['DQN','PPO'],default='DQN')
    parser.add_argument('--training-seed',type=int,choices=[101,202,303],default=101)
    parser.add_argument('--flow-seed',type=int,choices=[11,22,33,44,55],default=11)
    args=parser.parse_args()
    verify()
    folder=PILOT/'training'/f'{args.algorithm.lower()}_{args.training_seed}'
    if not (folder/'completed.json').exists():
        raise SystemExit('This training run is not complete yet. Check experiments/pilot_v1/training/.')
    torch.set_num_threads(1)
    model=(DQN if args.algorithm=='DQN' else PPO).load(folder/'model.zip',device='cpu')
    original_start=traci.start
    def start_gui(command):
        command=list(command)
        command[0]=sumolib.checkBinary('sumo-gui')
        command+=['--start','--delay','25','--gui-settings-file',str(ROOT/'models/eglinton_danforth/view.xml')]
        return original_start(command)
    # Reuse the identical controller and observation implementation; substitute
    # the socket TraCI backend only, because Windows libsumo does not support GUI.
    environment.sim=traci
    traci.start=start_gui
    env=environment.IntersectionEnv('dev',flow_seed=args.flow_seed,
        output=PILOT/'replays'/f'{args.algorithm.lower()}_{args.training_seed}_{args.flow_seed}')
    try:
        obs,_=env.reset(seed=args.flow_seed)
        done=False
        while not done:
            action=int(model.predict(obs,deterministic=True)[0])
            duration=env.phase_durations(action)
            print(f'Time {env.time}s: EW WALK {duration[3]}s; NS WALK {duration[7]}s',flush=True)
            obs,_,done,_,_=env.step(action)
    finally:
        env.close()


if __name__=='__main__':
    main()
