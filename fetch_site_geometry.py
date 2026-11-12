"""Download public City centreline features around TCS 379."""
import json
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'models'/'eglinton_danforth'/'source'
OUT.mkdir(parents=True,exist_ok=True)
url='https://gis.toronto.ca/arcgis/rest/services/cot_geospatial/MapServer/2/query'
params={'where':'1=1','geometry':'-79.251,43.733,-79.241,43.742',
        'geometryType':'esriGeometryEnvelope','inSR':'4326','spatialRel':'esriSpatialRelIntersects',
        'outFields':'*','outSR':'4326','f':'geojson'}
r=requests.get(url,params=params,timeout=60)
r.raise_for_status()
data=r.json()
if 'features' not in data:
    raise ValueError(data)
(OUT/'centreline.geojson').write_text(json.dumps(data,indent=2),encoding='utf-8')
(OUT/'request.json').write_text(json.dumps({'url':r.url,'source':'City of Toronto Centreline ArcGIS layer 2','features':len(data['features'])},indent=2))
print('Downloaded features:',len(data['features']))
for f in data['features']:
    p=f['properties']
    if any('eglin' in str(v).lower() or 'danforth' in str(v).lower() for v in p.values()):
        print(json.dumps(p))
