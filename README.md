# Toronto traffic signal research

Local setup for the supplied proposal, "Evaluating Deep Reinforcement Learning for Traffic Signal Control Under Real Toronto Demand".

## Current check-in (November 12, 2026)

The current two-page paper is `output/checkin/Progress_Report_Jowel_Akkeh.pdf`, with editable text and IEEEtran source alongside it. It reports the consistent 1.39 m/s pedestrian free-flow experiment under `experiments/freeflow_pilot_v1/`.

Both DQN and PPO were trained from scratch at 1.39 m/s using three seeds per algorithm and 2,048 cycle decisions per model. Five fixed-time runs and 15 matched dev evaluations per algorithm completed all 3,594 vehicles and 518 pedestrians in each case. Mean vehicle delay: fixed-time and DQN 156.13 s/vehicle; PPO 178.95 s/vehicle. Mean pedestrian delay: fixed-time/DQN 46.79 s/person; PPO 46.66 s/person. The paper reports training variability and uncertainty; test data remain unused.

See `experiments/freeflow_pilot_v1/README.md` for reproduction commands, frozen inputs and settings, and the excluded logging failure. `dev_summary.json` holds all results; `wandb_runs.json` indexes six verified training runs and the comparison.

Repository: https://github.com/joelles-work/toronto-traffic-signal-rl (private). W&B comparison: https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379/runs/109ddkqr . Confirm instructor access before submission.

`Watch_Trained_DQN.cmd` and `Watch_Trained_PPO.cmd` replay the new models (training seed 101, dev flow seed 11) at 1.39 m/s, without choosing a best seed. `Open_SUMO_Intersection.cmd` opens the current fixed-time simulation at the same walking speed.

Earlier experiments under `experiments/pilot_v1/` and `experiments/pedestrian_freeflow_v1/` retain the historical 1.2 m/s training and transfer check. They are not the current paper's comparison. The older report under `output/report/` is superseded.

## Open the drawn intersection

Double-click **Open_SUMO_Intersection.cmd** in this folder. It opens **Eglinton_Danforth.sumocfg** with the locally installed SUMO-GUI, without needing Windows file associations. This is the georeferenced geometry revision with separated eastern carriageways, sidewalks, crossings, 3,594 observed dev vehicles, and 518 observed dev pedestrians. Arrival times and pedestrian directions are modeled. Press the green Play button to run traffic; the simulation starts paused. Field dimensions and historical 2024 fidelity remain uncalibrated. See `models/eglinton_danforth/README.md` for provenance and assumptions.

The signal/demand audit and updated five-seed baseline are documented in `evidence/SIGNAL_AND_DEMAND_CHECK.md`. Current results are in `results/revised_fixed_dev/summary.json`. The original progress-report PDF below records the earlier prototype; it has not been rewritten around the revised geometry.

Alternatively open SUMO-GUI, select File > Open Simulation, and choose `Eglinton_Danforth.sumocfg`. The revised drawing is stored in `models/eglinton_danforth/intersection.net.xml`. The original `Eglinton_Danforth_Prototype.sumocfg` and `results/baseline_dev/idealized.net.xml` remain unchanged for the earlier experiments.

## Downloaded TorontoSUMONetworks source

The complete requested repository is cloned at `external/TorontoSUMONetworks`, including its Python scripts, configuration files, data assets, documentation, MIT license, and Git history. Source: https://github.com/Jahandad-Baloch/TorontoSUMONetworks . The downloaded revision and file count are recorded in `evidence/toronto_source.json`. Its requirements.txt dependencies are installed in this project's `.venv`. This external clone is ignored by the parent repository and remains a separate Git checkout.

The upstream pipeline still needs adaptation: main.py has a missing comma between its final task entries, and route/network_manager.py imports `scripts.*` modules absent from this checkout. Dashboard and analysis imports also include packages not listed in upstream requirements.txt. The directly openable prototype SUMO file does not depend on this upstream entry point. Downloading the source has not made its Toronto network-building pipeline fully operational.

## Run the setup check

From PowerShell in this folder:

```powershell
.\.venv\Scripts\python.exe check_setup.py
```

The check uses a temporary synthetic network and tests Python imports and TraCI communication. It does not validate Toronto geometry, demand, timing plans, pedestrian safety, or controller performance.

Open the installed SUMO interface:

```powershell
.\.venv\Scripts\sumo-gui.exe
```

Recreate the environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

For Python scripts, set `os.environ['SUMO_HOME'] = sumo.SUMO_HOME` after importing `sumo` and before importing `sumo_rl`. The check demonstrates this without changing system settings.

## Progress report and completed prototype

The current two-page report is `output/report/Progress_Report_Jowel_Akkeh.pdf`. Its editable IEEEtran source is `output/report/main.tex`; the local LaTeX compiler was unavailable, so this source has not been compiled. The PDF is generated with ReportLab in a two-column IEEE-style layout and was rendered and visually checked.

The local Toronto turning-movement data was found at `C:\Users\joelle11\Downloads\tmc_raw_data_2020_2029.csv`. Selected counts match the proposal. The frozen manifest reserves June 19, 15:00-17:00 for train and 17:00-18:00 for dev, and retains both proposed tests. This is a documented revision to introduce dev before any controller experiment. No test performance has been measured.

