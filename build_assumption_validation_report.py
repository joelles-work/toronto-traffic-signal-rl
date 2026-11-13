"""Publish dev checks and a source citation for each declared assumption."""
import copy
import hashlib
import html
import json
from pathlib import Path
import re
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle, CondPageBreak
import build_literature_review as review

ROOT = Path(__file__).resolve().parent
FOLDER = ROOT/'experiments/dev_assumptions_v1'
OUT = ROOT/'output/literature'
CITY = 'https://www.toronto.ca/wp-content/uploads/2020/08/945f-TS_Traffic-Management_Pedestrian-Timing-Guidelines-2020.pdf'
REPO = 'https://github.com/joelles-work/toronto-traffic-signal-rl'


def main():
    summary = json.loads((FOLDER/'summary.json').read_text())
    derived = json.loads((FOLDER/'derived_checks.json').read_text())
    hosted = json.loads((FOLDER/'wandb_run.json').read_text())
    assert hosted['state'] == 'finished'
    assert summary['fixed_baseline_parity'] == 'PASS'
    assert len(summary['runs']) == 25
    assert hashlib.sha256((ROOT/'validate_pilot_assumptions.py').read_bytes()).hexdigest() == summary['plan']['implementation_sha256']
    urls = {**review.URLS, 'P9':'https://arxiv.org/abs/1709.06560', 'D10':CITY,
            'E1':REPO+'/blob/master/experiments/freeflow_pilot_v1/experiment.json',
            'E2':hosted['url'], 'E3':REPO+'/blob/master/experiments/dev_assumptions_v1/derived_checks.json'}

    def cite(text, md=False):
        def replace(m):
            keys = m[1].split(', ')
            if md:
                return ', '.join(f'[{k}]({urls[k]})' for k in keys)
            return '['+', '.join(f'<link href="{urls[k]}" color="#1256a0">{k}</link>' for k in keys)+']'
        return re.sub(r'\[((?:P\d+|D\d+|E\d+)(?:, (?:P\d+|D\d+|E\d+))*)\]', replace, text if md else html.escape(text))

    register = ['# Assumption and Source Register', '', 'November 13, 2026', '',
                'Every row cites its origin or defining protocol. Published precedent, software defaults, site guidance and our own declared choices are different kinds of support: a citation does not establish that an exact value is optimal.', '',
                'E1 is the frozen pilot protocol; E2 is the completed 25-case dev validation; E3 records the conditional timing checks and proposed training-derived bounds. These are primary records of our own study, not independent peer-reviewed validation.', '']
    categories = [('Data, control and reward', copy.deepcopy(review.DESIGN_AUDIT)),
                  ('Training settings', copy.deepcopy(review.TRAINING_AUDIT)),
                  ('Evaluation and seed choices', copy.deepcopy(review.EVALUATION_AUDIT))]
    for title, rows in categories:
        register += ['## '+title, '', '| Assumption / choice | Actual value | Source and what it supports |', '|---|---|---|']
        for name, value, explanation in rows:
            if name == 'Action values':
                explanation = 'The 7-s Type A minimum has direct City guidance [D10]. The 39-s total follows the fixed cycle arithmetic. The intermediate choices are a declared grid [E1]; all five were tested as constant plans on dev [E2], which does not prove they cover the best adaptive policy.'
            if name == 'Normalization':
                explanation += ' New check: west pending-entry clipping occurred in 29 of 1,149 decision observations, all in the incomplete 7/32 cases [E2]. A proposed replacement uses full training-origin counts as mathematical upper bounds [E3]; it requires retraining before new performance claims.'
            if name == 'Reward and weights':
                explanation += ' Rescoring weights 0, 0.5, 1 and 2 preferred the same constant 32/7 plan among eligible cases [E2]. This is local trajectory sensitivity, not evidence of learning with those weights.'
            if name == 'Training randomness':
                explanation = 'Independent training repeats support reproducibility and variance reporting [P9]. The exact integers are identifiers fixed in the protocol [E1], not values claimed to be optimal or taken from another paper.'
            if name == 'Five demand seeds':
                explanation = 'Five-run simulation evaluation has benchmark precedent [P4]; common patterns permit paired comparisons. These particular identifiers were fixed in advance [E1], and repeated arrivals within one hour are not independent observed days.'
            if name == 'What results establish':
                explanation += ' A dev-selected constant 32/7 comparison now gives 142.97 s/vehicle and 46.98 s/person, providing a stronger simple reference [E2]. It is not an independently tested out-of-sample result.'
            explanation += ' Actual implementation/value: [E1].'
            register.append('| '+' | '.join(cite(s,True).replace('|','/') for s in [name,value,explanation])+' |')
        register.append('')

    seed_text = ('Three independently seeded training repetitions (101, 202 and 303) were used to assess training variability, following recommendations for reproducible RL evaluation [P9]. Five common simulation seeds (11, 22, 33, 44 and 55) generated paired traffic patterns for all controllers, consistent with five-run traffic benchmarking [P4]. The seed identifiers were fixed before training [E1]; their numeric values carry no claimed statistical advantage.')
    register += ['## Paper-ready seed statement', '', cite(seed_text,True), '', '## Sources', '']
    for key, author, title, publication, url, location in review.SOURCES:
        url = urls[key]
        register += [f'**{key}. {author}.** [{title}]({url}). {publication} {location}', '']
    register += [f'**D10. City of Toronto (2019).** [Pedestrian Timing at Signalised Intersections]({CITY}), version 2.0, May 6, 2019; Sections 2.1-2.2 and 4.7. Type A is a usual-conditions design assumption; Types B/C and site requirements can require longer WALK times.', '',
                 f'**E1.** [Frozen project protocol]({urls["E1"]}); explicit preset values and seed identifiers.', '',
                 f'**E2.** [Completed 25-case dev validation]({urls["E2"]}); plan, trajectories and summary.', '',
                 f'**E3.** [Derived checks and proposed normalization bounds]({urls["E3"]}); not a newly trained model.', '']
    (OUT/'Assumption_and_Source_Register.md').write_text('\n'.join(register),encoding='utf-8')

    body = ParagraphStyle('validation-body',fontName='Helvetica',fontSize=10,leading=13,spaceAfter=8)
    heading = ParagraphStyle('validation-heading',fontName='Helvetica-Bold',fontSize=12,leading=15,spaceBefore=12,spaceAfter=7)
    cell = ParagraphStyle('validation-cell',fontName='Helvetica',fontSize=8.5,leading=11)
    story = [Paragraph('Development Validation and Assumption Sources', ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=20,leading=24,spaceAfter=10))]
    md = ['# Development Validation and Assumption Sources', '', 'November 13, 2026', '']
    def para(text):
        story.append(Paragraph(cite(text),body));md.extend([cite(text,True),''])
    def head(text):
        story.extend([CondPageBreak(90),Paragraph(html.escape(text),heading)]);md.extend(['## '+text,''])
    def table(headers, rows, widths):
        items = [[Paragraph('<b>'+html.escape(v)+'</b>',cell) for v in headers]]
        items += [[Paragraph(cite(str(v)),cell) for v in row] for row in rows]
        t=LongTable(items,colWidths=widths,repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9eff6')),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#c3cddc')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        story.extend([t,Spacer(1,7)])
        md.extend(['| '+' | '.join(headers)+' |','| '+' | '.join('---' for _ in headers)+' |'])
        md.extend('| '+' | '.join(str(v) for v in row)+' |' for row in rows)
        md.append('')
    para('November 13, 2026 | Small check-in validation | Development data only')
    para('The validation tested all five allowed timing choices as constant plans on the same five traffic seeds, keeping observed counts, 1.39 m/s walking speed, geometry and signal transitions fixed. The protocol was saved before these 25 cases ran [E2]; no test data or new RL training were used, and the 31/8 plan reproduced every frozen baseline result exactly.')
    head('1. The strongest simple plan is a useful comparison')
    para('Mean +/- sample standard deviation is reported across five traffic patterns. The 7/32 plan left 540 vehicles unfinished across five cases (108 per case on average), so its completed-trip delay is not ranked. All other constant plans completed their demand without collisions or teleports [E2].')
    rows=[]
    for action,item in summary['actions'].items():
        if item['all_cases_eligible']:
            v=item['metrics']['vehicle_combined_delay_proxy_s'];p=item['metrics']['pedestrian_time_loss_s']
            rows.append([f"{item['ew_walk_s']}/{item['ns_walk_s']}",f"{v['mean']:.2f} +/- {v['sample_std']:.2f}",f"{p['mean']:.2f} +/- {p['sample_std']:.2f}",'5/5 complete'])
        else:rows.append([f"{item['ew_walk_s']}/{item['ns_walk_s']}",'Not ranked','Not ranked','0/5 complete'])
    table(['EW/NS WALK (s)','Vehicle delay (s/vehicle)','Pedestrian delay (s/person)','Completion'],rows,[80,145,155,124])
    para('The dev-selected 32/7 plan reduced vehicle delay by 13.16 s/vehicle relative to 31/8, while pedestrian delay increased by 0.18 s/person. The paired exploratory intervals were -17.66 to -8.27 s/vehicle and -0.02 to +0.39 s/person [E2]. Selection and comparison used the same dev hour, so these are development findings rather than an independently confirmed improvement or a multiplicity-adjusted significance claim.')
    head('2. Observation scaling has a demonstrated limit')
    para('The west pending-entry feature exceeded its scale of 500 in 29 of 1,149 decision observations (2.52%), reaching 562/500 = 1.124. Every clipped observation occurred in the incomplete 7/32 cases; the twenty completed cases had none [E2]. Therefore, 500 is adequate for the completed constant cases examined, but cannot be justified as a general bound for the current action space.')
    para('A concrete candidate replacement divides pending entries by the full training-period vehicle count for each origin arm: north 1,280, south 1,262, east 2,038 and west 2,136 [E3]. A pending queue cannot exceed all vehicles generated at its origin, and the dev totals are lower than these training totals. This supplies a train-derived bound for these fixed data windows, but changes the input scale and must be followed by retraining before reporting new policy performance. It is a proposed revision, not an implemented improvement.')
    head('3. Pedestrian-weight sensitivity is local evidence')
    para('For the same trajectories, pedestrian weights 0, 0.5, 1 and 2 all preferred constant 32/7 among the four complete plans [E2]. This supports local robustness of that constant-plan ranking to those weights; it neither proves weight 1 is ethically or operationally optimal nor measures how PPO/DQN would learn after changing the reward. Vehicles are counted as units, without bus-passenger occupancy weighting.')
    head('4. The WALK bound has an official source')
    para('Toronto\'s timing guidance specifies a 7-s WALK minimum for Type A usual conditions, with separate clearance and total-crossing-time criteria [D10]. Using the modeled crossing lengths, all five plans pass twenty conditional checks of those inequalities [E3]. This supports the lower-bound source and model arithmetic, not the choice of every intermediate allocation or field certification. The 1.39 m/s desired simulation speed is separate from the City\'s timing-design criteria.')
    head('5. How to cite seeds and all other assumptions')
    para(seed_text)
    para('The companion Assumption and Source Register maps every declared design, training and evaluation choice to a research source, software definition, site record or our own frozen protocol. For unsupported exact values, the register cites the protocol as the origin and states what remains untested; it does not use a citation to imply external proof.')
    head('Decision for the check-in')
    para('Retain the existing pilot as a completed, explicitly bounded experiment; add the stronger constant-plan comparison and disclose the clipping finding. Cite the City source for the conditional WALK minimum and the RL evaluation sources for repeated seeded runs. The pending-entry scale has a concrete train-derived replacement ready for the next training revision. Neither the frozen RL settings nor reported model results were silently changed.')
    head('Linked sources')
    for key in ['P9','P4','D10','E1','E2','E3']:
        if key=='P9':label='Henderson et al. (2018), Deep Reinforcement Learning that Matters'
        elif key=='P4':label='Ault and Sharon (2021), Reinforcement Learning Benchmarks for Traffic Signal Control'
        elif key=='D10':label='City of Toronto, Pedestrian Timing at Signalised Intersections, May 6, 2019; Sections 2.1-2.2, 4.7'
        elif key=='E1':label='Frozen freeflow_pilot_v1 protocol'
        elif key=='E2':label='Completed dev_assumptions_v1 validation, W&B'
        else:label='Derived timing checks and proposed training-only bounds'
        para(f'[{key}] '+label)
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.drawString(54,29,'TCS 379 | Development validation | November 13, 2026');canvas.drawRightString(558,29,str(doc.page))
    pdf=OUT/'Dev_Validation_and_Assumption_Sources.pdf'
    SimpleDocTemplate(str(pdf),pagesize=(612,792),leftMargin=54,rightMargin=54,topMargin=45,bottomMargin=54,title='Development Validation and Assumption Sources',author='Jowel Akkeh').build(story,onFirstPage=footer,onLaterPages=footer)
    (OUT/'Dev_Validation_and_Assumption_Sources.md').write_text('\n'.join(md),encoding='utf-8')
    print(pdf)


if __name__=='__main__':
    main()
