"""Cited review and explicit audit of the frozen check-in experiment."""
import hashlib
import html
import json
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle, CondPageBreak

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output/literature'
OUT.mkdir(parents=True, exist_ok=True)
PILOT = ROOT / 'experiments/freeflow_pilot_v1'
CONFIG = json.loads((PILOT / 'experiment.json').read_text())
SUMMARY = json.loads((PILOT / 'dev_summary.json').read_text())

# Locators distinguish verified table values from assumptions and our own analysis.
SOURCES = [
    ('P1', 'G. Han et al. (2022)', 'Deep Reinforcement Learning for Intersection Signal Control Considering Pedestrian Behavior', 'Electronics 11(21), 3519. DOI: 10.3390/electronics11213519.', 'https://www.mdpi.com/2079-9292/11/21/3519', 'Sections 3.2.2-3.2.3; Tables 2 and 4. Publisher-indexed methods and tables inspected; direct page intermittently rate-limited.'),
    ('P2', 'L. Wang, Z. Ma, C. Dong and H. Wang (2023)', 'Human-centric multimodal deep (HMD) traffic signal control', 'IET Intelligent Transport Systems 17, 744-753. DOI: 10.1049/itr2.12300. Online first: October 2022.', 'https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/itr2.12300', 'Sections 4.1, 4.3 and 5.1; Table 1. Full publisher methods inspected.'),
    ('P3', 'Y. Fu, Z. Cheng, B. Fang and X. Di (2026)', 'PedSLight: pedestrian and safety-aware reinforcement learning for mixed pedestrian-vehicle signal control', 'Frontiers in Future Transportation 7, 1953597. Published September 22, 2026. DOI: 10.3389/ffutr.2026.1953597.', 'https://www.frontiersin.org/journals/future-transportation/articles/10.3389/ffutr.2026.1953597/full', 'Sections 4.1, 4.3 and 5.1-5.4; Table 2, PDF printed page 7. Learning rate verified in PDF text because HTML omitted its equation.'),
    ('P4', 'J. Ault and G. Sharon (2021)', 'Reinforcement Learning Benchmarks for Traffic Signal Control', 'NeurIPS Datasets and Benchmarks, RESCO.', 'https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/file/f0935e4cd5920aa6c7c996a5ee53a70f-Paper-round1.pdf', 'Sections 3.4 and 4.1-4.3; Figure 4. Full proceedings PDF inspected.'),
    ('P5', 'A. Cabrejas-Egea, S. Howell, M. Knutins and C. Connaughton (2020)', 'Assessment of Reward Functions for Reinforcement Learning Traffic Signal Control under Real-World Limitations', 'Author manuscript accepted at IEEE SMC 2020; arXiv:2008.11634v2.', 'https://arxiv.org/abs/2008.11634', 'Sections 4.1-4.4 and 6.1-6.2; author full text at https://arxiv.org/html/2008.11634.'),
    ('P6', 'B. Koohy, S. Stein, E. Gerding and G. Manla (2022)', 'Reward Function Design in Multi-Agent Reinforcement Learning for Traffic Signal Control', 'ATT 2022 workshop proceedings, CEUR-WS volume 3173.', 'https://ceur-ws.org/Vol-3173/1.pdf', 'Section 5, printed page 7; Sections 6-7. Full proceedings PDF inspected.'),
    ('P7', 'G. Zheng et al. (2019)', 'Diagnosing Reinforcement Learning for Traffic Signal Control', 'Author preprint arXiv:1905.04716; cited as the inspected preprint, not using its placeholder manuscript DOI.', 'https://arxiv.org/abs/1905.04716', 'Sections 4.3, 5.1 and 5.7; full author text at https://arxiv.org/html/1905.04716.'),
    ('P8', 'K. Othman, X. Wang, A. Shalaby and B. Abdulhai (2025)', 'Multimodal adaptive traffic signal control: A decentralized multiagent reinforcement learning approach', 'Multimodal Transportation 4(1), 100190. DOI: 10.1016/j.multra.2025.100190.', 'https://www.sciencedirect.com/science/article/pii/S2772586325000048', 'Publisher-indexed Sections 3.3-3.4 and Table 1 inspected. Direct full-page retrieval returned 403; only verified indexed details are used.'),
    ('P9', 'P. Henderson et al. (2018)', 'Deep Reinforcement Learning that Matters', 'Proceedings of AAAI 2018.', 'https://ojs.aaai.org/index.php/AAAI/article/download/11694/11553', 'Primary conference paper; methodology and reproducibility discussion.'),
    ('P10', 'R. Agarwal et al. (2021)', 'Deep Reinforcement Learning at the Edge of the Statistical Precipice', 'NeurIPS 34.', 'https://proceedings.neurips.cc/paper_files/paper/2021/file/f514cec81cb148559cf475e7426eed5e-Paper.pdf', 'Primary conference paper; few-run uncertainty and interval-estimation methodology.'),
    ('D1', 'A. Raffin et al. (2021)', 'Stable-Baselines3: Reliable Reinforcement Learning Implementations', 'JMLR 22(268), 1-8.', 'https://jmlr.org/papers/v22/20-1364.html', 'Software paper; shared interface and tested reference implementations.'),
    ('D2', 'Stable-Baselines3', 'PPO documentation', 'Version 2.9.2, checked November 12, 2026.', 'https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html', 'Parameter defaults, MlpPolicy and supported action spaces; checked against the installed saved model.'),
    ('D3', 'Stable-Baselines3', 'DQN documentation', 'Version 2.9.2, checked November 12, 2026.', 'https://stable-baselines3.readthedocs.io/en/master/modules/dqn.html', 'Parameter defaults, vanilla DQN and discrete action support; checked against the installed saved model.'),
    ('D4', 'Eclipse SUMO', 'Persons specification', 'Checked November 12, 2026.', 'https://sumo.dlr.de/docs/Specification/Persons.html', 'Person-type desired maximum speed and walking model.'),
    ('D5', 'Eclipse SUMO', 'TripInfo output', 'Checked November 12, 2026.', 'https://sumo.dlr.de/docs/Simulation/Output/TripInfo.html', 'timeLoss, departDelay, unfinished-trip handling and person walk outputs.'),
    ('D6', 'City of Toronto', 'Traffic volumes - multimodal intersection turning movement counts', 'Toronto Open Data Portal; frozen 2024 rows used in the pilot.', 'https://open.toronto.ca/dataset/traffic-volumes-at-intersections-for-all-modes/', 'Local frozen data, row indices and source dictionary audited; not a research paper.'),
    ('D7', 'City of Toronto', 'Current Signal Timing Information: TCS 379', 'October 31, 2019, reproduced in WSP transportation report, February 2020.', 'https://320mccowan.ca/wp-content/uploads/2020/04/TransportationReport_320McCowan.pdf', 'PDF page 147; local phase and runtime validation records. Site-specific source, not a universal timing standard.'),
    ('D8', 'TorontoSUMONetworks contributors', 'TorontoSUMONetworks', 'GitHub revision 35dee7bf8c9963c2105c17befb673be9a9ce597d.', 'https://github.com/Jahandad-Baloch/TorontoSUMONetworks', 'Downloaded source and README; starting software reference, not a peer-reviewed validation of our implementation.'),
    ('D9', 'K. Wunderlich, M. Vasudevan and P. Wang / FHWA (2019)', 'Traffic Analysis Toolbox Volume III: Guidelines for Applying Traffic Microsimulation Modeling Software', '2019 update, FHWA-HOP-18-036.', 'https://highways.dot.gov/media/88726', 'Chapters 2, 5 and 6; Appendix A printed page 91 uses a warm-up and post-peak completion period. The example duration is not a universal prescription.'),
]
URLS = {s[0]: s[4] for s in SOURCES}

