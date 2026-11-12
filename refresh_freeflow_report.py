"""Update the check-in from the completed, consistent 1.39 m/s experiment."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PILOT = ROOT / 'experiments/freeflow_pilot_v1'


def main():
    summary = json.loads((PILOT / 'dev_summary.json').read_text())
    assert len(summary['runs']) == 35
    assert all(c['all_runs_eligible'] for c in summary['controllers'].values())
    fixed = summary['controllers']['fixed']['pooled_case_metrics']
    ppo = summary['controllers']['PPO']
    dqn = summary['controllers']['DQN']
    vkey, pkey = 'vehicle_combined_delay_proxy_s', 'pedestrian_time_loss_s'
    vf, pf = fixed[vkey], fixed[pkey]
    vp, pp = ppo['between_training_seed_metrics'][vkey], ppo['between_training_seed_metrics'][pkey]
    better = sum(m[vkey]['mean'] < vf['mean'] for m in ppo['by_training_seed'].values())
    intervals = ppo['paired_comparison_to_fixed']
    vi = intervals[vkey]['two_way_bootstrap_95_percent_interval_s']
    pi = intervals[pkey]['two_way_bootstrap_95_percent_interval_s']
    dqn_baseline = all(a['action'] == 3 for path in (PILOT / 'dev').glob('dqn_*/*/actions.json') for a in json.loads(path.read_text()))
    dqn_sentence = "DQN selected the baseline's 31/8-second WALK split in every evaluated cycle and therefore produced identical delay." if dqn_baseline else f"DQN averaged {dqn['pooled_case_metrics'][vkey]['mean']:.2f} s/vehicle and {dqn['pooled_case_metrics'][pkey]['mean']:.2f} s/person."
    unclear = vi[0] <= 0 <= vi[1] and pi[0] <= 0 <= pi[1]
    finding = 'These results do not establish a consistent improvement over fixed-time control.' if unclear else 'The direction and uncertainty of the paired differences are reported below.'
    sections = [
        ['METHOD', [
            ['Data and split.', "The study models Eglinton Avenue East and Danforth Road (TCS 379) using vehicle turning movements and pedestrian crossing totals recorded every 15 minutes in the Toronto Open Data Portal [1]. Training uses June 19, 2024, 15:00-17:00, while development (dev) uses 17:00-18:00 to compare controllers and guide later changes. The rows in Table I were saved before experiments; neither reserved test period has been used to measure performance."],
            ['Study periods.', "Each simulation starts empty, with no shared trips between periods; repeated arrival patterns represent the same observed days."],
            ['Existing software.', "TorontoSUMONetworks was selected as a starting reference because it organizes Toronto municipal data and SUMO network preparation [10]. Its downloaded entry point had code and import errors, so this study uses separate scripts to build the intersection, convert counts into trips, and apply the signal plan. DQN and PPO use Stable-Baselines3 [11] for its consistent training interface, paired here with a study-specific controller supplying traffic and pedestrian observations, five timing choices, and a waiting-based reward, plus scripts for saving splits and matching evaluations."],
            ['Building the simulation.', "The OpenStreetMap road layout [2] was checked against Google Maps and includes turning lanes, sidewalks, and four crossings. Vehicle and pedestrian demand both use observed counts from the Toronto Open Data Portal [1], with arrivals spread within each 15-minute interval and pedestrian directions balanced across each crossing. Training and evaluation use SUMO's desired free-flow pedestrian speed of 1.39 m/s [9]."],
            ['The fixed-time controller.', "The fixed-time baseline follows a 120-second cycle based on the City's PM timing card [3]: east-west green includes 31 seconds of WALK and 22 seconds of crossing clearance, while north-south green includes 8 seconds of WALK and 34 seconds of clearance. The 7-second east-west left-turn advance, yellow, and all-red stages are retained. Vehicle-detector requests, which can extend or request a signal phase when traffic is detected, are disabled so the baseline repeats the same documented timing plan."],
            ['What the learning controllers change.', "At the beginning of each 120-second cycle, DQN or PPO reads vehicle queues, vehicles waiting to enter, and pedestrian waiting, then sets the east-west WALK duration to 7, 19, 25, 31, or 32 seconds. North-south receives the remainder of 39 seconds, so 31 seconds east-west leaves 8 seconds north-south and reproduces the baseline. The cycle length, stage order, yellow, all-red, and crossing clearance times stay fixed."],
            ['Training setup.', "The Stable-Baselines3 controllers [11] exchange traffic conditions and timing choices with SUMO through Python [5], using a reward that penalizes waiting vehicles and pedestrians equally every five seconds, includes vehicles waiting outside the network, and adds a penalty for unfinished trips. Each training episode covers the two-hour demand period and allows up to one extra hour for traffic to clear."],
            ['Model settings.', "Each algorithm was trained for 2,048 timing decisions with seeds 101, 202, and 303, chosen in advance as three distinct, repeatable random initializations. Table II explains the settings, which were fixed for a small CPU-based pilot rather than selected through a parameter search. A common learning rate, network size, and batch size support a controlled comparison; the remaining presets limit memory and update costs [4]. Runs used Windows, Python 3.14.6, and an Intel CPU with 20 logical processors, without a GPU."],
            ['How delay is measured.', "Vehicle delay combines SUMO's time lost below ideal speed and waiting to enter the network [6], so queues outside the short modeled approaches are included. Pedestrian delay is SUMO's walking time loss; both are simulated measures. Completion, collisions, teleports, and emergency braking are recorded alongside delay."],
        ]],
        ['FIRST EXPERIMENTS', [
            ['Baseline and checks.', f"The evaluation script used traffic seeds 11, 22, 33, 44, and 55, selected in advance to create five repeatable arrival patterns with the same observed counts for every controller. Results below use mean +/- sample standard deviation across these five patterns. All 3,594 vehicles and 518 pedestrians completed each fixed-time run, giving {vf['mean']:.2f} +/- {vf['sample_std']:.2f} s/vehicle and {pf['mean']:.2f} +/- {pf['sample_std']:.2f} s/person. Vehicle delay comprised {fixed['vehicle_time_loss_s']['mean']:.2f} seconds inside the network and {fixed['vehicle_depart_delay_s']['mean']:.2f} seconds waiting to enter."],
            ['Checking the signals.', "Before training, the Python learning interface reproduced the fixed-time result exactly, and each of the five allowed timing choices was checked for a complete cycle. Earlier signal traces confirmed the planned sequence over 60 cycles and the intended crossing for all 518 pedestrians, while SUMO's conflict checks found no opposing movements receiving protected green together."],
            ['Pilot comparison.', "Each of the six final trained models was evaluated on the baseline's five traffic patterns, producing 15 DQN and 15 PPO evaluations in addition to five fixed-time runs. The last saved model from each training run was used, and Table III reports the controller means. " + dqn_sentence],
            ['Differences between training runs.', f"PPO averaged {vp['mean']:.2f} s/vehicle and {pp['mean']:.2f} s/person, with a vehicle-delay standard deviation of {vp['sample_std_of_five_demand_seed_means']:.2f} seconds across its three training-run means; {better} of the three training runs had lower mean vehicle delay than fixed-time. The limited 2,048-decision training budget and the difference between the waiting-based reward and reported travel-delay measure are possible explanations for the observed performance, but their effects have not been tested separately."],
            ['How certain are these differences?', f"The matched comparison was repeated 4,000 times by drawing training runs and traffic patterns from the existing results, allowing repeats. The estimated 95% range for PPO minus fixed-time was {vi[0]:+.2f} to {vi[1]:+.2f} s/vehicle and {pi[0]:+.2f} to {pi[1]:+.2f} s/person. {finding} Across all 35 dev evaluations, completion and safety-event counts are retained in the evidence [7]."],
        ]],
        ['EVIDENCE, PROBLEMS, AND NEXT STEPS', [
            ['Saved evidence.', "The GitHub repository contains the code, frozen splits, models, and results [8], while W&B records the six training runs and their matched dev comparison [7]. The report uses the consistent 1.39 m/s experiment under experiments/freeflow_pilot_v1; earlier experiments remain archived in the repository."],
            ['Problems found and corrected.', "An initial routing error allowed 62 south-side pedestrians to use an unintended nearby crossing; the network was corrected and routes checked again without changing Toronto's counts. During the current experiment, a local W&B logging connection interrupted seed 202 before a final model was saved; that attempt was excluded and the seed restarted from scratch with the same settings."],
            ['Revised plan.', "Further development will examine PPO's timing choices, entry queues, and the reward definition on dev. One final test period and additional development periods would support broader model checks after a documented split revision; the results here retain the original split. Validation against additional observed periods and field conditions remains future work, and the test periods stay unused until the final model is selected."],
        ]],
    ]
    method = sections[0][1]
    settings = next(item for item in method if item[0] == 'Model settings.')
    method.remove(settings)
    method.insert(3, settings)
    abstract = "This study compares Deep Q-Network (DQN), Proximal Policy Optimization (PPO), and fixed-time signal control at Eglinton Avenue East and Danforth Road using SUMO and observed Toronto vehicle and pedestrian counts. Training and evaluation use 1.39 m/s pedestrian free-flow speed, with six trained models evaluated on five shared development traffic patterns. " + finding + " The check-in documents the method, results, implementation problems, and next steps, with GitHub and W&B evidence."
    (ROOT / 'output/checkin/report_text.json').write_text(json.dumps({'abstract': abstract, 'sections': sections}, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
