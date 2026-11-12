"""Train the preregistered DQN/PPO pilot; no dev or test access during learning."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import time

import torch
from stable_baselines3 import DQN,PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from .freeze import ROOT,PILOT,SEEDS,freeze,verify,digest
from .environment import IntersectionEnv

for key,suffix in [('WANDB_DATA_DIR','data'),('WANDB_CACHE_DIR','cache'),('WANDB_CONFIG_DIR','config')]:
    p=ROOT/'wandb'/suffix
    p.mkdir(parents=True,exist_ok=True)
    os.environ[key]=str(p)
import wandb


def now():
    return datetime.now(timezone.utc).isoformat()


class Progress(BaseCallback):
    def __init__(self,folder,run,algorithm,seed,budget):
        super().__init__()
        self.folder=folder
        self.run=run
        self.algorithm=algorithm
        self.seed=seed
        self.budget=budget
        self.start=time.perf_counter()
        self.episodes=[]

    def _on_step(self):
        for info in self.locals.get('infos',[]):
            if 'episode' in info:
                record={'decision':self.num_timesteps,'flow_seed':int(info['flow_seed']),
                    'reward':float(info['episode']['r']),'decisions':int(info['episode']['l']),
                    'unfinished':int(info.get('unfinished',0)),'collisions':int(info['collisions']),
                    'teleports':int(info['teleports'])}
                self.episodes.append(record)
                with (self.folder/'episodes.jsonl').open('a') as f:
                    f.write(json.dumps(record)+'\n')
                self.run.log({'episode_reward':record['reward'],'unfinished':record['unfinished'],
                    'collisions':record['collisions'],'teleports':record['teleports'],
                    'training_decisions':self.num_timesteps})
        if self.num_timesteps%64==0 or self.num_timesteps==self.budget:
            status={'algorithm':self.algorithm,'training_seed':self.seed,'decisions':self.num_timesteps,
                'budget':self.budget,'episodes_completed':len(self.episodes),
                'elapsed_s':time.perf_counter()-self.start,'updated_utc':now(),
                'last_episode':self.episodes[-1] if self.episodes else None,'status':'training'}
            (self.folder/'progress.json').write_text(json.dumps(status,indent=2))
            print(json.dumps(status),flush=True)
        if self.num_timesteps%512==0:
            self.model.save(self.folder/'checkpoint')
        return True


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--algorithm',choices=['DQN','PPO','both'],default='both')
    parser.add_argument('--training-seed',type=int,choices=SEEDS)
    args=parser.parse_args()
    config=freeze()
    smoke=PILOT/'checks/smoke.json'
    if not smoke.exists() or json.loads(smoke.read_text()).get('result')!='PASS':
        raise RuntimeError('Run python -m rl.smoke successfully before training.')
    torch.set_num_threads(1)
    implementation={p.name:digest(p) for p in (ROOT/'rl_freeflow').glob('*.py')}
    implementation_path=PILOT/'implementation.json'
    if implementation_path.exists():
        assert json.loads(implementation_path.read_text())==implementation,'Experiment code changed after training freeze.'
    else:
        implementation_path.write_text(json.dumps(implementation,indent=2))
    algorithms=['DQN','PPO'] if args.algorithm=='both' else [args.algorithm]
    for seed in ([args.training_seed] if args.training_seed is not None else SEEDS):
        for algorithm in algorithms:
            verify()
            folder=PILOT/'training'/f'{algorithm.lower()}_{seed}'
            folder.mkdir(parents=True,exist_ok=True)
            if (folder/'completed.json').exists():
                print(f'Already complete: {algorithm} seed {seed}',flush=True)
                continue
            start=time.perf_counter()
            budget=config['decision_budget_per_model']
            record={'algorithm':algorithm,'training_seed':seed,'budget':budget,'started_utc':now(),
                'experiment_sha256':digest(PILOT/'experiment.json'),'implementation':implementation,
                'training_split':'train','dev_used_for_learning':False,'test_used':False}
            (folder/'run.json').write_text(json.dumps(record,indent=2))
            run=wandb.init(project='toronto-tcs379',mode='offline',dir=str(ROOT),
                name=f'freeflow-v1-{algorithm.lower()}-{seed}',group='constrained-freeflow-v1',
                config={**record,'hyperparameters':config[algorithm]})
            env=Monitor(IntersectionEnv('train'),filename=str(folder/'monitor.csv'))
            try:
                cls=DQN if algorithm=='DQN' else PPO
                model=cls('MlpPolicy',env,seed=seed,device='cpu',verbose=0,**config[algorithm])
                callback=Progress(folder,run,algorithm,seed,budget)
                model.learn(total_timesteps=budget,callback=callback,progress_bar=False)
                model.save(folder/'model')
                record.update(status='complete',finished_utc=now(),elapsed_s=time.perf_counter()-start,
                    actual_decisions=int(model.num_timesteps),episodes_completed=len(callback.episodes),
                    model_sha256=digest(folder/'model.zip'),wandb_id=run.id,
                    wandb_directory=str(Path(run.dir).parent),wandb_hosted_url=None)
                (folder/'completed.json').write_text(json.dumps(record,indent=2))
                run.summary.update({'status':'complete','actual_decisions':model.num_timesteps,
                    'episodes_completed':len(callback.episodes),'elapsed_s':record['elapsed_s']})
                artifact=wandb.Artifact(f'freeflow-v1-{algorithm.lower()}-{seed}',type='model')
                for p in [folder/'model.zip',folder/'run.json',folder/'completed.json',
                          PILOT/'experiment.json',PILOT/'implementation.json',smoke]:
                    artifact.add_file(str(p),name=p.name)
                run.log_artifact(artifact)
                print(json.dumps(record),flush=True)
            except Exception as exc:
                run.summary.update({'status':'failed','error':str(exc)})
                (folder/'failed.json').write_text(json.dumps({'error':repr(exc),'time_utc':now()},indent=2))
                raise
            finally:
                env.close()
                run.finish()


if __name__=='__main__':
    main()
