"""Build the check-in from saved experiment outputs (bundled document Python)."""
import html
import json
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'/'report'
OUT.mkdir(parents=True,exist_ok=True)
summary=json.loads((ROOT/'results/baseline_dev/summary.json').read_text())
splits=json.loads((ROOT/'data/split_manifest.json').read_text())['splits']

title='Evaluating Deep Reinforcement Learning for Traffic Signal Control Under Real Toronto Demand'
sections=[
('I. METHOD (IMPLEMENTED)',[
('Data and validation.', 'The implemented loader reads the local Toronto multimodal turning-movement file, selects TCS 379 (Danforth Road / Eglinton Avenue East), and validates nonnegative, nonmissing counts in 36 vehicle-movement fields and four pedestrian fields. Cars, trucks, and buses are retained separately. The two study dates each contain 56 fifteen-minute records. The extracted daily totals match the proposal [1]: 40,294 vehicles and 4,665 pedestrians on June 19, 2024; 36,110 vehicles and 4,949 pedestrians on November 2, 2024. These are demand observations; measured intersection delay is unavailable.'),
('Frozen split.', 'Before the first demand-driven controller run, source row identifiers and SHA-256 file hashes were saved in data/split_manifest.json. The proposal did not specify a development partition. Its June afternoon period was therefore divided chronologically: 15:00-17:00 for training and 17:00-18:00 for development (Table I). The proposed primary and secondary tests remain reserved. Their counts were audited, but no test simulation or controller-performance measurement was made. Simulation episodes have separate generated arrivals and reset traffic state; no trips are shared between partitions. Adjacent same-day train/dev demand may remain correlated.'),
('Implemented model.', 'The running baseline is a vehicle-only SUMO 1.28.0 prototype with a four-arm orthogonal junction, 500 m approach and departure edges, a 13.89 m/s speed limit, and three dedicated movement lanes on every approach (right, through, left). This constructed geometry has not been checked against the field intersection or TorontoSUMONetworks. For each observed class and movement count, exactly that number of vehicles is generated, with independent uniform scheduled arrivals inside its fifteen-minute interval. This converts observed counts into synthetic arrival times; observed platoons and upstream coordination are not reproduced.'),
('Control.', 'A single preset 120 s fixed cycle is run. Its duration sequence is 7, 3, 1, 53, 4, 3, 42, 4, and 3 s: simultaneous east-west protected-left green/yellow, all-red, east-west green/yellow/all-red, and north-south green/yellow/all-red. The durations follow a simplified interpretation of the published PM timing card [2], combining walk and flashing-clearance stages into vehicle greens. Opposing left turns during general green yield in SUMO. Detector calls are absent. Pedestrian records load but no persons or crossing signals are simulated. Accordingly, this is not a validated reproduction of the complete City baseline.'),
('Metrics and execution.', 'For each run, vehicle time loss is the arithmetic mean of SUMO tripinfo timeLoss over all completed vehicles. SUMO defines this as lost time relative to ideal driving speed [3]; it is a delay proxy, not a field-calibrated measure of intersection control delay. A second proxy adds each vehicle\'s departDelay to its timeLoss before averaging, so vehicles waiting outside the simulated network are not hidden. Demand lasts 3,600 s; runs end at 7,200 s to drain queues, with no warm-up and teleporting disabled. Completed and outstanding counts are checked. Pedestrian delay is unavailable, not zero.'),
]),
('II. FIRST EXPERIMENTS',[
('Protocol.', 'Five independent simulation seeds (11, 22, 33, 44, 55) were fixed in the split manifest. Each run uses the same observed dev counts, with different within-interval arrival times and SUMO randomness. One geometry/control configuration was evaluated; no parameter search, architecture selection, reward tuning, or RL training was performed. DQN and PPO packages import successfully, but neither has a trained model or reported result. Future choices will be made on dev, with comparable tuning effort for all controllers. Test evaluation is deferred until model and analysis settings are frozen.'),
('Development result.', f'Table II reports the five seed-level means. Mean vehicle time loss is {summary["mean_time_loss_s"]["mean"]:.2f} +/- {summary["mean_time_loss_s"]["sample_std"]:.2f} s/vehicle (mean +/- sample standard deviation across five runs). Mean departure delay is {summary["mean_depart_delay_s"]["mean"]:.2f} +/- {summary["mean_depart_delay_s"]["sample_std"]:.2f} s/vehicle. The combined proxy is {summary["mean_total_delay_proxy_s"]["mean"]:.2f} +/- {summary["mean_total_delay_proxy_s"]["sample_std"]:.2f} s/vehicle. All 3,594 generated vehicles completed in each run. SUMO reported zero collisions, zero teleports, and no vehicles awaiting insertion or still running at termination. No improvement over another controller is claimed; no significance test is warranted for this single-controller experiment.'),
('Hardware and repeatability.', 'Experiments ran on Windows with Python 3.14.6, an Intel64 Family 6 Model 154 processor and 20 logical CPUs. PyTorch 2.15.0+cpu reports no CUDA device. SUMO-RL 1.4.5 and Stable-Baselines3 2.9.2 are installed. The exact resolved package versions and machine information are saved in requirements-lock.txt and evidence/environment.json. Per-seed routes, command arguments, SUMO logs, statistics, trip records, and metrics are retained under results/baseline_dev/. Variability here represents simulation randomness conditional on one observed dev hour, not day-to-day uncertainty.'),
]),
('III. EVIDENCE AND REVISED PLAN',[
('Evidence available.', 'The project folder is initialized as a local Git repository. Reproduction entry points are prepare_data.py, run_baseline.py, and log_wandb.py; the frozen split and aggregate results are machine-readable. Five completed W&B offline runs record the per-seed metrics, configuration, and evidence artifacts as a post-hoc import of saved SUMO outputs. Their identifiers and local directories are listed in results/wandb_runs.json. The initial failed W&B artifact-staging attempt is excluded from this successful-run index.'),
('Hosted evidence still missing.', 'No remote repository URL or hosted W&B run URL is available in the current workspace. Offline W&B directories do not satisfy the assignment\'s hosted-run link requirement. Publication/synchronization and verification of both hosted links remain required before submission. The report does not supply invented URLs.'),
('What remains incomplete and why.', 'The full proposal implementation is incomplete: verified Toronto geometry, pedestrian crossings and delay, faithful City signal mapping, and trained DQN/PPO controllers are absent. The large 111.85 s/vehicle average entry delay exposes an important boundary/capacity limitation of the constructed model. All demand does eventually complete, but the resulting delay cannot be interpreted as the actual intersection\'s performance. The existing experiments establish data loading and an end-to-end prototype, not the proposed multimodal comparison.'),
('Revised plan.', 'First verify lane counts, turn connections, storage, and crossing geometry against source drawings and TorontoSUMONetworks. Validate the timing card\'s phase-to-movement mapping and pedestrian walk/clearance intervals. Add pedestrians and inspect entry queues, residual vehicles, warm-up, and arrival assumptions. Then rerun a fixed-time baseline on the same frozen dev partition. Train DQN/PPO on the training partition, choosing state, reward, constraints, and training budget only on dev. Preserve operational clearance constraints and comparable tuning budgets. Freeze the final models before evaluating both reserved test periods; report five-seed means and standard deviations and paired uncertainty for small differences. If any model is changed after viewing test performance, explicitly relabel that test as development data.'),
]),
]

