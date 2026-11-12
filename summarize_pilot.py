"""Create check-in tables and scientific plots from the completed frozen pilot."""
import json
from pathlib import Path
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from rl_freeflow.freeze import ROOT,PILOT,verify


def main():
    verify()
    summary=json.loads((PILOT/'dev_summary.json').read_text())
    out=ROOT/'output/checkin'
    out.mkdir(parents=True,exist_ok=True)
    fig,axes=plt.subplots(2,1,figsize=(7,5),sharex=True,constrained_layout=True)
    for ax,algorithm in zip(axes,['DQN','PPO']):
        for seed in [101,202,303]:
            path=PILOT/'training'/f'{algorithm.lower()}_{seed}'/'episodes.jsonl'
            data=[json.loads(line) for line in path.read_text().splitlines() if line]
            ax.plot([r['decision'] for r in data],[r['reward'] for r in data],label=f'Seed {seed}',linewidth=1.2)
        ax.set_ylabel('Episode reward')
        ax.set_title(f'{algorithm}: training period only',fontsize=10,loc='left')
        ax.grid(alpha=.2)
        ax.legend(fontsize=8,ncol=3)
    axes[-1].set_xlabel('Cycle decisions')
    fig.savefig(out/'training_curves.png',dpi=180)
    plt.close(fig)
    lines=['# Check-in pilot results','',
        'All numbers below are development results from consistent training and evaluation at 1.39 m/s pedestrian desired free-flow walking speed, not final test performance.','',
        '| Controller | Evaluations | Vehicle time loss | Entry delay | Combined vehicle proxy | Pedestrian time loss |',
        '|---|---:|---:|---:|---:|---:|']
    for algorithm,item in summary['controllers'].items():
        if not item['all_runs_eligible']:
            lines.append(f'| {algorithm} | {item["runs"]} | Incomplete/unsafe run: no all-demand ranking | - | - | - |')
            continue
        metrics=item['pooled_case_metrics']
        lines.append(f'| {algorithm} | {item["runs"]} | '+ ' | '.join(f'{metrics[k]["mean"]:.2f}' for k in
            ['vehicle_time_loss_s','vehicle_depart_delay_s','vehicle_combined_delay_proxy_s','pedestrian_time_loss_s'])+' |')
    lines+=['','Values are seconds per vehicle/person. Fixed-time has five demand-seed evaluations. Each RL algorithm has three trained policies evaluated on the same five demand seeds (15 paired cases). These are not 15 independent observed days.','',
        '## Training-seed variation','',
        '| Algorithm | Training seed | Vehicle combined proxy, mean ± demand-seed SD | Pedestrian time loss, mean ± demand-seed SD |',
        '|---|---:|---:|---:|']
    for algorithm in ['DQN','PPO']:
        item=summary['controllers'][algorithm]
        for seed,metrics in item.get('by_training_seed',{}).items():
            a,b=metrics['vehicle_combined_delay_proxy_s'],metrics['pedestrian_time_loss_s']
            lines.append(f'| {algorithm} | {seed} | {a["mean"]:.2f} ± {a["sample_std_across_demand"]:.2f} | {b["mean"]:.2f} ± {b["sample_std_across_demand"]:.2f} |')
    lines+=['','## Scope and issues','',
        '- Six completed pilot models: 2,048 cycle decisions each; no architecture, reward, or epoch search.',
        '- Test data were not generated or evaluated.',
        '- Each action preserves the 120-second cycle and all yellow, all-red, and pedestrian-clearance stages.',
        '- Training seed 202 initially stopped after a local W&B connection failure. That attempt was archived and excluded, and the seed restarted from scratch with unchanged settings.',
        '- The original prototype and its 180.37 s vehicle time-loss result are not comparable to this revised multimodal model.',
        '- Repeated stochastic episodes do not add independent observed traffic days. Time-blocked cross-validation and field calibration remain future work.',
        '- Hosted evidence: https://github.com/joelles-work/toronto-traffic-signal-rl and https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379 . Per-run URLs are indexed in experiments/freeflow_pilot_v1/wandb_runs.json.','',
        'Detailed machine-readable results and exploratory paired bootstrap intervals: `experiments/freeflow_pilot_v1/dev_summary.json`.']
    (out/'Pilot_Results.md').write_text('\n'.join(lines),encoding='utf-8')
    print('\n'.join(lines[:13]))


if __name__=='__main__':
    main()
