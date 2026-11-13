"""Write the checklist-focused IEEE-style check-in from saved experiment evidence."""
import html
import json
from pathlib import Path
import re
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER,TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import BaseDocTemplate,Frame,PageTemplate,Paragraph,Spacer,Table,TableStyle

ROOT=Path(__file__).resolve().parent
PILOT=ROOT/'experiments/freeflow_pilot_v1'
OUT=ROOT/'output/checkin'
OUT.mkdir(parents=True,exist_ok=True)
summary=json.loads((PILOT/'dev_summary.json').read_text())
config=json.loads((PILOT/'experiment.json').read_text())
split=json.loads((PILOT/'assets/split_manifest.json').read_text())['splits']
env=json.loads((ROOT/'evidence/environment.json').read_text())
fixed=summary['controllers']['fixed']['pooled_case_metrics']
ppo=summary['controllers']['PPO']
title='Evaluating Deep Reinforcement Learning for Traffic Signal Control Under Real Toronto Demand'

report_text=json.loads((OUT/'report_text.json').read_text(encoding='utf-8'))
sections=report_text['sections']

refs=[
'[1] City of Toronto, "Traffic volumes - multimodal intersection turning movement counts," Toronto Open Data. <link href="https://open.toronto.ca/dataset/traffic-volumes-at-intersections-for-all-modes/" color="blue">Dataset and dictionary</link>, accessed Nov. 11, 2026.',
'[2] OpenStreetMap contributors, "Eglinton Avenue East / Danforth Road map extract," ODbL 1.0, downloaded Nov. 9, 2026. <link href="https://www.openstreetmap.org/copyright" color="blue">Attribution and licence</link>.',
'[3] City of Toronto, "Current Signal Timing Information: TCS 379," Oct. 31, 2019, in WSP, 320 McCowan Road Transportation Impact Study, Feb. 14, 2020, App. B, PDF p. 147. <link href="https://320mccowan.ca/wp-content/uploads/2020/04/TransportationReport_320McCowan.pdf" color="blue">Source report</link>.',
'[4] Stable-Baselines3, "DQN and PPO parameters," v. 2.9.2. <link href="https://stable-baselines3.readthedocs.io/en/master/modules/dqn.html" color="blue">DQN</link>; <link href="https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html" color="blue">PPO</link>, accessed Nov. 12, 2026.',
'[5] Eclipse SUMO, "Libsumo." <link href="https://sumo.dlr.de/docs/Libsumo.html" color="blue">Documentation</link>, accessed Nov. 11, 2026.',
'[6] Eclipse SUMO, "TripInfo." <link href="https://sumo.dlr.de/docs/Simulation/Output/TripInfo.html" color="blue">Metric definitions</link>, accessed Nov. 11, 2026.',
]
refs.append('[7] J. Akkeh, "Toronto TCS 379 pilot experiment records," Weights & Biases. <link href="https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379" color="blue">Project and training runs</link>; <link href="https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379/runs/109ddkqr" color="blue">dev comparison</link>, uploaded Nov. 12, 2026.')
refs.append('[8] J. Akkeh, "Toronto traffic signal RL check-in," GitHub. <link href="https://github.com/joelles-work/toronto-traffic-signal-rl" color="blue">Code, saved models, and report</link>, Nov. 11, 2026.')
refs.append('[9] Eclipse SUMO, "Persons: desired maximum walking speed." <link href="https://sumo.dlr.de/docs/Specification/Persons.html" color="blue">Default 1.39 m/s</link>, accessed Nov. 12, 2026.')
refs.append('[10] TorontoSUMONetworks contributors, "TorontoSUMONetworks," GitHub, revision 35dee7b. <link href="https://github.com/Jahandad-Baloch/TorontoSUMONetworks" color="blue">Source project</link>, accessed Nov. 11, 2026.')
refs.append('[11] A. Raffin et al., "Stable-Baselines3: Reliable Reinforcement Learning Implementations," JMLR, vol. 22, no. 268, pp. 1-8, 2021. <link href="https://jmlr.org/papers/v22/20-1364.html" color="blue">Software paper</link>.')
refs.append('[12] P. Henderson et al., "Deep Reinforcement Learning that Matters," AAAI, 2018. <link href="https://arxiv.org/abs/1709.06560" color="blue">Reproducibility and random seeds</link>.')
refs.append('[13] J. Ault and G. Sharon, "Reinforcement Learning Benchmarks for Traffic Signal Control," NeurIPS Datasets and Benchmarks, 2021. <link href="https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/file/f0935e4cd5920aa6c7c996a5ee53a70f-Paper-round1.pdf" color="blue">Five-seed evaluation</link>.')
refs.append('[14] City of Toronto, "Pedestrian Timing at Signalised Intersections," version 2.0, May 6, 2019, sec. 2.2. <link href="https://www.toronto.ca/wp-content/uploads/2020/08/945f-TS_Traffic-Management_Pedestrian-Timing-Guidelines-2020.pdf" color="blue">Usual-conditions WALK minimum</link>.')
refs.append('[15] J. Akkeh, "Assumption/source register and development validation," Nov. 13, 2026. <link href="https://github.com/joelles-work/toronto-traffic-signal-rl/blob/master/output/literature/Assumption_and_Source_Register.md" color="blue">All assumptions and sources</link>; <link href="https://forge.coreweave.com/wandb/joelle1-york-university/toronto-tcs379/runs/wcirpdsc" color="blue">25-case validation</link>.')
tables={}
tables['Study periods.']=('I','STUDY PERIODS AND COUNTS (2024)',[
    ['Set / date / time','Intervals','Vehicles','People'],
    ['Train: Jun. 19, 15-17',8,'6,716',810],['Dev: Jun. 19, 17-18',4,'3,594',518],
    ['Test: Nov. 2, 15-18',12,'9,961','1,598'],['Test: Jun. 19, 07-10',12,'8,275',661]], [129,36,45,42])
