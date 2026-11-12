# Signal and observed-demand check

Completed November 9, 2026 for the revised Eglinton–Danforth model. This is a validation of the implemented simulation, not a certification of field operation or calibration to measured delay.

## What was verified

- The static PM cycle has the expected 120-second duration and interval sequence: 7, 3, 1, 31, 22, 4, 3, 8, 34, 4, 3 seconds.
- Every protected-green pair was checked against SUMO's junction conflict matrix. No conflicting pair receives protected green simultaneously. Turning movements outside the advance use yielding green.
- Each leg has one full-width signal-controlled crossing. North/south-leg crossings receive WALK with the east–west movement; east/west-leg crossings receive WALK with the north–south movement.
- The 22 s and 34 s modeled clearance intervals exceed the respective crossing traversal times at the explicit 1.2 m/s pedestrian speed. SUMO uses red to prevent new crossing entries during clearance; pedestrians already crossing continue.
- The recorded seed-11 trace contains 7,200 expected signal states over 60 cycles.
- All 518 seed-11 pedestrians were traced through the intended crossing leg: north 147, south 118, east 96, west 157. No out-of-WALK entry was detected, allowing one time-step alignment between trajectory and signal-state output.

Machine-readable checks: `signal_validation.json` and `signal_runtime_validation.json`. Actual signal and pedestrian traces are in `signal_trace_audit/`.

## Data interpretation

The City's official dictionary confirms that pedestrian columns represent the leg being crossed, rather than the pedestrian's direction of travel. The dictionary and package metadata were downloaded to `traffic_count_dictionary.json` and `traffic_count_metadata.json`.

Source API: https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/datastore_search?resource_id=262469c2-abfe-4756-9068-4ea5c7ba1af7&limit=0

The current SUMO file uses the observed dev period (June 19, 2024, 17:00–18:00): 3,594 vehicles and 518 pedestrians. It preserves each 15-minute crossing-leg count. Arrival times are uniform within each interval; pedestrian directions are approximately balanced, since the source has no direction breakdown. Walking speed is fixed at 1.2 m/s. These are model assumptions, not observations.

## Corrections made during validation

The initial imported network divided the east and west crossings at their refuges. These were changed to full-width crossings so a person who starts during WALK can continue through the modeled clearance interval.

The runtime trace also found 62 south-leg pedestrians using an automatically guessed approach crossing rather than the intended signalized crossing. Guessed crossings outside the main junction were removed from this isolated-intersection model. The full five-seed evaluation was then rerun; the earlier provisional run is not used in the final summary.

The eastern carriageway separation remains intact: no overlap in vehicle pavement and an approximately 2.39 m minimum modeled gap. The width remains an assumption.

## Final dev baseline

| Metric | Mean ± sample SD across five seeds |
|---|---:|
| Vehicle time loss | 55.12 ± 3.72 s/vehicle |
| Vehicle departure delay | 111.09 ± 9.22 s/vehicle |
| Vehicle combined delay proxy | 166.21 ± 10.16 s/vehicle |
| Pedestrian time loss | 46.93 ± 1.43 s/person |
| Pedestrian walk duration | 67.76 ± 1.43 s/person |

Seeds: 11, 22, 33, 44, 55. All 3,594 vehicles and 518 pedestrians completed in each run. No collisions or teleports were reported. Emergency-braking events per seed were 1, 2, 1, 2, and 0, respectively. These events remain part of the recorded evidence and require consideration during further behavior and signal calibration.

Results are in `results/revised_fixed_dev/summary.json`, with per-seed routes, audits, logs, and outputs. Five offline W&B records are indexed at `results/revised_fixed_dev/wandb_runs.json`; they have not been synchronized to hosted URLs.

These numbers must not be interpreted as an improvement over the earlier 180.37 s vehicle-only prototype result: geometry, route lengths, pedestrian demand, and boundary behavior changed. The original report and results remain a historical prototype snapshot.

No test-period controller performance was measured. The frozen split is unchanged. Before a final study, surveyed lane details, 2024 layout, timing-card movement interpretation, transit-lane permissions, transit stops, initial queues, and demand/behavior assumptions still need review.

## Reproduce

1. `python rebuild_intersection.py` rebuilds the revised drawing and the default observed seed-11 demand.
2. `python run_revised_baseline.py` audits the signal program and runs the five-seed dev baseline.
3. `python audit_simulation_trace.py` audits actual signal and pedestrian trace data for seed 11.
4. `python log_wandb.py --revised` imports saved results into W&B offline runs for later account synchronization.

Use `.venv/Scripts/python.exe` from the project root for these commands. Rerunning writes to the corresponding revised-result folders; original prototype results remain separate.
