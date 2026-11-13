"""Small, predeclared dev-only check of constant plans, clipping and reward weights.

This does not retrain policies, open test data, or alter the frozen pilot.
Reward-weight comparisons rescore the same trajectories; they are not new
policies trained with different rewards.
"""
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import statistics
import time

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'experiments/dev_assumptions_v1'
SEEDS = [11, 22, 33, 44, 55]
WEIGHTS = [0, 0.5, 1, 2]
KEYS = ['approach_count', 'queue', 'pending_entry', 'stopped_pedestrians', 'maximum_pedestrian_wait']


def freeze_plan():
    from rl_freeflow.freeze import verify
    verify()
    OUT.mkdir(parents=True, exist_ok=True)
    plan = {
        'name': 'dev_assumptions_v1', 'status': 'declared before this validation',
        'split': 'dev', 'test_evaluated': False, 'flow_seeds': SEEDS,
        'constant_actions': list(range(5)), 'pedestrian_reward_weights': WEIGHTS,
        'source_experiment': 'experiments/freeflow_pilot_v1',
        'source_experiment_sha256': hashlib.sha256((ROOT/'experiments/freeflow_pilot_v1/experiment.json').read_bytes()).hexdigest(),
        'implementation_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'protocol': '25 new constant-action evaluations at 1.39 m/s. All five timing plans and all five paired flow seeds are reported. Source frozen inputs and existing policies remain unchanged.',
        'questions': [
            'Does a simple constant allowed plan improve on the documented 31/8 baseline on dev?',
            'Are any of the 20 numerical observation features clipped above their fixed upper scale?',
            'Does rescoring the same completed trajectories with pedestrian weights 0, 0.5, 1 or 2 change the reward-preferred constant plan?',
        ],
        'ranking_rules': 'Only plans with all demand completed and no collisions/teleports receive all-demand delay rankings. Report vehicle and pedestrian metrics separately; no combined-delay winner is assumed. Paired flow-seed intervals are exploratory dev checks, not held-out confirmation or multiplicity-corrected tests.',
        'limitations': 'Constant plans do not establish optimal adaptive actions; five repeats are one observed dev hour. Rescoring rewards does not measure the effect of retraining a controller with new weights. No new hyperparameter or convergence claim follows.',
    }
    file = OUT / 'plan.json'
    if file.exists():
        assert json.loads(file.read_text()) == plan, 'Validation protocol changed after declaration.'
    else:
        file.write_text(json.dumps(plan, indent=2))
    return plan


def run_action(action):
    import numpy as np
    from rl_freeflow.environment import IntersectionEnv
    from rl_freeflow.evaluation import read_metrics
    records = []

    class AuditedEnv(IntersectionEnv):
        def reset(self, **kwargs):
            self.in_step = False
            self.last_sample_time = -1
            self.vehicle_wait_integral = 0.0
            self.pedestrian_wait_integral = 0.0
            self.samples = 0
            self.peaks = {f'{arm}/{key}': 0.0 for arm in 'nsew' for key in KEYS}
            self.clipped = dict.fromkeys(self.peaks, 0)
            return super().reset(**kwargs)

        def _counts(self):
            data = super()._counts()
            if getattr(self, 'in_step', False) and self.time > self.last_sample_time:
                _, queues, pending, peds, _ = data
                self.vehicle_wait_integral += 5 * (sum(queues.values()) + sum(pending.values()))
                self.pedestrian_wait_integral += 5 * sum(peds.values())
                self.last_sample_time = self.time
            return data

        def _observation(self):
            counts, queues, pending, peds, waits = self._counts()
            raw = []
            names = []
            for arm in 'nsew':
                raw.extend([counts[arm]/self.capacity[arm], queues[arm]/self.capacity[arm],
                            pending[arm]/500, peds[arm]/50, waits[arm]/600])
                names.extend(f'{arm}/{key}' for key in KEYS)
            observation = super()._observation()
            assert np.allclose(observation[:20], np.clip(raw, 0, 1))
            self.samples += 1
            for name, value in zip(names, raw):
                self.peaks[name] = max(self.peaks[name], float(value))
                self.clipped[name] += int(value > 1)
            return observation

        def step(self, value):
            self.in_step = True
            try:
                return super().step(value)
            finally:
                self.in_step = False

    for flow in SEEDS:
        folder = OUT / 'runs' / f'action_{action}' / f'flow_{flow}'
        folder.mkdir(parents=True, exist_ok=True)
        env = AuditedEnv('dev', flow_seed=flow, output=folder, fixed=False)
        start = time.perf_counter()
        _, _ = env.reset(seed=flow)
        audit = env.audit
        try:
            done = False
            decisions = 0
            while not done:
                _, _, done, _, info = env.step(action)
                decisions += 1
        finally:
            env.close()
        metrics = read_metrics(folder, audit)
        unfinished = metrics['unfinished_vehicles'] + metrics['unfinished_pedestrians']
        expected = -(env.vehicle_wait_integral + env.pedestrian_wait_integral)/1200 - unfinished
        assert abs(expected - info['episode_reward']) < 1e-5, (expected, info)
        metrics.update(action=action, flow_seed=flow, ew_walk_s=env.phase_durations(action)[3],
                       ns_walk_s=env.phase_durations(action)[7], decisions=decisions,
                       vehicle_wait_integral=env.vehicle_wait_integral,
                       pedestrian_wait_integral=env.pedestrian_wait_integral,
                       episode_reward=info['episode_reward'],
                       observation_samples=env.samples, maximum_normalized_feature=env.peaks,
                       clipped_observation_count=env.clipped,
                       reward_rescores={str(w): -(env.vehicle_wait_integral+w*env.pedestrian_wait_integral)/1200-unfinished for w in WEIGHTS},
                       wall_seconds=time.perf_counter()-start)
        (folder/'metrics.json').write_text(json.dumps(metrics, indent=2))
        records.append(metrics)
        print('Action', action, 'flow', flow, 'eligible', metrics['eligible_delay_comparison'], flush=True)
    return records


