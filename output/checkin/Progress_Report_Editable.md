# Evaluating Deep Reinforcement Learning for Traffic Signal Control Under Real Toronto Demand

Jowel Akkeh - GS/ESS 5420 - November 13, 2026

This study compares Deep Q-Network (DQN), Proximal Policy Optimization (PPO), and fixed-time signal control at Eglinton Avenue East and Danforth Road using SUMO and observed Toronto vehicle and pedestrian counts. Training and evaluation use 1.39 m/s pedestrian free-flow speed, with six trained models evaluated on five shared development traffic patterns. These results do not establish a consistent improvement over fixed-time control. Methods, validation and code are documented with linked evidence.

## METHOD

The study models Eglinton Avenue East and Danforth Road (TCS 379) using vehicle turning movements and pedestrian crossing totals recorded every 15 minutes in the Toronto Open Data Portal [1]. Training uses June 19, 2024, 15:00-17:00, while development (dev) uses 17:00-18:00 to compare controllers and guide later changes. The rows in Table I were saved before experiments; neither reserved test period has been used to measure performance.

Each simulation starts empty, with no shared trips between periods; repeated arrival patterns represent the same observed days [2].

Table I: STUDY PERIODS AND COUNTS (2024)

| Set / date / time | Intervals | Vehicles | People |
| --- | --- | --- | --- |
| Train: Jun. 19, 15-17 | 8 | 6,716 | 810 |
| Dev: Jun. 19, 17-18 | 4 | 3,594 | 518 |
| Test: Nov. 2, 15-18 | 12 | 9,961 | 1,598 |
| Test: Jun. 19, 07-10 | 12 | 8,275 | 661 |

TorontoSUMONetworks provides a reference for Toronto data and SUMO network preparation [3]. Study-specific scripts build the intersection, convert counts into trips and apply the signal plan, while Stable-Baselines3 [4] supplies DQN/PPO implementations paired with traffic/pedestrian observations, timing choices, a waiting reward, and matched evaluation scripts [2].

Each algorithm used seeds 101, 202 and 303 with 2,048 timing decisions per run [2]. Seeded repetitions assess variability [5]; these integer identifiers were fixed in advance. Table II explains the shared presets, used without a parameter search [6]. Runs used Windows, Python 3.14.6 and an Intel CPU with 20 logical processors, without a GPU. The source register documents every preset and evidence limit [7].

Table II: TRAINING PRESETS AND THEIR PURPOSE

| Setting | Value and purpose |
| --- | --- |
| Network | Two layers of 64 neurons: a small shared architecture for 25 inputs and five timing choices. |
| Learning rate | 0.0003: small learning updates; PPO default, also used for DQN to share one preset rate. |
| Discount / batch | 0.99 weights future reward; batches of 64 experiences average each update while limiting CPU cost. |
| Training budget | 2,048 decisions: the same bounded pilot budget for each model. |
| DQN memory / start | Capacity 20,000 experiences limits replay memory; collect 180 initial experiences before learning starts. |
| DQN exploration | Final random-action probability 0.05 retains 5% exploration during training. Evaluation uses deterministic choices. |
| PPO collection | 256 new decisions per update gives eight collection blocks within the pilot budget. |
| PPO updates | 10 passes through each block reuse its data; GAE 0.95 balances short- and longer-term reward estimates (library defaults). |

The OpenStreetMap layout [8] was checked against Google Maps and includes turning lanes, sidewalks and four crossings. Observed vehicle and pedestrian counts come from Toronto Open Data [1]; within-interval arrivals and balanced walking directions follow the declared protocol [2]. Training and evaluation use SUMO's 1.39 m/s desired free-flow pedestrian speed [9].

The fixed-time baseline follows a 120-second cycle based on the City's PM timing card [10]: east-west green includes 31 seconds of WALK and 22 seconds of crossing clearance, while north-south green includes 8 seconds of WALK and 34 seconds of clearance. The 7-second east-west left-turn advance, yellow, and all-red stages are retained. Vehicle-detector requests, which can extend or request a signal phase when traffic is detected, are disabled so the baseline repeats the same documented timing plan.

