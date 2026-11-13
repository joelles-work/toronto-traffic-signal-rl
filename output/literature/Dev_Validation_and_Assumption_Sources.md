# Development Validation and Assumption Sources

November 13, 2026

November 13, 2026 | Small check-in validation | Development data only

The validation tested all five allowed timing choices as constant plans on the same five traffic seeds, keeping observed counts, 1.39 m/s walking speed, geometry and signal transitions fixed. The protocol was saved before these 25 cases ran [E2](https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379/runs/wcirpdsc); no test data or new RL training were used, and the 31/8 plan reproduced every frozen baseline result exactly.

## 1. The strongest simple plan is a useful comparison

Mean +/- sample standard deviation is reported across five traffic patterns. The 7/32 plan left 540 vehicles unfinished across five cases (108 per case on average), so its completed-trip delay is not ranked. All other constant plans completed their demand without collisions or teleports [E2](https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379/runs/wcirpdsc).

| EW/NS WALK (s) | Vehicle delay (s/vehicle) | Pedestrian delay (s/person) | Completion |
| --- | --- | --- | --- |
| 7/32 | Not ranked | Not ranked | 0/5 complete |
| 19/20 | 364.02 +/- 18.71 | 46.12 +/- 1.31 | 5/5 complete |
| 25/14 | 242.29 +/- 14.25 | 46.11 +/- 1.44 | 5/5 complete |
| 31/8 | 156.13 +/- 6.58 | 46.79 +/- 1.41 | 5/5 complete |
| 32/7 | 142.97 +/- 11.37 | 46.98 +/- 1.44 | 5/5 complete |

The dev-selected 32/7 plan reduced vehicle delay by 13.16 s/vehicle relative to 31/8, while pedestrian delay increased by 0.18 s/person. The paired exploratory intervals were -17.66 to -8.27 s/vehicle and -0.02 to +0.39 s/person [E2](https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379/runs/wcirpdsc). Selection and comparison used the same dev hour, so these are development findings rather than an independently confirmed improvement or a multiplicity-adjusted significance claim.

## 2. Observation scaling has a demonstrated limit

The west pending-entry feature exceeded its scale of 500 in 29 of 1,149 decision observations (2.52%), reaching 562/500 = 1.124. Every clipped observation occurred in the incomplete 7/32 cases; the twenty completed cases had none [E2](https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379/runs/wcirpdsc). Therefore, 500 is adequate for the completed constant cases examined, but cannot be justified as a general bound for the current action space.

A concrete candidate replacement divides pending entries by the full training-period vehicle count for each origin arm: north 1,280, south 1,262, east 2,038 and west 2,136 [E3](https://github.com/joelles-work/toronto-traffic-signal-rl/blob/master/experiments/dev_assumptions_v1/derived_checks.json). A pending queue cannot exceed all vehicles generated at its origin, and the dev totals are lower than these training totals. This supplies a train-derived bound for these fixed data windows, but changes the input scale and must be followed by retraining before reporting new policy performance. It is a proposed revision, not an implemented improvement.

## 3. Pedestrian-weight sensitivity is local evidence

For the same trajectories, pedestrian weights 0, 0.5, 1 and 2 all preferred constant 32/7 among the four complete plans [E2](https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379/runs/wcirpdsc). This supports local robustness of that constant-plan ranking to those weights; it neither proves weight 1 is ethically or operationally optimal nor measures how PPO/DQN would learn after changing the reward. Vehicles are counted as units, without bus-passenger occupancy weighting.

## 4. The WALK bound has an official source

Toronto's timing guidance specifies a 7-s WALK minimum for Type A usual conditions, with separate clearance and total-crossing-time criteria [D10](https://www.toronto.ca/wp-content/uploads/2020/08/945f-TS_Traffic-Management_Pedestrian-Timing-Guidelines-2020.pdf). Using the modeled crossing lengths, all five plans pass twenty conditional checks of those inequalities [E3](https://github.com/joelles-work/toronto-traffic-signal-rl/blob/master/experiments/dev_assumptions_v1/derived_checks.json). This supports the lower-bound source and model arithmetic, not the choice of every intermediate allocation or field certification. The 1.39 m/s desired simulation speed is separate from the City's timing-design criteria.

## 5. How to cite seeds and all other assumptions

Three independently seeded training repetitions (101, 202 and 303) were used to assess training variability, following recommendations for reproducible RL evaluation [P9](https://arxiv.org/abs/1709.06560). Five common simulation seeds (11, 22, 33, 44 and 55) generated paired traffic patterns for all controllers, consistent with five-run traffic benchmarking [P4](https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/file/f0935e4cd5920aa6c7c996a5ee53a70f-Paper-round1.pdf). The seed identifiers were fixed before training [E1](https://github.com/joelles-work/toronto-traffic-signal-rl/blob/master/experiments/freeflow_pilot_v1/experiment.json); their numeric values carry no claimed statistical advantage.

The companion Assumption and Source Register maps every declared design, training and evaluation choice to a research source, software definition, site record or our own frozen protocol. For unsupported exact values, the register cites the protocol as the origin and states what remains untested; it does not use a citation to imply external proof.

## Decision for the check-in

Retain the existing pilot as a completed, explicitly bounded experiment; add the stronger constant-plan comparison and disclose the clipping finding. Cite the City source for the conditional WALK minimum and the RL evaluation sources for repeated seeded runs. The pending-entry scale has a concrete train-derived replacement ready for the next training revision. Neither the frozen RL settings nor reported model results were silently changed.

## Linked sources

[P9](https://arxiv.org/abs/1709.06560) Henderson et al. (2018), Deep Reinforcement Learning that Matters

[P4](https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/file/f0935e4cd5920aa6c7c996a5ee53a70f-Paper-round1.pdf) Ault and Sharon (2021), Reinforcement Learning Benchmarks for Traffic Signal Control

[D10](https://www.toronto.ca/wp-content/uploads/2020/08/945f-TS_Traffic-Management_Pedestrian-Timing-Guidelines-2020.pdf) City of Toronto, Pedestrian Timing at Signalised Intersections, May 6, 2019; Sections 2.1-2.2, 4.7

[E1](https://github.com/joelles-work/toronto-traffic-signal-rl/blob/master/experiments/freeflow_pilot_v1/experiment.json) Frozen freeflow_pilot_v1 protocol

[E2](https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379/runs/wcirpdsc) Completed dev_assumptions_v1 validation, W&B

[E3](https://github.com/joelles-work/toronto-traffic-signal-rl/blob/master/experiments/dev_assumptions_v1/derived_checks.json) Derived timing checks and proposed training-only bounds
