"""Record the check-in dev comparison and index its actual offline W&B evidence."""
import json
import os
from pathlib import Path
from rl_freeflow.freeze import ROOT,PILOT,verify

for key,suffix in [('WANDB_DATA_DIR','data'),('WANDB_CACHE_DIR','cache'),('WANDB_CONFIG_DIR','config')]:
    directory=ROOT/'wandb'/suffix
    directory.mkdir(parents=True,exist_ok=True)
    os.environ[key]=str(directory)
import wandb


def main():
    verify()
    summary=json.loads((PILOT/'dev_summary.json').read_text())
    records=summary['runs']
    with wandb.init(project='toronto-tcs379',mode='offline',dir=str(ROOT),
        name='freeflow-v1-matched-dev-comparison',group='constrained-freeflow-v1',
        config={'split':'dev','test_evaluated':False,'training_seeds':[101,202,303],
            'pedestrian_desired_speed_m_s':1.39,'demand_seeds':[11,22,33,44,55],'recording':'post-hoc import of completed matched evaluations','experiment':'freeflow_pilot_v1'}) as run:
        columns=['controller','training_seed','flow_seed','vehicle_time_loss_s',
            'vehicle_depart_delay_s','vehicle_combined_delay_proxy_s','pedestrian_time_loss_s',
            'vehicles_completed','pedestrians_completed','collisions','teleports','emergency_braking',
            'eligible_delay_comparison']
        table=wandb.Table(columns=columns,data=[[r.get(c) for c in columns] for r in records])
        run.log({'dev_comparison':table})
        for controller,item in summary['controllers'].items():
            run.summary[f'{controller}/all_runs_eligible']=item['all_runs_eligible']
            for metric,value in item.get('pooled_case_metrics',{}).items():
                run.summary[f'{controller}/{metric}']=value['mean']
        artifact=wandb.Artifact('freeflow-v1-dev-evidence',type='evaluation')
        for p in [PILOT/'dev_summary.json',PILOT/'experiment.json',PILOT/'implementation.json',
            PILOT/'checks/smoke.json',PILOT/'checks/fixed_dev_seed11/metrics.json']:
            artifact.add_file(str(p),name=p.name)
        run.log_artifact(artifact)
        evaluation={'kind':'dev_comparison','id':run.id,'directory':str(Path(run.dir).parent),'hosted_url':None}
    training=[]
    for p in sorted((PILOT/'training').glob('*/completed.json')):
        record=json.loads(p.read_text())
        training.append({'kind':'training','algorithm':record['algorithm'],'seed':record['training_seed'],
            'id':record['wandb_id'],'directory':record['wandb_directory'],'hosted_url':None})
    (PILOT/'wandb_runs.json').write_text(json.dumps({'training':training,'evaluation':evaluation},indent=2))


if __name__=='__main__':
    main()