PAPERS = [
    ['Pedestrian DQN: Han et al. [P1]', 'SUMO at standard and actual intersections; a dueling/double DQN variant uses pedestrian/vehicle position information, four phase actions, a one-second decision interval and a three-second yellow transition.', 'Table 2: batch 64, discount 0.99, replay 20,000, 300 episodes and six environments. These give precedent for several of our values, but neither their action scheme nor training effort matches our cycle-level vanilla DQN.'],
    ['Multimodal HMD: Wang et al. [P2]', 'SUMO with cars, buses and pedestrians; compares fixed and flexible phase order and uses passenger-weighted waiting/queues. Webster, cyclic Webster and actuated control are baselines.', 'Table 1 reports random-search-selected batch 64, replay 5,000, rate 0.0005, discount 0.75 and two 256-neuron layers. It supports pedestrian inclusion and tuning, not our exact weights or 64-neuron width.'],
    ['Cycle-level PPO: Fu et al. [P3]', 'SUMO, one junction and a corridor; PPO sets continuous green-allocation ratios while phase sequence and transitions remain constrained. The reward combines waiting and a time-to-collision surrogate.', 'Table 2: rate 0.0003, discount 0.99, GAE 0.95, ten epochs, rollout 1,000, batch 50 and 250,000 decisions. Five evaluation seeds and actuated/fixed-time baselines are used. Our discrete five-choice controller is simpler.'],
    ['Toronto multimodal: Othman et al. [P8]', 'Aimsun Next at five North York intersections around Yonge-Steeles, using Toronto 15-minute turning counts, transit schedules and occupancy-aware person-delay optimization.', 'Table 1 includes 64/64 encoder layers, a 64/32 executor, batch 256, replay two million and target updates every 2,000. It supports local count-based demand preparation, but uses another simulator, multiple signals and transit-passenger weighting.'],
    ['RESCO benchmark: Ault and Sharon [P4]', 'SUMO benchmark comparing DQN-based and policy-gradient controllers across realistic and synthetic networks, with fixed-time, max-pressure and greedy baselines.', 'Uses five seeds and reports learning instability and scenario-dependent rankings. Some policy-gradient examples required about 1,400 episodes versus about 100 for DQN variants; these are context-specific results, not a required training threshold for our model.'],
    ['Constrained rewards: Cabrejas-Egea et al. [P5]', 'A real Manchester junction in SUMO, calibrated from sensor data, with realistic stage sequence, minimum greens and intergreens; compares several reward definitions without pedestrians.', 'DQN uses 500/1,000 hidden units, rate 0.00001 and discount 0.8. Ten training runs and evaluations across three demand levels illustrate broader validation; exact values differ substantially from ours.'],
    ['Reward/boundary bias: Koohy et al. [P6]', 'SUMO/RESCO with demand-calibrated Ingolstadt traffic; compares twelve rewards using DQN and a MOVA-based reference, with twenty repetitions per reward.', 'Shows that reward rankings depend on the network and warns that excluding unfinished trips can make poor controllers look better. This supports our completion audit, but does not validate our precise reward coefficients.'],
    ['Compact state/reward: Zheng et al. [P7]', 'LIT re-examines traffic-control states and rewards through transportation theory and tests concise designs in SUMO.', 'Supports considering compact traffic features instead of assuming images are necessary. Its queue/travel-time arguments have stated assumptions; they do not prove that our clipped 25-feature pedestrian/vehicle observation or hybrid reward is sufficient.'],
    ['Reproducibility: Henderson et al. [P9]', 'Examines how random seeds, implementation and hyperparameters affect deep-RL comparisons.', 'Supports independent training repetitions and complete reporting. It does not prescribe our particular seed integers or establish that three repetitions are enough for a precise conclusion.'],
    ['Uncertainty: Agarwal et al. [P10]', 'Studies uncertainty when deep-RL comparisons use few training runs, advocating interval estimates rather than point estimates alone.', 'Supports reporting the uncertainty around our pilot results. Our crossed resampling of three policy seeds and five traffic patterns is a small, scenario-specific analysis, not a replication of their multi-task evaluation procedure.'],
]

