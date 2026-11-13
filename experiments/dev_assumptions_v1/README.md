# Small development validation and assumption sources

This follow-up keeps the check-in scope: 25 constant-plan simulations at 1.39 m/s on dev only. The original 35-case RL comparison remains frozen. No model was retrained and no test data were simulated.

Run: `.venv\Scripts\python.exe validate_pilot_assumptions.py`.

`plan.json` was written before these simulations, with the source experiment hash and validation-code hash. `summary.json` includes every case, completion flags, descriptive means, exploratory paired intervals, observation clipping and reward rescoring. `derived_checks.json` separately records conditional City Type A timing inequalities and proposed train-derived pending-entry bounds.

## Findings

- Constant 32/7 WALK timing: 142.97 +/- 11.37 s/vehicle and 46.98 +/- 1.44 s/person across five traffic patterns. It was selected and measured on the same dev hour, not confirmed on independent test data.
- Documented 31/8 timing: 156.13 +/- 6.58 s/vehicle and 46.79 +/- 1.41 s/person. Exact parity with the frozen baseline passed for every traffic seed.
- Constant 7/32 timing left 540 vehicles unfinished across five cases; its completed-trip delay is not ranked.
- The west pending-entry feature clipped in 29 of 1,149 decision observations, all in incomplete 7/32 cases. No clipping was recorded in the twenty complete cases.
- Pedestrian weights 0, 0.5, 1 and 2 preferred constant 32/7 when rescoring the same complete trajectories. This is not an experiment retraining policies with each weight.

## Seeds and citations

Training seeds 101, 202, 303 and traffic seeds 11, 22, 33, 44, 55 are predeclared identifiers, not claimed scientifically optimal numbers. Multiple seeded runs are motivated by [Henderson et al., 2018](https://arxiv.org/abs/1709.06560), and five-run traffic evaluation has precedent in [Ault and Sharon, 2021](https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/file/f0935e4cd5920aa6c7c996a5ee53a70f-Paper-round1.pdf).

The 7-s WALK floor has a conditional source in [Toronto's usual-conditions timing guidance, version 2.0, May 6, 2019](https://www.toronto.ca/wp-content/uploads/2020/08/945f-TS_Traffic-Management_Pedestrian-Timing-Guidelines-2020.pdf). That guidance distinguishes other pedestrian populations and timing-design speeds; it is not a validation of this site's current field geometry or population mix.

The full current source register is `output/literature/Assumption_and_Source_Register.md`. It supersedes the initial literature audit for the newly sourced WALK minimum and observed clipping result. Its sources distinguish research precedent, software definitions, site records, and our own declared protocol.

## Proposed revision, not newly evaluated models

Replace pending-entry divisor 500 with the full train-origin counts: n=1280, s=1262, e=2038, w=2136. Queue counts cannot exceed total generated demand at their origin in these episodes, and dev counts are smaller. These bounds are derived from training counts rather than fitted to dev maxima. Changing this scale requires new training and evaluation; present model performance must not be relabeled as using it.

W&B evidence: https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379/runs/wcirpdsc . The unsuccessful cases are included.
