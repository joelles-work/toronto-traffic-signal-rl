# Consistent pedestrian free-flow pilot

This is the current check-in experiment. Both training and development evaluation use a pedestrian desired free-flow walking speed of **1.39 m/s**, with `speedFactor=1` and `speedDev=0`. Vehicle and pedestrian counts are observed Toronto Open Data Portal counts. Within-interval arrival times and pedestrian crossing directions are modeled.

The data split, signal phases, action set, reward, architecture, training budget and other hyperparameters match the earlier bounded pilot. Test data remain inaccessible to this experiment. The earlier `pilot_v1` and `pedestrian_freeflow_v1` directories retain the historical 1.2 m/s training and the subsequent transfer check; they are not the current reported comparison.

## Reproduction

Use the project's Python environment:

```powershell
.\.venv\Scripts\python.exe -m rl_freeflow.smoke
.\.venv\Scripts\python.exe -m rl_freeflow.train
.\.venv\Scripts\python.exe -m rl_freeflow.compare
```

`smoke.py` verifies the exact paired 1.39 m/s demand, checks the Gymnasium/SB3 interface, tests 600 actual signal states across the five allowed actions, and checks fixed-time parity against the earlier 1.39 m/s fixed-time run.

Each algorithm has one preset configuration, with training seeds 101, 202 and 303 and 2,048 decisions per model. The evaluation script uses the final saved model from each training run on five common traffic seeds, 11, 22, 33, 44 and 55. These seed values were chosen as distinct, reproducible identifiers rather than selected for favorable results. The five arrival patterns preserve the same observed totals. Five fixed-time cases plus 15 cases for each learning algorithm yield 35 development evaluations.

Frozen assets and their hashes are in `experiment.json`; implementation hashes are saved before training in `implementation.json`. Per-episode learning histories, progress and final model hashes are saved under `training/`. The comparison records completion and safety events before reporting an all-demand mean. Unfinished demand or collisions/teleports invalidate a case for that delay comparison.

## Settings and interpretation

The shared network (two layers of 64 neurons), learning rate (0.0003), batch size (64), discount (0.99), and budget (2,048 decisions) are fixed comparison presets. The learning rate matches the PPO library default and was also used for DQN; this does not imply it is optimal for DQN. The small architecture and bounded data collections limit CPU and memory costs. No parameter search was performed.

DQN has capacity for 20,000 transitions, collects 180 transitions before learning, updates once per new decision, refreshes the target network every 256 decisions, and decreases random exploration over 60% of training to a final 5% probability. PPO gathers 256 decisions per update, uses minibatches of 64 for 10 passes, uses a GAE smoothing factor of 0.95, and an entropy coefficient of 0.01. These are recorded in full in the frozen configuration, with unspecified options using the installed Stable-Baselines3 defaults.

## Excluded attempt

The first attempt for training seed 202 stopped when the local W&B service connection was aborted before a final DQN model was saved. It is archived under `interrupted_attempts/dqn_202_logging_failure/`, marked excluded, and is not used in comparisons. Seed 202 was restarted from scratch with the same implementation, data and hyperparameters. Only completed runs are indexed for W&B publication.

The current GUI launchers replay these new models at 1.39 m/s. Training and dev episodes start empty; the one observed development hour and synthetic arrival repetitions do not establish performance across multiple real days. No test result is reported.