PARAMETERS = [
    ['Our DQN', '2 x 64 ReLU layers; rate 0.0003; discount 0.99; batch 64; replay 20,000.', '2,048 cycle decisions; learning starts at 180; target refresh 256; initial/final exploration 1.0/0.05 over 60% of training.'],
    ['Our PPO', 'Separate 2 x 64 tanh policy/value networks; rate 0.0003; discount 0.99; batch 64.', '2,048 cycle decisions; rollout 256; ten epochs; GAE 0.95; entropy coefficient 0.01; clipping 0.2.'],
    ['Han et al. [P1]', 'CNN-based variant; batch 64; discount 0.99; replay 20,000.', '300 episodes, six environments. A learning-rate value was not established from the inspected parameter table.'],
    ['Wang et al. [P2]', 'Two 256-unit layers; rate 0.0005; discount 0.75; batch 64; replay 5,000.', 'Random-search tuning. Decision periods and network architecture differ, so matching one numerical value is not a replication.'],
    ['Fu et al. [P3]', 'MLP; rate 0.0003; discount 0.99; batch 50; rollout 1,000.', '250,000 cycle decisions; ten epochs; GAE 0.95; clipping 0.2. About 122 times our decision budget, with a different task and action space.'],
    ['Cabrejas-Egea et al. [P5]', '500/1,000-unit hidden layers; rate 0.00001; discount 0.8.', 'Different states, control intervals and demand scenarios. These values show that traffic RL has no single standard parameter set.'],
]

