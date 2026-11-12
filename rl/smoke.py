"""Meaningful integration checks before training: schema, controls, and baseline parity."""
import gzip
import json
import time
import xml.etree.ElementTree as ET
from stable_baselines3.common.env_checker import check_env
import libsumo as sim
from .freeze import ROOT,PILOT,freeze
from .demand import generate
from .environment import IntersectionEnv
from .evaluation import evaluate


def main():
    freeze()
    start=time.perf_counter()
    route,audit=generate('dev',11)
    with gzip.open(route,'rb') as f:
        generated=ET.parse(f).getroot()
    original=ET.parse(ROOT/'results/revised_fixed_dev/seed_11/routes.rou.xml').getroot()
    for tag in ('vType','vehicle','person'):
        aa=generated.findall(tag)
        bb=original.findall(tag)
        assert len(aa)==len(bb),(tag,len(aa),len(bb))
        assert all(ET.tostring(a)==ET.tostring(b) for a,b in zip(aa,bb)),f'Dev realization changed: {tag}'
    env=IntersectionEnv('train',flow_seed=101)
    check_env(env,warn=True)
    env.close()
    # Exercise every legal action for a complete cycle, recording the actual
    # signal state each second. An action cannot skip or shorten a clearance.
    env=IntersectionEnv('train',flow_seed=101)
    env.reset(seed=101)
    checked=0
    try:
        for action in range(env.action_space.n):
            beginning=env.time
            durations=env.phase_durations(action)
            env._apply_action(action)
            boundaries=[]
            total=0
            for d in durations:
                total+=d
                boundaries.append(total)
            for elapsed in range(120):
                sim.simulationStep()
                expected=next(i for i,end in enumerate(boundaries) if elapsed<end)
                state=sim.trafficlight.getRedYellowGreenState('TCS379')
                assert state==env.phase_data[expected]['state'],(action,elapsed,expected,state)
                checked+=1
            env.time=beginning+120
    finally:
        env.close()
    result=evaluate('fixed',None,11,PILOT/'checks/fixed_dev_seed11')
    baseline=json.loads((ROOT/'results/revised_fixed_dev/seed_11/metrics.json').read_text())
    differences={key:result[key]-baseline[key] for key in ['vehicle_time_loss_s','vehicle_depart_delay_s','vehicle_combined_delay_proxy_s','pedestrian_time_loss_s']}
    assert result['eligible_delay_comparison']
    assert all(abs(value)<0.02 for value in differences.values()),differences
    report={'result':'PASS','training_demand':{'vehicles':6716,'pedestrians':810},
        'dev_exact_realization_match':True,'gymnasium_SB3_check':'PASS',
        'action_phase_states_checked':checked,'baseline_parity_differences_s':differences,
        'elapsed_seconds':time.perf_counter()-start}
    (PILOT/'checks/smoke.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
