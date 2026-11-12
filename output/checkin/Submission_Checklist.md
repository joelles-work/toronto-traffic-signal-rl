# Check-in submission checklist

The current paper is `Progress_Report_Jowel_Akkeh.pdf`; editable text and IEEEtran source are alongside it. This is a check-in draft, not a finished final study.

| Requirement | Status | Evidence |
|---|---|---|
| Data load | Complete | Frozen train/dev CSVs, exact count audits, demand generation |
| Method describes what actually ran | Complete | Report Section I; frozen experiment.json and implementation hashes |
| Split before controller experiments; save indices | Complete | data/split_manifest.json; copied and hashed pilot inputs |
| End-to-end baseline with a dev number | Complete | Five fixed-time runs: combined vehicle proxy 166.21 ± 10.16 s/vehicle; pedestrian time loss 46.93 ± 1.43 s/person |
| Repeated seeds and uncertainty | Complete for pilot | Five demand seeds; three independently trained policies per RL algorithm; paired exploratory bootstrap |
| Report failed/inconclusive plan and revision | Complete | DQN reproduces baseline, PPO unstable/worse on average; temporary-file failure and routing correction documented |
| No test-based tuning | Complete | RL code exposes train/dev only; no test controller performance measured |
| Small-data validation limitations | Explicitly disclosed | Only selected observed periods; no time-blocked cross-validation yet; repeated episodes are not independent observed days |
| IEEE-style, individual report | Draft complete; visually checked | Two-page, two-column PDF and editable IEEEtran source; all pages rendered and inspected |
| Hosted repository URL | Complete; instructor access needs confirmation | https://github.com/joelles-work/toronto-traffic-signal-rl (private) |
| Hosted W&B run links | Complete | All six training runs and the dev comparison uploaded and verified; links in the report references and experiments/pilot_v1/wandb_runs.json |

Both hosted links are included in the report. Confirm instructor access before submission. Do not put API keys or passwords into the paper, repository, or chat.

The previous report under `output/report/` documents an earlier prototype and is superseded for this check-in by the current paper under `output/checkin/`.

Pedestrian free-flow follow-up: 35 paired dev evaluations at 1.39 m/s completed; all demand finished without collisions or teleports. Existing policies were trained at 1.2 m/s, so this is a sensitivity evaluation. Evidence: experiments/pedestrian_freeflow_v1 and https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379/runs/0f8391l6 .