DESIGN_AUDIT = [
    ['Simulator and code', 'SUMO 1.28; Python/libsumo; SB3 2.9.2.', 'Established software and literature precedent [D1, P1, P3]. TorontoSUMONetworks is a starting reference [D8]; the current environment, demand conversion and evaluation code are study-specific. No claim of running its full upstream pipeline is justified.'],
    ['Algorithm choice', 'Vanilla DQN and PPO on five discrete actions.', 'Defensible contrasting value-based and policy-gradient baselines [D2, D3, P4]. Pedestrian studies support both families [P1, P3]; they do not imply PPO should outperform DQN here.'],
    ['Observed demand', '15-minute counts; cars, trucks, buses and crossing-leg pedestrian totals.', 'Direct site data support [D6]; Toronto count-based preparation also has precedent [P8]. Counts constrain volumes, not exact arrival times, walking directions, speeds or experienced delay.'],
    ['Arrival assumptions', 'Uniform times within bins; approximately 50/50 walking directions.', 'Explicit reconstruction presets because those details are absent from our count file. No reviewed paper establishes these exact assumptions for this site; keep totals fixed and later test their influence on dev.'],
    ['Walking speed', '1.39 m/s; factor 1; deviation 0 throughout training/evaluation.', 'A documented SUMO default supports the reference speed [D4]. Zero variation is a simplifying preset; local speed variability and slower walkers remain a future sensitivity check. It is separate from signal-clearance design.'],
    ['Signal structure', '120-s cycle; fixed order and transition/clearance stages.', 'Grounded in the published site timing card [D7], with broader constrained-control precedent [P3, P5]. The card is historical; literature does not establish current on-street calibration or regulatory approval.'],
    ['Action values', 'EW WALK 7, 19, 25, 31, 32 s; NS = 39 minus EW.', 'Study-specific grid: includes the documented 31/8 split and keeps both WALK periods at least 7 s. Fixed clearances leave 39 s to allocate. No reviewed paper validates these five exact values or the 7-s lower bound as a local standard.'],
    ['Timing constants', 'Advance 7/3/1 s; clearances 22/34 s; main yellow/red 4/3 s.', 'Site-source and implementation checks [D7], rather than universal hyperparameters. Protect these during learning; passing SUMO conflict checks does not alone establish field safety.'],
    ['Observation', '25 values: four legs x five features, plus previous-action encoding.', 'Compact traffic states and pedestrian inclusion have precedent [P1, P7]. Our exact aggregation is a design choice, not proven fully observable or sufficient; turning movements and bus occupancy are not separately encoded.'],
    ['Normalization', 'Road capacity based on lane length/7.5 m; pending/500; peds/50; wait/600; clip to [0,1].', 'Manual scales keep network inputs bounded without fitting on dev. Exact divisors and clipping are unvalidated presets; log saturation rates and examine them on dev before claiming this representation is adequate.'],
    ['Reward and weights', 'Stopped vehicles + pending vehicles + stopped pedestrians, each weight 1.', 'Waiting/queue objectives have precedent [P1, P6]. This counts each vehicle and pedestrian once; unlike occupancy-weighted HMD [P2], a bus is not weighted by its passengers. Do not describe this as equal weight per person or demonstrated social equity.'],
    ['Reward sampling/scale', 'Five-second samples; per-cycle sum divided by 1,200; terminal penalty equals unfinished count.', 'Numerical and computational presets, not literature-optimized coefficients. Report the formula and test alternatives on dev; scaling can interact with optimizer and entropy settings. Completion checking has stronger methodological support than this exact penalty weight [P6].'],
    ['Static baseline', 'Published timing plan; detector requests disabled.', 'Appropriate first end-to-end baseline [D7]. Stronger comparisons later should include a feasible actuated or pressure-based controller [P4]; fixed-time alone does not establish superiority over conventional adaptive control.'],
    ['Vehicle behavior', 'Cars 5 m; trucks 10 m; buses 12 m; sigma 0.5; remaining dynamics use simulator defaults.', 'Implementation presets tied to counted classes, not locally fitted behavior. Counts alone do not verify travel-time, car-following or lane-changing realism; local field comparisons are the calibration route [D9].'],
]