Run the implemented dev prototype:

```powershell
.\.venv\Scripts\python.exe run_baseline.py
```

Five fixed seeds each generated and completed 3,594 vehicles. Mean time loss was 180.37 +/- 11.19 s/vehicle; including departure delay gave 292.22 +/- 16.63 s/vehicle (mean +/- sample standard deviation across five seed means). These results use idealized geometry and no pedestrians. They are not calibrated Toronto intersection performance or DRL results. See `results/baseline_dev/summary.json` and per-seed logs for evidence.

Data preparation is reproducible with `prepare_data.py`, but it deliberately refuses to overwrite an existing frozen split. Keep this manifest intact. The original 88 MB input is outside the repository; its full SHA-256 hash is recorded in the manifest. Car, truck, and bus demand is included; pedestrian fields load and are audited, but pedestrian movement and delay are not simulated. Bicycle fields are excluded from the current vehicle-only model.

The signal timing source was recovered from the public report linked in the proposal: https://320mccowan.ca/wp-content/uploads/2020/04/TransportationReport_320McCowan.pdf (PDF p. 147). Only a simplified vehicle-phase interpretation is implemented; field geometry, the full signal interpretation, and pedestrian clearance remain to be verified.

Five successful W&B offline records have been created using `log_wandb.py`. `results/wandb_runs.json` identifies exactly these successful records; an earlier failed staging run must not be used as evidence. They contain a post-hoc import of the actual SUMO output metrics, not learning curves. They are not hosted web links. After logging into your W&B account, sync the five directories named in the index to the intended entity/project. Do not commit API keys. The project is a local Git repository with no remote URL configured. Both hosted repository and W&B evidence links remain required before submission.

`requirements-lock.txt` contains the full resolved simulation/learning environment. The report-generation script uses the separate bundled document runtime's ReportLab. Setup checks and hardware details are retained in `evidence/`.

## Original research specification from the proposal

- Site: Eglinton Avenue East and Danforth Road, TCS 379.
- Train: June 19, 2024, 15:00-18:00; proposal totals 10,310 vehicles and 1,328 pedestrians.
- Primary frozen-policy test: November 2, 2024, 15:00-18:00; 9,961 vehicles and 1,598 pedestrians.
- Secondary frozen-policy test: June 19, 2024, 07:00-10:00; 8,275 vehicles and 661 pedestrians.
- Compare DQN and PPO against the documented fully fixed-time baseline using matched demand realizations and random seeds.
- Use the PM, OFF, and AM baseline plans respectively. The proposal identifies OFF as 95 seconds and AM/PM as 120 seconds; individual intervals still need verification against the timing card.
- Report simulated vehicle and pedestrian mean delay separately. Document definitions, warm-up, unfinished trips, and departures after the evaluation window.

These totals are transcribed from the proposal and have not yet been independently verified.

## Remaining full-study work

1. Verify the full phase-to-movement interpretation of the TCS 379 timing card against field geometry; source demand has been extracted and validated.
2. Obtain TorontoSUMONetworks geometry, extract the site, and verify lanes, connections, crossings, and phase mappings.
3. Build demand files and reconcile each movement and pedestrian count with the source records.
4. Reproduce and verify the published fixed-time plans, including pedestrian clearance, yellow, and all-red intervals.
5. Implement constrained DQN/PPO control with the same operational requirements. Review SUMO-RL signal transitions before using it at this site.
6. Train on the designated period, freeze policies, and run matched-seed independent evaluations.
7. Produce reproducible metrics, uncertainty estimates, figures, and a report with model limitations.

A vehicle-only prototype baseline is implemented and evaluated on dev. No calibrated Toronto model, trained policy, pedestrian delay, or test performance has been produced.

## Pedestrian free-flow speed follow-up

Pedestrian volumes are observed in the same 15-minute Toronto counts as vehicles; only exact arrival times and directions are modeled. `experiments/pedestrian_freeflow_v1/` records 35 matched dev evaluations at SUMO's 1.39 m/s desired free-flow walking speed. The original frozen pilot and policies remain at 1.2 m/s; this follow-up is an evaluation sensitivity check, not retraining. Mean vehicle/pedestrian delay: fixed and DQN 156.13/46.79 s; PPO 202.72/46.50 s. All cases completed all demand without collisions or teleports. `pedestrian_freeflow_check.py` reproduces the check. The current openable fixed-time simulation and `revised_demand.py` use 1.39 m/s; signal clearance timings are unchanged.

## Literature review and method justification

The targeted review dated November 13, 2026 compares ten research papers and audits the existing design and hyperparameters against primary literature, software defaults and site sources. It distinguishes published precedent from practical pilot choices and does not change the frozen experiment.

- [Readable review and full method audit](output/literature/Literature_Review_and_Method_Justification.pdf)
- [Editable review](output/literature/Literature_Review_and_Method_Justification.md)
- [Source links, verification locations and access limits](output/literature/sources_and_verification.json)

The review includes paper-ready cited wording. Its main gaps for future development are training-budget adequacy, algorithm-specific tuning, the exact action grid, reward/normalization sensitivity, additional adaptive baselines, and independent observed traffic periods.
