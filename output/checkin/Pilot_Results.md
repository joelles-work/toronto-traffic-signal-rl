# Check-in pilot results

All numbers below are development results from consistent training and evaluation at 1.39 m/s pedestrian desired free-flow walking speed, not final test performance.

| Controller | Evaluations | Vehicle time loss | Entry delay | Combined vehicle proxy | Pedestrian time loss |
|---|---:|---:|---:|---:|---:|
| fixed | 5 | 54.24 | 101.89 | 156.13 | 46.79 |
| DQN | 15 | 54.24 | 101.89 | 156.13 | 46.79 |
| PPO | 15 | 55.39 | 123.56 | 178.95 | 46.66 |

Values are seconds per vehicle/person. Fixed-time has five demand-seed evaluations. Each RL algorithm has three trained policies evaluated on the same five demand seeds (15 paired cases). These are not 15 independent observed days.

## Training-seed variation

| Algorithm | Training seed | Vehicle combined proxy, mean ± demand-seed SD | Pedestrian time loss, mean ± demand-seed SD |
|---|---:|---:|---:|
| DQN | 101 | 156.13 ± 6.58 | 46.79 ± 1.41 |
| DQN | 202 | 156.13 ± 6.58 | 46.79 ± 1.41 |
| DQN | 303 | 156.13 ± 6.58 | 46.79 ± 1.41 |
| PPO | 101 | 241.03 ± 12.45 | 46.15 ± 1.39 |
| PPO | 202 | 147.70 ± 13.02 | 46.80 ± 1.55 |
| PPO | 303 | 148.10 ± 7.27 | 47.03 ± 1.64 |

## Scope and issues

- Six completed pilot models: 2,048 cycle decisions each; no architecture, reward, or epoch search.
- Test data were not generated or evaluated.
- Each action preserves the 120-second cycle and all yellow, all-red, and pedestrian-clearance stages.
- Training seed 202 initially stopped after a local W&B connection failure. That attempt was archived and excluded, and the seed restarted from scratch with unchanged settings.
- The original prototype and its 180.37 s vehicle time-loss result are not comparable to this revised multimodal model.
- Repeated stochastic episodes do not add independent observed traffic days. Time-blocked cross-validation and field calibration remain future work.
- Hosted evidence: https://github.com/joelles-work/toronto-traffic-signal-rl and https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379 . Per-run URLs are indexed in experiments/freeflow_pilot_v1/wandb_runs.json.

Detailed machine-readable results and exploratory paired bootstrap intervals: `experiments/freeflow_pilot_v1/dev_summary.json`.