TRAINING_AUDIT = [
    ['Architecture', 'Two hidden layers of 64 per network/head.', 'Small CPU-friendly preset. SB3 defaults provide software precedent; a 64/64 encoder also appears in Toronto work [P8]. DQN uses a Q/target pair, while PPO uses policy/value networks, so identical widths do not mean identical models.'],
    ['Learning rate', '0.0003 for DQN and PPO.', 'PPO default and used in PedSLight [D2, P3]. It is above SB3 DQN\'s 0.0001 default [D3]. A shared rate is a reproducible preset, not evidence of fair or optimal tuning for both algorithms.'],
    ['Discount', '0.99 for both.', 'Precedent in pedestrian-aware DQN and PPO [P1, P3]. Other studies use 0.75 or 0.8 [P2, P5]. Because our decisions span 120 s, matching a discount used with one-second actions does not match its time horizon.'],
    ['Batch size', '64.', 'Direct precedent in two pedestrian-aware studies [P1, P2]; a manageable CPU minibatch. Other credible work uses 50 or 256 [P3, P8], so 64 remains a sensible starting value, not an established optimum.'],
    ['Total learning', '2,048 decisions per model; three training seeds per algorithm.', 'Bounded check-in budget, not a convergence justification. Close studies train much longer [P3, P4]. Equal numbers of decisions control sample budget but not algorithm-specific learning effort or sample efficiency.'],
    ['DQN replay', 'Capacity 20,000.', 'Exact precedent in Han et al. [P1]. Our entire 2,048-transition pilot fits below this capacity, so memory size is not evidence of a fully exercised long-run replay regime.'],
    ['DQN start/update', 'Start 180; one gradient update per new decision.', 'Collect initial examples before updating, then learn frequently [D3]. The exact threshold and update ratio are presets; no inspected traffic paper justifies 180 specifically.'],
    ['DQN target copy', 'Every 256 decisions.', 'Target-network stabilization follows DQN [D3], but the period is not its library default and has no exact support in the inspected close studies. Check on dev if longer training is undertaken.'],
    ['DQN exploration', 'Initial epsilon 1.0; decay fraction 0.6; final epsilon 0.05.', 'Initial/final probabilities have SB3 default precedent [D3]; stretching decay over 60% is a pilot adaptation. It leaves 5% random actions during late training; deterministic evaluation removes that exploratory randomness.'],
    ['PPO collection', '256 decisions per rollout.', 'Eight rollout-and-update blocks fit into 2,048 decisions. This is a short-budget preset, below the library default 2,048 and PedSLight\'s 1,000 [D2, P3]; no convergence claim follows from eight updates.'],
    ['PPO epochs/GAE', 'Ten epochs; GAE 0.95.', 'Both match SB3 defaults and a close pedestrian PPO study [D2, P3]. They control data reuse and reward-estimate smoothing; local optimality would still require dev comparisons.'],
    ['PPO entropy', '0.01.', 'An explicit exploration preset above SB3\'s zero default [D2]. It encourages diverse actions; the reviewed sources do not validate 0.01 for our normalized reward and small budget.'],
    ['Inherited defaults', 'PPO clip 0.2, value weight 0.5, gradient cap 0.5; DQN gradient cap 10; Adam; algorithm-specific activations.', 'Verified from saved models and the installed SB3 implementation [D2, D3]. Keep the exact software version; inherited defaults are reproducibility choices, not individually tuned traffic parameters.'],
    ['Training randomness', '101, 202, 303; last model from each completed run.', 'Distinct identifiers fixed in advance, with no special scientific status. Repeated training and reporting all runs are supported [P9]; any later checkpoint selection must use dev rather than test.'],
]

