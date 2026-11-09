"""Extract TCS 379 and freeze a chronological split before controller experiments."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    out = ROOT / 'data'
    out.mkdir(exist_ok=True)
    manifest_path = out / 'split_manifest.json'
    if manifest_path.exists():
        raise SystemExit('Split already frozen; refusing to overwrite it.')
    rows = []
    with args.source.open(newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r['px'] == '379' and r['count_date'] in ('2024-06-19', '2024-11-02'):
                rows.append(r)
    rows.sort(key=lambda r: (r['start_time'], r['_id']))
    assert len(rows) == 112
    fields = list(rows[0])
    vehicles = [k for k in fields if any('_'+c+'_' in k for c in ('cars', 'truck', 'bus'))]
    pedestrians = [k for k in fields if k.endswith('_peds')]
    assert len(vehicles) == 36 and len(pedestrians) == 4
    for r in rows:
        for k in vehicles + pedestrians:
            assert r[k] != '' and int(r[k]) >= 0
    groups = {
        'train': [r for r in rows if r['count_date']=='2024-06-19' and '15:00' <= r['start_time'][11:16] < '17:00'],
        'dev': [r for r in rows if r['count_date']=='2024-06-19' and '17:00' <= r['start_time'][11:16] < '18:00'],
        'test_primary': [r for r in rows if r['count_date']=='2024-11-02' and '15:00' <= r['start_time'][11:16] < '18:00'],
        'test_secondary': [r for r in rows if r['count_date']=='2024-06-19' and '07:00' <= r['start_time'][11:16] < '10:00'],
    }
    ids = [r['_id'] for rr in groups.values() for r in rr]
    assert len(ids) == len(set(ids))
    summaries = {}
    for name, rr in groups.items():
        assert len(rr) == (8 if name=='train' else 4 if name=='dev' else 12)
        target = out / f'{name}.csv'
        with target.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rr)
        summaries[name] = {
            'row_ids': [r['_id'] for r in rr], 'intervals': len(rr),
            'vehicles': sum(int(r[k]) for r in rr for k in vehicles),
            'pedestrians': sum(int(r[k]) for r in rr for k in pedestrians),
            'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        }
    manifest = {
        'source_name': args.source.name,
        'source_sha256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
        'site': 'TCS 379, Danforth Rd / Eglinton Ave E',
        'revision': 'Reserve 17:00-18:00 of the proposal training period for development; train on 15:00-17:00.',
        'policy': 'Choose configurations on dev; no test simulation until final model freeze. Separate episodes reset queues; no shared trips across boundaries.',
        'seeds': [11, 22, 33, 44, 55], 'splits': summaries,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