refs=[
'[1] J. Akkeh, "Evaluating Deep Reinforcement Learning for Traffic Signal Control Under Real Toronto Demand," project proposal, York University, 2026. Data: local Toronto file tmc_raw_data_2020_2029.csv; source hash and selected record identifiers are in the split manifest.',
'[2] City of Toronto, "Current Signal Timing Information: Eglinton Ave E &amp; Danforth Rd, TCS 379," Oct. 31, 2019, reproduced in WSP Canada Group Limited, 320 McCowan Road Transportation Impact Study, Feb. 14, 2020, App. B, PDF p. 147. <link href="https://320mccowan.ca/wp-content/uploads/2020/04/TransportationReport_320McCowan.pdf" color="blue">Public source PDF</link>.',
'[3] Eclipse SUMO, "TripInfo," SUMO documentation, accessed Nov. 9, 2026. <link href="https://sumo.dlr.de/docs/Simulation/Output/TripInfo.html" color="blue">Official metric definitions</link>.',
]

style=ParagraphStyle('body',fontName='Times-Roman',fontSize=10,leading=11.7,alignment=TA_JUSTIFY,spaceAfter=5)
heading=ParagraphStyle('heading',parent=style,alignment=TA_CENTER,fontSize=10,leading=12,spaceBefore=7,spaceAfter=6,keepWithNext=True)
small=ParagraphStyle('small',parent=style,fontSize=8,leading=9.3,alignment=0,spaceAfter=5)
caption=ParagraphStyle('caption',parent=small,alignment=TA_CENTER,spaceBefore=5,spaceAfter=5,keepWithNext=True)
story=[]