tables['Model settings.']=('II','TRAINING PRESETS AND THEIR PURPOSE',[
    ['Setting','Value and purpose'],
    ['Network','Two layers of 64 neurons: a small shared architecture for 25 inputs and five timing choices.'],
    ['Learning rate','0.0003: small learning updates; PPO default, also used for DQN to share one preset rate.'],
    ['Discount / batch','0.99 weights future reward; batches of 64 experiences average each update while limiting CPU cost.'],
    ['Training budget','2,048 decisions: the same bounded pilot budget for each model.'],
    ['DQN memory / start','Capacity 20,000 experiences limits replay memory; collect 180 initial experiences before learning starts.'],
    ['DQN exploration','Final random-action probability 0.05 retains 5% exploration during training. Evaluation uses deterministic choices.'],
    ['PPO collection','256 new decisions per update gives eight collection blocks within the pilot budget.'],
    ['PPO updates','10 passes through each block reuse its data; GAE 0.95 balances short- and longer-term reward estimates (library defaults).']], [80,172])

tables['Pilot comparison.']=('III','AVERAGE DELAY ON THE DEVELOPMENT PERIOD',[
    ['Controller','Vehicle delay (s/vehicle)','Pedestrian delay (s/person)'],
    *[[a,*[f'{summary["controllers"][a]["pooled_case_metrics"][k]["mean"]:.2f}' for k in
        ['vehicle_combined_delay_proxy_s','pedestrian_time_loss_s']]] for a in ['fixed','DQN','PPO']]], [72,90,90])
policy_table=[['PPO training seed','Vehicle delay','Pedestrian delay']]
for seed,metrics in ppo['by_training_seed'].items():
    a,b=metrics['vehicle_combined_delay_proxy_s'],metrics['pedestrian_time_loss_s']
    policy_table.append([seed,f'{a["mean"]:.2f} +/- {a["sample_std_across_demand"]:.2f}',f'{b["mean"]:.2f} +/- {b["sample_std_across_demand"]:.2f}'])


# IEEE references follow the order in which sources first appear in the text.
citation_order=[]
for _,paragraphs in sections:
    for _,paragraph in paragraphs:
        for match in re.finditer(r'\[(\d+)\]',paragraph):
            number=int(match[1])
            if number not in citation_order:
                citation_order.append(number)
citation_map={old:new for new,old in enumerate(citation_order,1)}
def renumber(text):
    return re.sub(r'\[(\d+)\]',lambda m:'['+str(citation_map[int(m[1])])+']',text)
sections=[(name,[(lead,renumber(text)) for lead,text in paragraphs]) for name,paragraphs in sections]
refs=[renumber(refs[old-1]) for old in citation_order]

body=ParagraphStyle('body',fontName='Times-Roman',fontSize=10,leading=11.5,alignment=TA_JUSTIFY,spaceAfter=4)
small=ParagraphStyle('small',parent=body,fontSize=8,leading=9.2,alignment=0,spaceAfter=3)
heading=ParagraphStyle('heading',parent=body,alignment=TA_CENTER,spaceBefore=7,spaceAfter=6,keepWithNext=True)
caption=ParagraphStyle('caption',parent=small,alignment=TA_CENTER,spaceBefore=5,spaceAfter=5,keepWithNext=True)
story=[]
abstract=report_text['abstract']
story.append(Paragraph('<b>Abstract</b> - '+html.escape(abstract),body))

