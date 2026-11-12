"""Cycle-level signal control with immutable yellow/all-red/pedestrian clearances."""
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import libsumo as sim
import sumolib
from .freeze import ASSETS, PILOT, WALK_ALLOCATIONS, verify
from .demand import generate


class IntersectionEnv(gym.Env):
    metadata={'render_modes':[]}

    def __init__(self,split='train',flow_seed=None,output=None,fixed=False):
        verify()
        if split not in ('train','dev'):
            raise ValueError('Test simulation is disabled.')
        self.split=split
        self.flow_seed=flow_seed
        self.output=Path(output) if output else None
        self.fixed=fixed
        self.action_space=spaces.Discrete(len(WALK_ALLOCATIONS))
        self.observation_space=spaces.Box(0,1,shape=(25,),dtype=np.float32)
        self.meta=json.loads((ASSETS/'provenance.json').read_text())
        net=sumolib.net.readNet(str(ASSETS/'intersection.net.xml'))
        self.capacity={a:sum(l.getLength()/7.5 for eid in self.meta['incoming'][a]
            for l in net.getEdge(eid).getLanes() if l.allows('passenger')) for a in 'nsew'}
        root=ET.parse(ASSETS/'intersection.net.xml').getroot()
        self.phase_data=[dict(p.attrib) for p in next(t for t in root.findall('tlLogic') if t.get('id')=='TCS379').findall('phase')]
        self.active=False
        self.episode=0

    def reset(self,seed=None,options=None):
        super().reset(seed=seed)
        self.close()
        flow_seed=self.flow_seed if self.flow_seed is not None else int(self.np_random.integers(1,2**30))
        route,self.audit=generate(self.split,flow_seed)
        self.current_flow_seed=flow_seed
        self.duration=self.audit['duration']
        self.horizon=self.duration+3600
        self.time=0
        self.previous_action=3
        self.episode+=1
        self.total_reward=0.0
        self.collisions=0
        self.teleports=0
        self.emergency_braking=0
        self.output_files={}
        args=['sumo','-n',str(ASSETS/'intersection.net.xml'),'-r',str(route),
            '--seed',str(flow_seed),'--end',str(self.horizon),
            '--time-to-teleport','-1','--no-step-log','true','--no-warnings','true',
            '--duration-log.disable','true','--xml-validation','never']
        if self.output:
            self.output.mkdir(parents=True,exist_ok=True)
            for option,name in [('tripinfo-output','tripinfo.xml'),('personinfo-output','personinfo.xml'),('statistic-output','statistics.xml')]:
                self.output_files[name]=self.output/name
                args+=['--'+option,str(self.output/name)]
            args+=['--tripinfo-output.write-unfinished','true']
        else:
            runtime=PILOT/'runtime'
            runtime.mkdir(parents=True,exist_ok=True)
            self.output_files['statistics.xml']=runtime/f'training_statistics_{os.getpid()}.xml'
            args+=['--statistic-output',str(self.output_files['statistics.xml'])]
        sim.start(args)
        self.active=True
        return self._observation(),{'flow_seed':flow_seed,'split':self.split}

    @staticmethod
    def phase_durations(action):
        ew=WALK_ALLOCATIONS[int(action)]
        durations=[7,3,1,ew,22,4,3,39-ew,34,4,3]
        assert sum(durations)==120 and min(ew,39-ew)>=7
        return durations

    def _apply_action(self,action):
        durations=self.phase_durations(action)
        phases=[]
        for duration,data in zip(durations,self.phase_data):
            phase=sim.trafficlight.Phase(float(duration),data['state'])
            phase.name=data['name']
            phases.append(phase)
        logic=sim.trafficlight.Logic('constrained_policy',0,0,phases)
        sim.trafficlight.setProgramLogic('TCS379',logic)
        sim.trafficlight.setProgram('TCS379','constrained_policy')
        sim.trafficlight.setPhase('TCS379',0)
        sim.trafficlight.setPhaseDuration('TCS379',7.0)

    def _counts(self):
        queues={a:sum(sim.edge.getLastStepHaltingNumber(e) for e in self.meta['incoming'][a]) for a in 'nsew'}
        counts={a:sum(sim.edge.getLastStepVehicleNumber(e) for e in self.meta['incoming'][a]) for a in 'nsew'}
        pending={a:0 for a in 'nsew'}
        for pid in sim.simulation.getPendingVehicles():
            arm=self.audit['vehicle_arms'].get(pid)
            if arm:
                pending[arm]+=1
        peds={a:0 for a in 'nsew'}
        max_wait={a:0.0 for a in 'nsew'}
        for pid in sim.person.getIDList():
            arm=pid.split('_')[1]
            if sim.person.getSpeed(pid)<0.1:
                peds[arm]+=1
                max_wait[arm]=max(max_wait[arm],sim.person.getWaitingTime(pid))
        return counts,queues,pending,peds,max_wait

    def _observation(self):
        counts,queues,pending,peds,max_wait=self._counts()
        values=[]
        for arm in 'nsew':
            values.extend([counts[arm]/self.capacity[arm],queues[arm]/self.capacity[arm],
                pending[arm]/500,peds[arm]/50,max_wait[arm]/600])
        values += [float(a==self.previous_action) for a in range(len(WALK_ALLOCATIONS))]
        return np.clip(values,0,1).astype(np.float32)

    def step(self,action):
        if not self.active:
            raise RuntimeError('Reset the environment before stepping.')
        action=int(action)
        if not self.action_space.contains(action):
            raise ValueError(action)
        if not self.fixed:
            self._apply_action(action)
        elif action!=3:
            raise ValueError('The documented fixed-time baseline must use action 3 (31/8 s).')
        self.previous_action=action
        reward=0.0
        done=False
        for _ in range(24):
            # SUMO still advances internally at one-second resolution; Python
            # samples the queue reward every five seconds. Final statistics
            # retain safety events from every internal simulation step.
            sim.simulationStep(float(min(self.time+5,self.horizon)))
            self.time=int(sim.simulation.getTime())
            _,queues,pending,peds,_=self._counts()
            reward-=5*(sum(queues.values())+sum(pending.values())+sum(peds.values()))/1200
            if self.time>=self.horizon or (self.time>=self.duration and sim.simulation.getMinExpectedNumber()==0):
                done=True
                break
        self.total_reward+=reward
        obs=self._observation()
        info={'flow_seed':self.current_flow_seed,'simulated_seconds':self.time,
            'collisions':self.collisions,'teleports':self.teleports,'episode_reward':self.total_reward}
        if done:
            info['unfinished']=int(sim.simulation.getMinExpectedNumber())
            if info['unfinished']:
                # Account for demand still queued after the maximum drain period.
                reward-=info['unfinished']
                self.total_reward-=info['unfinished']
            info['episode_reward']=self.total_reward
            self.close()
            stats=ET.parse(self.output_files['statistics.xml']).getroot()
            info['collisions']=int(stats.find('safety').get('collisions'))
            info['teleports']=int(stats.find('teleports').get('total'))
        return obs,float(reward),done,False,info

    def close(self):
        if self.active:
            sim.close()
            self.active=False