EVALUATION_AUDIT = [
    ['Frozen time split', 'Train June 19 15-17; dev 17-18; two reserved test periods.', 'Saved rows support reproducibility. Adjacent hours from one day provide limited distributional coverage; papers do not validate this exact split. A future one-test/more-dev revision should be declared before using the newly assigned periods.'],
    ['Five demand seeds', '11, 22, 33, 44, 55 for every controller.', 'Common arrival realizations permit paired comparisons. Five-seed traffic evaluation has precedent [P3, P4], but repeated randomness within one observed hour is not five independent days.'],
    ['Run structure', 'Two-hour training, one-hour dev; empty start; no warm-up; up to one-hour drain.', 'Time windows follow the saved count periods; drain avoids censoring. No warm-up is a limitation for field interpretation. FHWA\'s example uses lead-in and post-peak simulation [D9], not a universal fixed warm-up length.'],
    ['Delay metric', 'Vehicle timeLoss + departDelay; pedestrian walk timeLoss reported separately.', 'Grounded in SUMO output semantics [D5]. Entry waiting prevents boundary queues disappearing from the score. These are not the same quantities as every paper\'s average stopped wait, travel time or person-weighted delay.'],
    ['Completion guard', 'All generated demand must finish; collisions/teleports invalidate ranking.', 'Strong protection against censoring bias [P6]. Current 35 cases meet it. Record emergency braking too, but collision-free simulation is not proof of pedestrian safety or low near-conflict risk [P3].'],
    ['Uncertainty', 'Mean/sample SD; three policy seeds x five traffic patterns; 4,000 paired crossed resamples.', 'Reporting intervals has methodological support [P10]. The resampling count and crossed design are our analysis choices; only three independently trained policies make inference exploratory and do not establish statistical power.'],
    ['What results establish', 'Fixed/DQN 156.13 s/vehicle; PPO 178.95; all are dev results.', 'DQN reproduced the baseline on these cases; PPO\'s interval includes benefit and harm. This is a bounded-pilot finding, not evidence that PPO is generally inferior, that training converged, or that the controller transfers to new days.'],
]

NARRATIVE = [
    ('What the literature supports', 'The project fits an established line of pedestrian-aware signal-control research: pedestrian states and rewards are used in DQN-based SUMO studies [P1, P2], while cycle-level PPO provides a close precedent for adjusting allocations without discarding the signal sequence [P3]. Toronto-based work also supports using municipal turning counts for demand preparation [P8]. The studies differ in simulator, passenger weighting and action design, so they support the research direction without validating this exact Toronto controller.'),
    ('Why outcomes differ between papers', 'State, action and reward choices change the problem being learned. RESCO demonstrates scenario-dependent rankings and instability [P4], reward comparisons find differing conclusions across networks [P5, P6], and LIT argues for testing concise representations rather than adding detail automatically [P7]. Our pilot therefore cannot borrow a published percentage improvement or assume that sharing a learning rate reproduces another study.'),
    ('What we can claim now', 'Several current values have direct published precedent, while others are library defaults, site-plan constants or practical pilot presets. The literature was checked after the experiment: matching values is supporting precedent, not a claim that the experiment was originally copied from those papers. The current evidence supports feasibility and a documented initial comparison; it does not establish optimal hyperparameters or a generally superior controller.'),
]

NEXT_STEPS = [
    ['Keep for this check-in', 'Retain the frozen experiment and report it as an initial pilot, cite the relevant sources, and preserve the observed counts and signal constraints. No additional experiment is needed merely to add these citations.'],
    ['Correct the justification', 'Describe the reward as equal vehicle/pedestrian unit weighting, not equal passenger weighting; describe 2,048 decisions as a resource-bounded budget; and state that shared presets do not replace algorithm-specific tuning.'],
    ['Next development priority', 'First diagnose training curves, timing choices and observation clipping on dev; then predefine a small, equal-budget search over training length, learning rate and reward alternatives. Longer training is a candidate intervention, not a proven cure for PPO variability.'],
    ['Strengthen the final study', 'Add an appropriate adaptive baseline and independent development periods, examine initial-queue/warm-up assumptions, and validate speed/behavior against available field data. Freeze the revised protocol before final test evaluation.'],
]

PAPER_TEXT = [
    'Pedestrian-aware traffic-signal control has been investigated using DQN-based SUMO models that include pedestrian information in the state and reward [P1, P2]. Cycle-level PPO has also been used to adjust signal allocations while preserving a constrained phase structure [P3]. These studies motivate comparing DQN and PPO with a documented fixed-time plan, while retaining this site\'s pedestrian clearance and transition stages.',
    'The batch size of 64, discount factor of 0.99 and replay capacity of 20,000 have precedent in pedestrian-aware DQN research [P1], while the PPO learning rate of 0.0003, ten update epochs and GAE parameter of 0.95 match a close cycle-level study [P3]. These precedents support initial settings; our smaller networks, short rollouts and 2,048-decision budget remain practical presets rather than optimized choices.',
    'The reward counts waiting vehicles and pedestrians as separate units without passenger-occupancy weighting, unlike person-based multimodal objectives [P2]. All controllers are evaluated on common arrival patterns, and unfinished demand is retained because completed-trip-only statistics can bias rankings [P6]. The repeated training runs and uncertainty intervals follow the broader need for reliable few-run RL reporting [P9, P10].',
]