At the beginning of each 120-second cycle, DQN or PPO reads vehicle queues, vehicles waiting to enter, and pedestrian waiting, then sets the east-west WALK duration to 7, 19, 25, 31, or 32 seconds. North-south receives the remainder of 39 seconds, so 31 seconds east-west leaves 8 seconds north-south and reproduces the baseline. The cycle length, stage order, yellow, all-red, and crossing clearance times stay fixed. The grid is declared in the protocol [2], with a 7-s floor from the City's usual-conditions guidance [11].

The Stable-Baselines3 controllers [4] exchange traffic conditions and timing choices with SUMO through Python [12], using a reward that penalizes waiting vehicles and pedestrians equally every five seconds, includes vehicles waiting outside the network, and adds a penalty for unfinished trips. Each training episode covers the two-hour demand period and allows up to one extra hour for traffic to clear [2].

Vehicle delay combines SUMO timeLoss and departDelay, retaining queues outside the modeled approaches [13]. Pedestrian delay uses walking timeLoss, while completion, collisions, teleports and emergency braking are recorded alongside both measures.

## FIRST EXPERIMENTS

Traffic seeds 11, 22, 33, 44 and 55 were fixed in the protocol [2] for paired comparisons, with five-run benchmark precedent [14]. Results use mean +/- sample standard deviation across these patterns. All 3,594 vehicles and 518 pedestrians finished each fixed-time run, giving 156.13 +/- 6.58 s/vehicle and 46.79 +/- 1.41 s/person.

Before training, the Python interface reproduced fixed-time results exactly and passed checks for all five timing choices. Earlier traces matched the signal sequence for 60 cycles and the intended crossing for all 518 pedestrians, with no conflicting protected greens in SUMO's checks [2].

The six final saved models were evaluated on the baseline's five traffic patterns, giving 15 evaluations per algorithm. Table III reports means. DQN selected the baseline's 31/8-second WALK split in every evaluated cycle and therefore produced identical delay.

Table III: AVERAGE DELAY ON THE DEVELOPMENT PERIOD

| Controller | Vehicle delay (s/vehicle) | Pedestrian delay (s/person) |
| --- | --- | --- |
| fixed | 156.13 | 46.79 |
| DQN | 156.13 | 46.79 |
| PPO | 178.95 | 46.66 |

PPO averaged 178.95 s/vehicle and 46.66 s/person, with a between-training-run vehicle-delay standard deviation of 53.77 seconds; 2 runs had lower vehicle delay than fixed-time. Possible explanations include the short training budget and a reward based on waiting rather than travel delay, but neither explanation has been tested separately.

The matched comparison was repeated 4,000 times by drawing training runs and traffic patterns from the existing results, allowing repeats. The estimated 95% range for PPO minus fixed-time was -11.17 to +82.79 s/vehicle and -0.67 to +0.36 s/person. These results do not establish a consistent improvement over fixed-time control. Across all 35 dev evaluations, completion and safety-event counts are retained in the evidence [15].

A dev-only check tested the five timing choices as constant plans on five shared traffic patterns [7]. The 32/7 plan gave 142.97 +/- 11.37 s/vehicle and 46.98 +/- 1.44 s/person; 7/32 left 540 vehicles unfinished. Pending-entry observations clipped 29 times, all in incomplete cases. Rescoring pedestrian weights 0, 0.5, 1 and 2 preferred the same completed constant plan, without testing retraining at these weights.

## EVIDENCE, PROBLEMS, AND NEXT STEPS

The GitHub repository contains the code, frozen splits, models, and results [2], while W&B records the six training runs and their matched dev comparison [15]. The report uses the consistent 1.39 m/s experiment under experiments/freeflow_pilot_v1; earlier experiments remain archived in the repository. The full assumption/source register and follow-up dev validation are also linked [7].

