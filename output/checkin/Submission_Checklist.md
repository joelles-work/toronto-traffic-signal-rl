# Check-in submission checklist

The current paper is `Progress_Report_Jowel_Akkeh.pdf`; editable text and IEEEtran source are alongside it. This is a check-in draft, not a finished final study.

| Requirement | Status | Evidence |
|---|---|---|
| Data load | Complete | Frozen train/dev CSVs, exact count audits, demand generation |
| Method describes what actually ran | Complete | Report Section I; experiments/freeflow_pilot_v1/experiment.json and implementation hashes |
| Split before controller experiments; save indices | Complete | data/split_manifest.json; copied and hashed pilot inputs |
| End-to-end baseline with a dev number | Complete | Five fixed-time runs: combined vehicle proxy 156.13 ± 6.58 s/vehicle; pedestrian time loss 46.79 ± 1.41 s/person |
| Repeated seeds and uncertainty | Complete for pilot | Five demand seeds; three independently trained policies per RL algorithm; paired exploratory bootstrap |
| Report failed/inconclusive plan and revision | Complete | DQN reproduces baseline, PPO unstable/worse on average; temporary-file failure and routing correction documented |
| No test-based tuning | Complete | RL code exposes train/dev only; no test controller performance measured |
| Small-data validation limitations | Explicitly disclosed | Only selected observed periods; no time-blocked cross-validation yet; repeated episodes are not independent observed days |
| IEEE-style, individual report | Draft complete; visually checked | Two-page, two-column PDF and editable IEEEtran source; all pages rendered and inspected |
| Hosted repository URL | Complete; instructor access needs confirmation | https://github.com/joelles-work/toronto-traffic-signal-rl (private) |
| Hosted W&B run links | Complete | All six training runs and the dev comparison uploaded and verified; links in the report references and experiments/freeflow_pilot_v1/wandb_runs.json |

Both hosted links are included in the report. Confirm instructor access before submission. Do not put API keys or passwords into the paper, repository, or chat.

The previous report under `output/report/` documents an earlier prototype and is superseded for this check-in by the current paper under `output/checkin/`.

Current report: training and evaluation both use 1.39 m/s pedestrian desired free-flow speed in experiments/freeflow_pilot_v1. Six new trained models and 35 matched dev cases are complete; all seven records are verified online. Earlier speed experiments are archived. The first seed-202 logging failure was excluded and restarted with unchanged settings.

November 13 validation/source update: the paper includes citations for repeated training seeds and five-run traffic evaluation, City usual-conditions WALK guidance, and the complete assumption/source register. A separate 25-case dev study is uploaded and reported, including incomplete demand and clipping. Proposed normalization changes are not relabeled as current trained-model settings.
