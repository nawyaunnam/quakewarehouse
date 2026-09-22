from feeds import fetch,run
from engine import Warehouse,normalize_geojson
import hashlib
import json

def acquire():
    return {'sources':[fetch('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson')]}


def analyze(snapshot):
    data=snapshot['sources'][0]['payload']
    rows=list(normalize_geojson(data))
    batch=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
    warehouse=Warehouse('live-warehouse.db')
    try:
        load=warehouse.ingest(batch,rows)
        return {'project':'QuakeWarehouse','source_observations':len(rows),'accepted':load['accepted'],
                'quarantined':load['rejected'],'replayed':load['replayed'],
                'stored_events':warehouse.db.execute('SELECT COUNT(*) FROM earthquakes').fetchone()[0],
                'source_generated_ms':data['metadata']['generated'],'regions':warehouse.analytics()}
    finally:warehouse.close()


if __name__=='__main__': run(acquire,analyze)