def main():
    freeze_plan()
    with ProcessPoolExecutor(max_workers=3) as pool:
        groups = list(pool.map(run_action, range(5)))
    records = [r for group in groups for r in group]
    import numpy as np
    summaries = {}
    baseline = {r['flow_seed']: r for r in records if r['action'] == 3}
    for action in range(5):
        cases = [r for r in records if r['action'] == action]
        eligible = all(r['eligible_delay_comparison'] for r in cases)
        summary = {'ew_walk_s': cases[0]['ew_walk_s'], 'ns_walk_s': cases[0]['ns_walk_s'],
                   'all_cases_eligible': eligible, 'metrics': {},
                   'unfinished_vehicles': sum(r['unfinished_vehicles'] for r in cases),
                   'unfinished_pedestrians': sum(r['unfinished_pedestrians'] for r in cases),
                   'collisions': sum(r['collisions'] for r in cases), 'teleports': sum(r['teleports'] for r in cases)}
        if eligible:
            for key in ['vehicle_combined_delay_proxy_s', 'pedestrian_time_loss_s']:
                values = [r[key] for r in cases]
                diffs = np.array([r[key]-baseline[r['flow_seed']][key] for r in cases])
                rng = np.random.default_rng(5420)
                samples = diffs[rng.integers(0, 5, size=(4000, 5))].mean(axis=1)
                summary['metrics'][key] = {'mean': statistics.mean(values), 'sample_std': statistics.stdev(values),
                    'paired_difference_vs_documented_baseline': float(diffs.mean()),
                    'exploratory_95_percent_interval': [float(x) for x in np.quantile(samples, [.025, .975])]}
            summary['mean_reward_rescores'] = {str(w): statistics.mean(r['reward_rescores'][str(w)] for r in cases) for w in WEIGHTS}
        summaries[str(action)] = summary
    eligible = [int(a) for a, s in summaries.items() if s['all_cases_eligible']]
    preferred = {str(w): max(eligible, key=lambda a: summaries[str(a)]['mean_reward_rescores'][str(w)]) for w in WEIGHTS} if eligible else {}
    clipping = {name: {'samples': sum(r['observation_samples'] for r in records),
                       'clipped_samples': sum(r['clipped_observation_count'][name] for r in records),
                       'maximum_normalized_value': max(r['maximum_normalized_feature'][name] for r in records)} for name in records[0]['maximum_normalized_feature']}
    for item in clipping.values():
        item['clipped_fraction'] = item['clipped_samples']/item['samples']
    # The baseline-equivalent constant action must reproduce the frozen baseline.
    for flow in SEEDS:
        old = json.loads((ROOT/'experiments/freeflow_pilot_v1/dev/fixed_None'/f'flow_{flow}'/'metrics.json').read_text())
        for key in ['vehicle_combined_delay_proxy_s', 'pedestrian_time_loss_s']:
            assert abs(baseline[flow][key] - old[key]) < 1e-9
    result = {'plan': json.loads((OUT/'plan.json').read_text()), 'actions': summaries,
              'preferred_constant_action_by_pedestrian_weight': preferred,
              'observation_clipping': clipping, 'fixed_baseline_parity': 'PASS', 'runs': records}
    (OUT/'summary.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({'actions': summaries, 'preferred_actions': preferred, 'clipped_features': {k:v for k,v in clipping.items() if v['clipped_samples']}}, indent=2))


if __name__ == '__main__':
    main()
