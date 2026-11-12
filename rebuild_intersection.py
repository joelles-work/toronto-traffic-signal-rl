"""Build an openable georeferenced TCS 379 revision from the saved OSM extract.

Google Maps was used for visual comparison, not as a traced geometry source.
OSM map data: (c) OpenStreetMap contributors, ODbL 1.0.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess
import xml.etree.ElementTree as ET

import sumolib
from shapely.geometry import LineString
from shapely.ops import substring, unary_union

ROOT=Path(__file__).resolve().parent
MODEL=ROOT/'models'/'eglinton_danforth'
SOURCE=MODEL/'source'


def xml(root,path):
    ET.indent(root)
    ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)


def command(args,name):
    run=subprocess.run(args,capture_output=True,text=True)
    (MODEL/f'{name}.log').write_text(run.stdout+run.stderr,encoding='utf-8')
    if run.returncode:
        raise RuntimeError(run.stderr)


def road(edge):
    return edge.getName() in ('Eglinton Avenue East','Danforth Road') and edge.allows('passenger')


def separate_east_carriageways(incoming,outgoing):
    """Avoid shared OSM nodes paving over the eastern median.

    Retain the source road's georeferenced spine, but use independent EB/WB
    nodes and a 2.4 m model median. The gap width is an explicit assumption.
    """
    prefix=MODEL/'carriageways'
    command([sumolib.checkBinary('netconvert'),'--sumo-net-file',str(MODEL/'intersection.net.xml'),
        '--plain-output-prefix',str(prefix),'--output-file',str(MODEL/'geometry_base.net.xml')], 'export_geometry')
    nt=ET.parse(str(prefix)+'.nod.xml')
    et=ET.parse(str(prefix)+'.edg.xml')
    ct=ET.parse(str(prefix)+'.con.xml')
    nodes={n.get('id'):n for n in nt.getroot().findall('node')}
    edges={e.get('id'):e for e in et.getroot().findall('edge')}
    outer=edges[outgoing['e'][-1].getID()]
    points=[tuple(map(float,p.split(','))) for p in outer.get('shape').split()]
    a,b=points[:2]
    dx,dy=b[0]-a[0],b[1]-a[1]
    length=math.hypot(dx,dy)
    points.insert(0,(a[0]-dx/length*250,a[1]-dy/length*250))
    spine=LineString(points)
    changed={}
    for tag,path in [('WB',incoming['e']),('EB',outgoing['e'])]:
        for old_edge in path:
            e=edges[old_edge.getID()]
            original_ids=[e.get('from'),e.get('to')]
            positions=[]
            for attr,old_id in zip(('from','to'),original_ids):
                node=nodes[old_id]
                from shapely.geometry import Point
                pos=spine.project(Point(float(node.get('x')),float(node.get('y'))))
                positions.append(pos)
                if old_id=='TCS379':
                    continue
                new_id=f'{old_id}_{tag}'
                if new_id not in changed:
                    delta=0.2
                    p=spine.interpolate(pos)
                    before=spine.interpolate(max(0,pos-delta))
                    after=spine.interpolate(min(spine.length,pos+delta))
                    vx,vy=after.x-before.x,after.y-before.y
                    norm=math.hypot(vx,vy)
                    sign=1 if tag=='WB' else -1
                    attrs=dict(node.attrib)
                    attrs.update(id=new_id,x=f'{p.x-sign*vy/norm*1.2:.3f}',y=f'{p.y+sign*vx/norm*1.2:.3f}')
                    attrs.pop('shape',None)
                    attrs['type']='priority' if node.get('type')!='dead_end' else 'dead_end'
                    new_node=ET.SubElement(nt.getroot(),'node',attrs)
                    changed[new_id]=new_node
                e.set(attr,new_id)
            segment=substring(spine,*positions).offset_curve(-1.2,join_style=2)
            e.set('spreadType','right')
            e.set('shape',' '.join(f'{x:.3f},{y:.3f}' for x,y in segment.coords))
            for lane in e.findall('lane'):
                lane.attrib.pop('shape',None)
    used={e.get(key) for e in edges.values() for key in ('from','to')}
    for node in list(nt.getroot().findall('node')):
        if node.get('id') not in used:
            nt.getroot().remove(node)
    # Original cross-carriageway connections at the shared nodes are not roads.
    for c in list(ct.getroot()):
        if c.tag=='connection':
            a,b=edges.get(c.get('from')),edges.get(c.get('to'))
            if a is None or b is None or a.get('to')!=b.get('from'):
                ct.getroot().remove(c)
        elif c.get('node') and c.get('node') not in used:
            ct.getroot().remove(c)
    xml(nt.getroot(),str(prefix)+'.nod.xml')
    xml(et.getroot(),str(prefix)+'.edg.xml')
    xml(ct.getroot(),str(prefix)+'.con.xml')
    command([sumolib.checkBinary('netconvert'),'--node-files',str(prefix)+'.nod.xml',
        '--edge-files',str(prefix)+'.edg.xml','--connection-files',str(prefix)+'.con.xml',
        '--type-files',str(prefix)+'.typ.xml','--tls.rebuild','true',
        '--output-file',str(MODEL/'intersection.net.xml'),'--output.street-names','true',
        '--junctions.corner-detail','12'], 'separate_carriageways')


def chain(edge,backwards):
    result=[edge]
    length=edge.getLength()
    seen={edge.getID()}
    while length<230:
        node=edge.getFromNode() if backwards else edge.getToNode()
        if node.getType().startswith('traffic_light'):
            break
        options=node.getIncoming() if backwards else node.getOutgoing()
        options=[e for e in options if road(e) and e.getName()==edge.getName() and e.getID() not in seen]
        if not options:
            break
        # Continue along the same carriageway, avoiding reverse-direction edges.
        vector=(edge.getToNode().getCoord()[0]-edge.getFromNode().getCoord()[0],edge.getToNode().getCoord()[1]-edge.getFromNode().getCoord()[1])
        def score(e):
            a,b=e.getFromNode().getCoord(),e.getToNode().getCoord()
            v=(b[0]-a[0],b[1]-a[1])
            return sum(x*y for x,y in zip(v,vector))/(math.hypot(*v)*math.hypot(*vector))
        candidate=max(options,key=score)
        if score(candidate)<0.5:
            break
        result.append(candidate)
        length+=candidate.getLength()
        seen.add(candidate.getID())
        edge=candidate
    return list(reversed(result)) if backwards else result


def main():
    raw=SOURCE/'site.osm.xml'
    tree=ET.parse(raw)
    # Remove transit stop markers to permit joining the separate signal nodes.
    # This revision has no scheduled transit stops; original source stays intact.
    for node in tree.getroot().findall('node'):
        for tag in list(node.findall('tag')):
            if tag.get('k') in ('public_transport','bus','tram','railway') or (tag.get('k')=='highway' and tag.get('v')=='bus_stop'):
                node.remove(tag)
    for relation in list(tree.getroot().findall('relation')):
        tags={z.get('k'):z.get('v') for z in relation.findall('tag')}
        if tags.get('type')=='route':
            tree.getroot().remove(relation)
    xml(tree.getroot(),SOURCE/'roads_only.osm.xml')
    command([sumolib.checkBinary('netconvert'),'--osm-files',str(SOURCE/'roads_only.osm.xml'),
        '--node-files',str(MODEL/'join.nod.xml'),'--output-file',str(MODEL/'joined.net.xml'),
        '--keep-edges.in-geo-boundary=-79.250,43.734,-79.242,43.741',
        '--geometry.remove','true','--osm.turn-lanes','true','--osm.lane-access','true',
        '--sidewalks.guess','true','--sidewalks.guess.max-speed','20',
        '--crossings.guess','true','--output.street-names','true','--no-turnarounds','true',
        '--keep-edges.by-type','highway.primary,highway.secondary','--junctions.corner-detail','12'], 'import')
    net=sumolib.net.readNet(str(MODEL/'joined.net.xml'),withInternal=True)
    junction=net.getNode('TCS379')
    center=junction.getCoord()
    incoming={}
    outgoing={}
    for backwards,edges,target in [(True,junction.getIncoming(),incoming),(False,junction.getOutgoing(),outgoing)]:
        for e in edges:
            if not road(e):
                continue
            outer=e.getFromNode().getCoord() if backwards else e.getToNode().getCoord()
            if e.getName()=='Eglinton Avenue East':
                arm='e' if outer[0]>center[0] else 'w'
            else:
                arm='n' if outer[1]>center[1] else 's'
            assert arm not in target
            target[arm]=chain(e,backwards)
    assert set(incoming)==set(outgoing)==set('nsew')
    keep=sorted({e.getID() for group in (incoming,outgoing) for path in group.values() for e in path})
    command([sumolib.checkBinary('netconvert'),'--sumo-net-file',str(MODEL/'joined.net.xml'),
        '--keep-edges.explicit='+','.join(keep),'--output-file',str(MODEL/'intersection.net.xml'),
        '--output.street-names','true','--junctions.corner-detail','12'], 'crop')
    path=MODEL/'intersection.net.xml'
    separate_east_carriageways(incoming,outgoing)
    nt=ET.parse(path)
    root=nt.getroot()
    close_in={arm:edges[-1].getID() for arm,edges in incoming.items()}
    close_out={arm:edges[0].getID() for arm,edges in outgoing.items()}
    # Incomplete OSM turn arrows can make unmarked curb lanes through-only.
    # Specify the observed approach movement topology rather than silently
    # dropping right-turn demand. Lane allocation remains a documented model.
    patch=ET.Element('connections')
    dest={'n':{'r':'w','s':'s','l':'e'},'s':{'r':'e','s':'n'},
          'e':{'r':'n','s':'w','l':'s'},'w':{'r':'s','s':'e','l':'n'}}
    cropped=sumolib.net.readNet(str(path))
    existing_pairs={(c.get('from'),c.get('to')) for c in root.findall('connection')}
    # One signal-controlled crossing per leg avoids treating the refuge as a
    # second crossing entry during flashing clearance (which SUMO represents red).
    for crossing in root.findall('edge'):
        if crossing.get('function')!='crossing':
            continue
        if not crossing.get('id').startswith(':TCS379'):
            # The isolated-junction model must not let measured intersection
            # pedestrians bypass its signal through guessed approach crossings.
            other_node=crossing.get('id')[1:].rsplit('_c',1)[0]
            ET.SubElement(patch,'crossing',node=other_node,edges=crossing.get('crossingEdges'),discard='true')
        else:
            crossed=set(crossing.get('crossingEdges').split())
            if crossed & {close_in['e'],close_out['e'],close_in['w'],close_out['w']}:
                ET.SubElement(patch,'crossing',node='TCS379',edges=crossing.get('crossingEdges'),discard='true')
    for arm in 'ew':
        ET.SubElement(patch,'crossing',node='TCS379',edges=f'{close_in[arm]} {close_out[arm]}',priority='1',width='4')
    for arm,a in close_in.items():
        for b in close_out.values():
            if (a,b) in existing_pairs:
                ET.SubElement(patch,'delete',{'from':a,'to':b})
        lanes=[l.getIndex() for l in cropped.getEdge(a).getLanes() if l.allows('passenger')]
        for move,target_arm in dest[arm].items():
            targets=[l.getIndex() for l in cropped.getEdge(close_out[target_arm]).getLanes() if l.allows('passenger')]
            if move=='r':
                lane_pairs=[(lanes[0],targets[0])]
            elif move=='l':
                lane_pairs=[(lanes[-1],targets[-1])]
            else:
                through=lanes[:-1] if 'l' in dest[arm] else lanes
                lane_pairs=[(lane,targets[min(i,len(targets)-1)]) for i,lane in enumerate(through)]
                if len(targets)>len(through):
                    lane_pairs.extend((through[-1],lane) for lane in targets[len(through):])
            for a_lane,b_lane in lane_pairs:
                ET.SubElement(patch,'connection',{'from':a,'to':close_out[target_arm],
                    'fromLane':str(a_lane),'toLane':str(b_lane)})
    xml(patch,MODEL/'movements.con.xml')
    command([sumolib.checkBinary('netconvert'),'--sumo-net-file',str(path),
        '--connection-files',str(MODEL/'movements.con.xml'),'--tls.rebuild','true',
        '--output-file',str(MODEL/'connected.net.xml'),'--output.street-names','true'], 'connections')
    root=ET.parse(MODEL/'connected.net.xml').getroot()
    arms={eid:arm for d in (close_in,close_out) for arm,eid in d.items()}
    controlled={int(c.get('linkIndex')):c for c in root.findall('connection') if c.get('tl')=='TCS379'}
    # Crossing link indices are stored on crossing edges, not necessarily connections.
    cross_indices={}
    crossing_arms={}
    for e in root.findall('edge'):
        if e.get('function')=='crossing' and e.get('id').startswith(':TCS379'):
            arm_set={arms[x] for x in e.get('crossingEdges').split()}
            assert len(arm_set)==1
            arm=arm_set.pop()
            crossing_arms[e.get('id')]=arm
    for c in root.findall('connection'):
        if c.get('tl')=='TCS379' and c.get('to') in crossing_arms:
            cross_indices[int(c.get('linkIndex'))]=crossing_arms[c.get('to')]
    logic=next(t for t in root.findall('tlLogic') if t.get('id')=='TCS379')
    size=len(logic.find('phase').get('state'))
    # Each controlled connection (including pedestrian links) must be classified.
    for i,c in controlled.items():
        if c.get('from') in crossing_arms:
            cross_indices[i]=crossing_arms[c.get('from')]
        if c.get('to') in crossing_arms:
            cross_indices[i]=crossing_arms[c.get('to')]
    for p in list(logic):
        logic.remove(p)
    logic.set('programID','PM_geometry_revision')
    stages=[(7,'advance'),(3,'advance_y'),(1,'red'),(31,'ew_walk'),(22,'ew_clear'),(4,'ew_y'),(3,'red'),(8,'ns_walk'),(34,'ns_clear'),(4,'ns_y'),(3,'red')]
    assert sum(d for d,_ in stages)==120
    for duration,mode in stages:
        state=['r']*size
        for i,c in controlled.items():
            if i in cross_indices:
                arm=cross_indices[i]
                if (mode=='ew_walk' and arm in 'ns') or (mode=='ns_walk' and arm in 'ew'):
                    state[i]='G'
                continue
            arm=arms.get(c.get('from'))
            if arm is None:
                continue
            ew=arm in 'ew'
            direction=c.get('dir')
            if mode.startswith('advance') and ew and direction=='l':
                state[i]='y' if mode.endswith('_y') else 'G'
            elif ((mode.startswith('ew_') and ew) or (mode.startswith('ns_') and not ew)):
                state[i]='y' if mode.endswith('_y') else ('G' if direction=='s' else 'g')
        ET.SubElement(logic,'phase',duration=str(duration),state=''.join(state),name=mode)
    xml(root,path)
    final=sumolib.net.readNet(str(path),withInternal=True,withPrograms=True)
    def pavement(path_edges):
        return unary_union([LineString(lane.getShape()).buffer(lane.getWidth()/2,cap_style=2)
            for old_edge in path_edges for lane in final.getEdge(old_edge.getID()).getLanes()
            if lane.allows('passenger')])
    westbound,eastbound=pavement(incoming['e']),pavement(outgoing['e'])
    overlap=westbound.intersection(eastbound).area
    median_gap=westbound.distance(eastbound)
    def node_ids(path_edges):
        return {node.getID() for old_edge in path_edges for node in
            (final.getEdge(old_edge.getID()).getFromNode(),final.getEdge(old_edge.getID()).getToNode())}
    assert overlap<0.01 and median_gap>1.0, 'Eastern carriageways overlap or lose their median.'
    assert node_ids(incoming['e']) & node_ids(outgoing['e'])=={'TCS379'}, 'Spurious east-arm junction joins opposing carriageways.'
    # Reuse the exact previous dev arrival schedule; map the named approaches to
    # shortest valid paths in the revised network, and let SUMO choose a lane.
    original=ET.parse(ROOT/'results/baseline_dev/seed_11/routes.rou.xml').getroot()
    routes=ET.Element('routes')
    for t in original.findall('vType'):
        routes.append(t)
    route_cache={}
    for vehicle in original.findall('vehicle'):
        before=vehicle.find('route').get('edges').split()
        a,b=before[0][0],before[-1][0]
        key=(a,b)
        if key not in route_cache:
            begin=final.getEdge(incoming[a][0].getID())
            end=final.getEdge(outgoing[b][-1].getID())
            found,_=final.getShortestPath(begin,end,vClass='passenger')
            if found is None:
                raise ValueError(f'No path for observed movement {key}')
            assert any(e.getToNode().getID()=='TCS379' for e in found)
            route_cache[key]=' '.join(e.getID() for e in found)
        attrs=dict(vehicle.attrib)
        attrs['departLane']='best'
        v=ET.SubElement(routes,'vehicle',attrs)
        ET.SubElement(v,'route',edges=route_cache[key])
    additional=ET.Element('additional')
    # Red curb surfacing is a visual cue only. Legal/time-dependent transit
    # restrictions are not imposed without a verified operating rule.
    highlight_count=0
    for e in final.getEdges():
        if e.getName()!='Eglinton Avenue East':
            continue
        lanes=[lane for lane in e.getLanes() if lane.allows('passenger')]
        if not lanes:
            continue
        lane=min(lanes,key=lambda lane:lane.getIndex())
        poly=LineString(lane.getShape()).buffer(lane.getWidth()*.43,cap_style=2,join_style=2)
        if not poly.is_empty:
            ET.SubElement(additional,'poly',id=f'bus_curb_{highlight_count}',type='transit_curb_visual',
                color='0.65,0.08,0.12,0.65',fill='true',layer='0.1',
                shape=' '.join(f'{x:.2f},{y:.2f}' for x,y in poly.exterior.coords))
            highlight_count+=1
    xml(additional,MODEL/'visuals.add.xml')
    gui=ET.Element('viewsettings')
    ET.SubElement(gui,'scheme',name='real world')
    j=final.getNode('TCS379')
    ET.SubElement(gui,'viewport',zoom='300',x=str(j.getCoord()[0]),y=str(j.getCoord()[1]))
    xml(gui,MODEL/'view.xml')
    cfg=ET.Element('configuration')
    inp=ET.SubElement(cfg,'input')
    for name,value in [('net-file','models/eglinton_danforth/intersection.net.xml'),('route-files','models/eglinton_danforth/traffic.rou.xml'),('additional-files','models/eglinton_danforth/visuals.add.xml')]:
        ET.SubElement(inp,name,value=value)
    time=ET.SubElement(cfg,'time');ET.SubElement(time,'end',value='7200')
    processing=ET.SubElement(cfg,'processing');ET.SubElement(processing,'time-to-teleport',value='-1')
    rand=ET.SubElement(cfg,'random_number');ET.SubElement(rand,'seed',value='11')
    gui_only=ET.SubElement(cfg,'gui_only')
    ET.SubElement(gui_only,'gui-settings-file',value='models/eglinton_danforth/view.xml')
    ET.SubElement(gui_only,'delay',value='100')
    xml(cfg,ROOT/'Eglinton_Danforth.sumocfg')
    metadata={'status':'Georeferenced geometry revision, not calibrated or historically validated for 2024',
        'source_url':'https://api.openstreetmap.org/api/0.6/map?bbox=-79.250,43.734,-79.242,43.741',
        'source_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
        'attribution':'Map data (c) OpenStreetMap contributors, ODbL 1.0',
        'junction':'TCS379','incoming':{a:[e.getID() for e in es] for a,es in incoming.items()},
        'outgoing':{a:[e.getID() for e in es] for a,es in outgoing.items()},
        'vehicle_lanes_at_stopline':{a:sum(l.allows('passenger') for l in final.getEdge(eid).getLanes()) for a,eid in close_in.items()},
        'crossing_segments':crossing_arms,'crossing_signal_indices':cross_indices,
        'vehicle_count':len(original.findall('vehicle')),'pedestrians':{'count':518,'source':'Observed dev crossing-leg totals; modeled within-interval arrivals, direction split, and walking speed'},
        'transit_curbs':'red visual overlays only; access rules remain unvalidated',
        'assumptions':['SUMO-generated lane widths and corner radii','guessed 2 m sidewalks','guessed crossing geometry on source road alignment','static simplified PM plan','no transit stop schedule'],
        'east_median':'Independent EB/WB nodes, source-aligned spine, 2.4 m modeled median gap; width not surveyed',
        'east_separation_check':{'overlap_area_m2':overlap,'minimum_vehicle_surface_gap_m':median_gap,'only_shared_node':'TCS379'},
        'route_pairs':{'_'.join(k):v for k,v in route_cache.items()}}
    (MODEL/'provenance.json').write_text(json.dumps(metadata,indent=2))
    from revised_demand import write_routes
    write_routes(11,MODEL/'traffic.rou.xml')
    metadata['pedestrians']={'count':518,'source':'Observed dev count totals by crossing leg; uniform arrival times and balanced directions are modeled.'}
    (MODEL/'provenance.json').write_text(json.dumps(metadata,indent=2))
    print(json.dumps(metadata,indent=2))


if __name__=='__main__':
    main()