An initial routing error allowed 62 south-side pedestrians to use an unintended nearby crossing; the network was corrected and routes checked again without changing Toronto's counts. During the current experiment, a local W&B logging connection interrupted seed 202 before a final model was saved; that attempt was excluded and the seed restarted from scratch with the same settings.

The next revision should replace the pending-entry scale with train-derived origin-count bounds and retrain before evaluating its effect [7]. Further work will examine training length, reward design and an adaptive baseline on dev. Additional development periods require a documented split revision; test periods remain unused until final model selection.

## References
[1] City of Toronto, "Traffic volumes - multimodal intersection turning movement counts," Toronto Open Data. Dataset and dictionary (https://open.toronto.ca/dataset/traffic-volumes-at-intersections-for-all-modes/), accessed Nov. 11, 2026.
[2] J. Akkeh, "Toronto traffic signal RL check-in," GitHub. Code, saved models, and report (https://github.com/joelles-work/toronto-traffic-signal-rl), Nov. 11, 2026.
[3] TorontoSUMONetworks contributors, "TorontoSUMONetworks," GitHub, revision 35dee7b. Source project (https://github.com/Jahandad-Baloch/TorontoSUMONetworks), accessed Nov. 11, 2026.
[4] A. Raffin et al., "Stable-Baselines3: Reliable Reinforcement Learning Implementations," JMLR, vol. 22, no. 268, pp. 1-8, 2021. Software paper (https://jmlr.org/papers/v22/20-1364.html).
[5] P. Henderson et al., "Deep Reinforcement Learning that Matters," AAAI, 2018. Reproducibility and random seeds (https://arxiv.org/abs/1709.06560).
[6] Stable-Baselines3, "DQN and PPO parameters," v. 2.9.2. DQN (https://stable-baselines3.readthedocs.io/en/master/modules/dqn.html); PPO (https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html), accessed Nov. 12, 2026.
[7] J. Akkeh, "Assumption/source register and development validation," Nov. 13, 2026. All assumptions and sources (https://github.com/joelles-work/toronto-traffic-signal-rl/blob/master/output/literature/Assumption_and_Source_Register.md); 25-case validation (https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379/runs/wcirpdsc).
[8] OpenStreetMap contributors, "Eglinton Avenue East / Danforth Road map extract," ODbL 1.0, downloaded Nov. 9, 2026. Attribution and licence (https://www.openstreetmap.org/copyright).
[9] Eclipse SUMO, "Persons: desired maximum walking speed." Default 1.39 m/s (https://sumo.dlr.de/docs/Specification/Persons.html), accessed Nov. 12, 2026.
[10] City of Toronto, "Current Signal Timing Information: TCS 379," Oct. 31, 2019, in WSP, 320 McCowan Road Transportation Impact Study, Feb. 14, 2020, App. B, PDF p. 147. Source report (https://320mccowan.ca/wp-content/uploads/2020/04/TransportationReport_320McCowan.pdf).
[11] City of Toronto, "Pedestrian Timing at Signalised Intersections," version 2.0, May 6, 2019, sec. 2.2. Usual-conditions WALK minimum (https://www.toronto.ca/wp-content/uploads/2020/08/945f-TS_Traffic-Management_Pedestrian-Timing-Guidelines-2020.pdf).
[12] Eclipse SUMO, "Libsumo." Documentation (https://sumo.dlr.de/docs/Libsumo.html), accessed Nov. 11, 2026.
[13] Eclipse SUMO, "TripInfo." Metric definitions (https://sumo.dlr.de/docs/Simulation/Output/TripInfo.html), accessed Nov. 11, 2026.
[14] J. Ault and G. Sharon, "Reinforcement Learning Benchmarks for Traffic Signal Control," NeurIPS Datasets and Benchmarks, 2021. Five-seed evaluation (https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/file/f0935e4cd5920aa6c7c996a5ee53a70f-Paper-round1.pdf).
[15] J. Akkeh, "Toronto TCS 379 pilot experiment records," Weights & Biases. Project and training runs (https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379); dev comparison (https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379/runs/109ddkqr), uploaded Nov. 12, 2026.