def make_table(data,widths):
    obj=Table([[Paragraph(str(c),small) for c in row] for row in data],colWidths=widths,hAlign='CENTER')
    obj.setStyle(TableStyle([('LINEABOVE',(0,0),(-1,0),.6,colors.black),('LINEBELOW',(0,0),(-1,0),.4,colors.black),('LINEBELOW',(0,-1),(-1,-1),.6,colors.black),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
    return obj

for number,(section,paragraphs) in enumerate(sections,1):
    story.append(Paragraph(['I','II','III'][number-1]+'. '+section,heading))
    for lead,text in paragraphs:
        story.append(Paragraph(html.escape(text),body))
        if lead in tables:
            n,cap,data,widths=tables[lead]
            story.append(Paragraph('TABLE '+n+'<br/>'+cap,caption))
            story.append(make_table(data,widths))
            story.append(Spacer(1,5))
story.append(Paragraph('REFERENCES',heading))
story.extend(Paragraph(r,small) for r in refs)

W,H=8.5*inch,11*inch
left,bottom,col,gap=45,54,252,18
def footer(canvas,doc):
    canvas.setFont('Times-Roman',8)
    canvas.drawCentredString(W/2,32,str(doc.page))
def first(canvas,doc):
    p=Paragraph(title,ParagraphStyle('title',fontName='Times-Roman',fontSize=22,leading=24,alignment=TA_CENTER))
    _,height=p.wrap(W-90,120)
    p.drawOn(canvas,left,H-48-height)
    y=H-48-height-22
    for text in ['Jowel Akkeh','Department of Civil Engineering, Lassonde School of Engineering','York University, Toronto, Canada']:
        canvas.setFont('Times-Roman',10);canvas.drawCentredString(W/2,y,text);y-=12
    canvas.setFont('Times-Italic',9)
    canvas.drawCentredString(W/2,y-3,'GS/ESS 5420 - Individual check-in - November 13, 2026')
    footer(canvas,doc)
doc=BaseDocTemplate(str(OUT/'Progress_Report_Jowel_Akkeh.pdf'),pagesize=(W,H),title=title,author='Jowel Akkeh')
first_frames=[Frame(left+i*(col+gap),bottom,col,554,id=f'f{i}',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0) for i in range(2)]
other_frames=[Frame(left+i*(col+gap),bottom,col,H-108,id=f'b{i}',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0) for i in range(2)]
doc.addPageTemplates([PageTemplate(id='first',frames=first_frames,onPage=first,autoNextPageTemplate='body'),PageTemplate(id='body',frames=other_frames,onPage=footer)])
doc.build(story)

def reference_text(s):
    return re.sub(r'<link href="([^"]+)"[^>]*>(.*?)</link>', lambda m: m[2]+' ('+m[1]+')', s)

def plain(s):return html.unescape(re.sub('<[^>]+>','',s))
def tex(s):
    return ''.join({'&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}'}.get(c,c) for c in plain(s)).replace('+/-',r'$\pm$')
source=[r'\documentclass[conference]{IEEEtran}',r'\usepackage[T1]{fontenc}',r'\usepackage{url}',r'\begin{document}',r'\title{'+tex(title)+'}',r'\author{\IEEEauthorblockN{Jowel Akkeh}\IEEEauthorblockA{Department of Civil Engineering, Lassonde School of Engineering\\York University, Toronto, Canada}}',r'\maketitle',r'\begin{abstract}'+tex(abstract)+r'\end{abstract}']
markdown=['# '+title,'','Jowel Akkeh - GS/ESS 5420 - November 13, 2026','',abstract]
for section,paragraphs in sections:
    source.append(r'\section{'+tex(section)+'}')
    markdown+=['','## '+section]
    for lead,text in paragraphs:
        source.append(tex(text)+'\n')
        markdown+=['',plain(text)]
        if lead in tables:
            number,cap,data,_=tables[lead]
            source += [r'\begin{table}[ht]\centering\footnotesize',r'\caption{'+tex(cap)+'}',r'\setlength{\tabcolsep}{2pt}\begin{tabular}{'+''.join('p{'+str(w-4)+'pt}' for w in tables[lead][3])+r'}\hline']
            source += [' & '.join(tex(str(c)) for c in row)+r' \\' for row in data]
            source += [r'\hline\end{tabular}\end{table}']
            markdown+=['','Table '+number+': '+cap,'','| '+' | '.join(str(c) for c in data[0])+' |','| '+' | '.join('---' for c in data[0])+' |']
            markdown += ['| '+' | '.join(str(c) for c in row)+' |' for row in data[1:]]
source.append(r'\begin{thebibliography}{15}')
for i,r in enumerate(refs,1):
    source.append(r'\bibitem{r'+str(i)+'} '+tex(reference_text(re.sub(r'^\[\d+\] ','',r))))
source += [r'\end{thebibliography}',r'\end{document}']
markdown += ['', '## References', *[plain(reference_text(r)) for r in refs]]
(OUT/'main.tex').write_text('\n'.join(source),encoding='utf-8')
(OUT/'Progress_Report_Editable.md').write_text('\n'.join(markdown),encoding='utf-8')
print(OUT/'Progress_Report_Jowel_Akkeh.pdf')