def paragraph(text,sty=style):
    return Paragraph(text,sty)

def table(data,widths):
    obj=Table([[paragraph(str(c),small) for c in row] for row in data],colWidths=widths,hAlign='CENTER')
    obj.setStyle(TableStyle([('LINEABOVE',(0,0),(-1,0),.6,colors.black),('LINEBELOW',(0,0),(-1,0),.4,colors.black),('LINEBELOW',(0,-1),(-1,-1),.6,colors.black),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
    return obj

split_table=[['Partition / period','Intervals','Vehicles','Peds']]
for key,label in [('train','Train: June 19, 15-17'),('dev','Dev: June 19, 17-18'),('test_primary','Test: Nov. 2, 15-18'),('test_secondary','Test: June 19, 07-10')]:
    s=splits[key]
    split_table.append([label,str(s['intervals']),f'{s["vehicles"]:,}',f'{s["pedestrians"]:,}'])
metric_table=[['Seed','Time loss','Entry delay','Combined']]
for r in summary['runs']:
    metric_table.append([r['seed'],f'{r["mean_time_loss_s"]:.2f}',f'{r["mean_depart_delay_s"]:.2f}',f'{r["mean_total_delay_proxy_s"]:.2f}'])
metric_table.append(['Mean +/- SD','180.37 +/- 11.19','111.85 +/- 6.31','292.22 +/- 16.63'])

story.append(paragraph('<b>Abstract</b> - This check-in reports an implemented demand loader, a frozen chronological split, and five SUMO runs of a fixed-cycle vehicle-only prototype. The development result is 180.37 +/- 11.19 s/vehicle of simulated time loss. Geometry and pedestrian fidelity remain unresolved; no DRL result or test performance is claimed. Hosted evidence links remain a submission dependency.'))
for section,paras in sections:
    story.append(paragraph(section,heading))
    for lead,body in paras:
        story.append(paragraph('<i>'+lead+'</i> '+body))
        if lead=='Frozen split.':
            story.append(paragraph('TABLE I<br/>FROZEN DEMAND PARTITIONS (2024)',caption))
            story.append(table(split_table,[133,39,40,40]))
            story.append(Spacer(1,5))
        if lead=='Development result.':
            story.append(paragraph('TABLE II<br/>DEV RESULTS IN SECONDS PER VEHICLE',caption))
            story.append(table(metric_table,[53,67,65,67]))
            story.append(Spacer(1,5))
story.append(paragraph('REFERENCES',heading))
story.extend(paragraph(r,small) for r in refs)

W,H=8.5*inch,11*inch
left=45
bottom=54
col=252
gap=18

def first(canvas,doc):
    canvas.saveState()
    p=paragraph(title,ParagraphStyle('title',fontName='Times-Roman',fontSize=22,leading=24,alignment=TA_CENTER))
    _,h=p.wrap(W-90,120)
    p.drawOn(canvas,left,H-48-h)
    y=H-48-h-22
    for text in ['Jowel Akkeh','Department of Civil Engineering, Lassonde School of Engineering','York University, Toronto, Canada']:
        canvas.setFont('Times-Roman',10)
        canvas.drawCentredString(W/2,y,text)
        y-=12
    canvas.setFont('Times-Italic',9)
    canvas.drawCentredString(W/2,y-3,'GS/ESS 5420 - Individual progress report - November 9, 2026')
    footer(canvas,doc)
    canvas.restoreState()

def footer(canvas,doc):
    canvas.setFont('Times-Roman',8)
    canvas.drawCentredString(W/2,32,str(doc.page))

doc=BaseDocTemplate(str(OUT/'Progress_Report_Jowel_Akkeh.pdf'),pagesize=(W,H),title=title,author='Jowel Akkeh')
frames_first=[Frame(left+i*(col+gap),bottom,col,516,id=f'first{i}',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0) for i in range(2)]
frames_rest=[Frame(left+i*(col+gap),bottom,col,H-108,id=f'body{i}',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0) for i in range(2)]
doc.addPageTemplates([PageTemplate(id='first',frames=frames_first,onPage=first,autoNextPageTemplate='body'),PageTemplate(id='body',frames=frames_rest,onPage=footer)])
doc.build(story)

# Also retain an editable IEEEtran source with identical substantive text.
def plain(value):
    return html.unescape(re.sub('<[^>]+>','',value))

def tex(value):
    value=plain(value)
    return ''.join({'&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}'}.get(c,c) for c in value).replace('+/-',r'$\pm$')

source=[r'\documentclass[conference]{IEEEtran}',r'\usepackage[T1]{fontenc}',r'\usepackage{url}',r'\begin{document}',r'\title{'+tex(title)+'}',r'\author{\IEEEauthorblockN{Jowel Akkeh}\IEEEauthorblockA{Department of Civil Engineering, Lassonde School of Engineering\\York University, Toronto, Canada}}',r'\maketitle',r'\begin{abstract}This check-in reports an implemented demand loader, frozen chronological split, and five fixed-cycle prototype runs. Mean dev time loss is $180.37\pm11.19$ s/vehicle. Geometry and pedestrian fidelity remain unresolved; no DRL or test result is claimed. Hosted evidence links remain required.\end{abstract}']
for section,paras in sections:
    source.append(r'\section{'+tex(section.split('. ',1)[1])+'}')
    for lead,body in paras:
        source.append(r'\paragraph{'+tex(lead.rstrip('.'))+'} '+tex(body)+'\n')
        if lead in ('Frozen split.','Development result.'):
            data=split_table if lead=='Frozen split.' else metric_table
            cap='Frozen demand partitions (2024)' if lead=='Frozen split.' else 'Dev results in seconds per vehicle'
            source.extend([r'\begin{table}[ht]',r'\centering\footnotesize',r'\caption{'+cap+'}',r'\begin{tabular}{lrrr}\hline'])
            for row in data:
                source.append(' & '.join(tex(str(c)) for c in row)+r' \\')
            source.extend([r'\hline\end{tabular}',r'\end{table}'])
source.append(r'\begin{thebibliography}{3}')
for i,r in enumerate(refs,1):
    source.append(r'\bibitem{r'+str(i)+'} '+tex(re.sub(r'^\[\d+\] ','',r)))
source.extend([r'\end{thebibliography}',r'\end{document}'])
(OUT/'main.tex').write_text('\n'.join(source),encoding='utf-8')
print(OUT/'Progress_Report_Jowel_Akkeh.pdf')