def main():
    assert CONFIG['pedestrian_desired_speed_m_s'] == 1.39
    assert CONFIG['decision_budget_per_model'] == 2048
    assert len(SUMMARY['runs']) == 35
    title = 'Literature Review and Method Justification'
    subtitle = 'Toronto TCS 379 traffic-signal RL pilot | November 13, 2026'
    markdown = ['# ' + title, '', subtitle, '',
                'Targeted review of ten research papers, plus primary software, data and engineering sources. This is a method audit for the completed check-in, not an exhaustive systematic review.', '',
                'Search focus: SUMO + pedestrians + DQN/PPO; cycle-level signal control; reward/state design; Toronto count-based demand; reproducible RL evaluation. Publication cutoff: November 12, 2026. Search snippets alone were not used to invent missing parameters; access limits are recorded with the sources.', '']
    styles = {
        'title': ParagraphStyle('lit-title', fontName='Helvetica-Bold', fontSize=21, leading=25, spaceAfter=10),
        'sub': ParagraphStyle('lit-sub', fontName='Helvetica', fontSize=10, leading=13, textColor=colors.HexColor('#46546a'), spaceAfter=14),
        'h': ParagraphStyle('lit-h', fontName='Helvetica-Bold', fontSize=12, leading=15, spaceBefore=13, spaceAfter=7),
        'body': ParagraphStyle('lit-body', fontName='Helvetica', fontSize=9.5, leading=12.5, spaceAfter=7),
        'cell': ParagraphStyle('lit-cell', fontName='Helvetica', fontSize=8.1, leading=10.6),
        'ref': ParagraphStyle('lit-ref', fontName='Helvetica', fontSize=8, leading=10, spaceAfter=3),
    }

    def links(text, md=False):
        if md:
            def convert(m):
                return ', '.join(f'[{key}]({URLS[key]})' for key in m[1].split(', '))
            return re.sub(r'\[((?:P\d+|D\d+)(?:, (?:P\d+|D\d+))*)\]', convert, text)
        escaped = html.escape(text)
        return re.sub(r'\[((?:P\d+|D\d+)(?:, (?:P\d+|D\d+))*)\]',
                      lambda m: '[' + ', '.join(f'<link href="{URLS[k]}" color="#1256a0">{k}</link>' for k in m[1].split(', ')) + ']', escaped)

    story = [Paragraph(title, styles['title']), Paragraph(subtitle, styles['sub'])]

    def paragraph(text, style='body'):
        story.append(Paragraph(links(text), styles[style]))
        markdown.extend([links(text, True), ''])

    def heading(text):
        story.append(CondPageBreak(80))
        story.append(Paragraph(html.escape(text), styles['h']))
        markdown.extend(['## ' + text, ''])

    def table(headers, rows, widths):
        values = [[Paragraph('<b>' + html.escape(t) + '</b>', styles['cell']) for t in headers]]
        values += [[Paragraph(links(t), styles['cell']) for t in row] for row in rows]
        t = LongTable(values, colWidths=widths, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9eff6')),
            ('LINEBELOW', (0, 0), (-1, 0), .7, colors.HexColor('#60718a')),
            ('LINEBELOW', (0, 1), (-1, -1), .25, colors.HexColor('#c8d1de')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.extend([t, Spacer(1, 7)])
        markdown.extend(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |'])
        markdown.extend('| ' + ' | '.join(links(cell, True).replace('|', '/') for cell in row) + ' |' for row in rows)
        markdown.append('')

    paragraph('This targeted review compares ten research papers with the completed freeflow_pilot_v1 experiment and distinguishes published precedent, software defaults, site constraints and untested presets. It is not an exhaustive systematic review.')
    paragraph('The search covered pedestrian-aware SUMO DQN/PPO studies, cycle-level signal control, reward/state design, Toronto count-based demand and RL evaluation, with a publication cutoff of November 12, 2026. Verified methods and parameter tables are used; access limitations and exact source locations are recorded at the end.')
    for label, text in NARRATIVE:
        heading(label)
        paragraph(text)
    heading('Closest studies and what they actually used')
    table(['Study', 'Implemented method', 'Verified settings and relevance'], PAPERS, [99, 196, 209])
    heading('Direct parameter comparison')
    paragraph('Values below come from the specified parameter tables or our frozen configuration and saved models. Episode counts, simulator seconds and decision counts are not interchangeable. The listed studies use different action periods, observations, rewards and demand; this table is a design comparison, not a performance leaderboard.')
    table(['Study', 'Architecture and principal values', 'Budget or qualification'], PARAMETERS, [91, 215, 198])
    heading('Audit of data, control and reward choices')
    table(['Choice', 'What our experiment used', 'Defensible justification and remaining limit'], DESIGN_AUDIT, [83, 147, 274])
    heading('Audit of every explicit training setting')
    table(['Setting', 'Current value', 'Evidence and interpretation'], TRAINING_AUDIT, [84, 131, 289])
    heading('Audit of evaluation and reporting')
    table(['Choice', 'Current implementation', 'Evidence and interpretation'], EVALUATION_AUDIT, [84, 141, 279])
    heading('Recommended use in the check-in and next phase')
    table(['Priority', 'Action'], NEXT_STEPS, [123, 381])
    heading('Cited wording that can be adapted into the paper')
    paragraph('The following paragraphs describe the existing experiment without claiming that the later literature review was a completed hyperparameter search.')
    for text in PAPER_TEXT:
        paragraph(text)
    heading('Sources and verification locations')
    paragraph('P1-P10 are research papers; D1-D9 are supporting software, data and engineering sources. For P1 and P8, publisher-indexed methods/tables supplied the cited details when direct access was blocked; unverified full-text details are not inferred. Secondary summaries and social-media posts were excluded from the evidence base.')
    source_records = []
    for key, author, source_title, citation, url, location in SOURCES:
        line = f'[{key}] {author}. {source_title}. {citation} Verification: {location}'
        markdown.extend([f'**[{key}] {author}.** [{source_title}]({url}). {citation} Verification: {location}', ''])
        text = f'<b>[{key}] {html.escape(author)}.</b> <link href="{url}" color="#1256a0">{html.escape(source_title)}</link>. {html.escape(citation)} Verification: {html.escape(location)}'
        story.append(Paragraph(text, styles['ref']))
        source_records.append(dict(id=key, authors=author, title=source_title, citation=citation, url=url, verified_locations=location, accessed='2026-11-12'))

    pdf = OUT / 'Literature_Review_and_Method_Justification.pdf'
    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor('#d5dce5'))
        canvas.line(54, 42, 558, 42)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#46546a'))
        canvas.drawString(54, 29, 'TCS 379 | Literature and method audit | November 13, 2026')
        canvas.drawRightString(558, 29, str(doc.page))
    doc = SimpleDocTemplate(str(pdf), pagesize=(8.5 * inch, 11 * inch), rightMargin=54, leftMargin=54, topMargin=45, bottomMargin=54,
                            title=title, author='Jowel Akkeh')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    (OUT / 'Literature_Review_and_Method_Justification.md').write_text('\n'.join(markdown), encoding='utf-8')
    provenance = {
        'review_date': '2026-11-13', 'scope': 'Targeted method comparison, not exhaustive systematic review',
        'experiment': str(PILOT.relative_to(ROOT)),
        'experiment_sha256': hashlib.sha256((PILOT / 'experiment.json').read_bytes()).hexdigest(),
        'summary_sha256': hashlib.sha256((PILOT / 'dev_summary.json').read_bytes()).hexdigest(),
        'source_records': source_records,
        'screened_not_used_for_parameter_claims': [
            {'title': 'An adaptive traffic signal control scheme with Proximal Policy Optimization based on deep reinforcement learning for a single intersection',
             'url': 'https://www.sciencedirect.com/science/article/pii/S0952197625004403', 'reason': 'Full-text retrieval blocked; no unverified hyperparameter values used.'},
        ],
        'implementation_audit': 'Frozen configuration, rl_freeflow/environment.py and saved DQN/PPO policies inspected. No training settings changed and no additional experiments run for this review.',
    }
    (OUT / 'sources_and_verification.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    print(pdf)


if __name__ == '__main__':
    main()
