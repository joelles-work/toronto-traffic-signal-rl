# Check-in pilot results

All numbers below are development results, not final test performance. The model remains uncalibrated for field delay and 2024 geometry.

| Controller | Evaluations | Vehicle time loss | Entry delay | Combined vehicle proxy | Pedestrian time loss |
|---|---:|---:|---:|---:|---:|
| fixed | 5 | 55.12 | 111.09 | 166.21 | 46.93 |
| DQN | 15 | 55.12 | 111.09 | 166.21 | 46.93 |
| PPO | 15 | 58.76 | 152.55 | 211.31 | 46.61 |

Values are seconds per vehicle/person. Fixed-time has five demand-seed evaluations. Each RL algorithm has three trained policies evaluated on the same five demand seeds (15 paired cases). These are not 15 independent observed days.

## Training-seed variation

| Algorithm | Training seed | Vehicle combined proxy, mean ± demand-seed SD | Pedestrian time loss, mean ± demand-seed SD |
|---|---:|---:|---:|
| DQN | 101 | 166.21 ± 10.16 | 46.93 ± 1.43 |
| DQN | 202 | 166.21 ± 10.16 | 46.93 ± 1.43 |
| DQN | 303 | 166.21 ± 10.16 | 46.93 ± 1.43 |
| PPO | 101 | 253.89 ± 14.82 | 46.24 ± 1.65 |
| PPO | 202 | 227.53 ± 12.92 | 46.54 ± 1.54 |
| PPO | 303 | 152.52 ± 7.62 | 47.07 ± 1.41 |

## Scope and issues

- Six completed pilot models: 2,048 cycle decisions each; no architecture, reward, or epoch search.
- Test data were not generated or evaluated.
- Each action preserves the 120-second cycle and all yellow, all-red, and pedestrian-clearance stages.
- A failed preliminary attempt shared a temporary statistics file with a diagnostic run. It was archived and excluded; successful models restarted with per-process output isolation.
- The original prototype and its 180.37 s vehicle time-loss result are not comparable to this revised multimodal model.
- Repeated stochastic episodes do not add independent observed traffic days. Time-blocked cross-validation and field calibration remain future work.
- Repository publication and W&B synchronization still require authenticated account access; local evidence is complete but hosted URLs are not yet available.

Detailed machine-readable results and exploratory paired bootstrap intervals: `experiments/pilot_v1/dev_summary.json`.