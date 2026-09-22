"""Transactional incremental loads with revision ordering and quarantine."""
import hashlib
import json
import math
import sqlite3

class Warehouse:
    def __init__(self,path):
        self.db=sqlite3.connect(path,isolation_level=None,timeout=10)
        self.db.row_factory=sqlite3.Row
        self.db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY,digest TEXT,accepted INTEGER,rejected INTEGER);
            CREATE TABLE IF NOT EXISTS earthquakes(id TEXT PRIMARY KEY,updated REAL,event_time REAL,
                region TEXT,magnitude REAL,depth REAL,batch_id TEXT);
            CREATE INDEX IF NOT EXISTS event_time_idx ON earthquakes(event_time);
            CREATE TABLE IF NOT EXISTS quarantine(batch_id TEXT,row_number INTEGER,payload TEXT,error TEXT,
                PRIMARY KEY(batch_id,row_number));
        """)
    def close(self): self.db.close()
    @staticmethod
    def validate(row):
        if not isinstance(row,dict): raise ValueError('record must be an object')
        if not isinstance(row.get('id'),str) or not row['id']: raise ValueError('event id required')
        if not isinstance(row.get('region'),str) or not row['region']: raise ValueError('region required')
        for key in ['time','updated','magnitude','depth']:
            value=row.get(key)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
                raise ValueError(f'{key} must be finite numeric')
        if row['updated']<row['time']: raise ValueError('revision precedes event')
        if not -5<=row['magnitude']<=15: raise ValueError('magnitude outside contract')
        if not -20<=row['depth']<=1000: raise ValueError('depth outside contract')
    def ingest(self,batch_id,rows):
        if not isinstance(batch_id,str) or not batch_id: raise ValueError('batch id required')
        rows=list(rows)
        # Nonfinite JSON values are retained in quarantine as diagnostic source text.
        body=json.dumps(rows,sort_keys=True)
        digest=hashlib.sha256(body.encode()).hexdigest()
        self.db.execute('BEGIN IMMEDIATE')
        try:
            old=self.db.execute('SELECT * FROM batches WHERE id=?',(batch_id,)).fetchone()
            if old:
                if old['digest']!=digest: raise ValueError('batch id reused with different content')
                self.db.execute('COMMIT')
                return {'accepted':old['accepted'],'rejected':old['rejected'],'replayed':True}
            accepted=rejected=0
            for i,row in enumerate(rows):
                try: self.validate(row)
                except ValueError as error:
                    self.db.execute('INSERT INTO quarantine VALUES(?,?,?,?)',(batch_id,i,json.dumps(row),str(error)))
                    rejected+=1
                    continue
                self.db.execute("""INSERT INTO earthquakes VALUES(?,?,?,?,?,?,?)
                    ON CONFLICT(id) DO UPDATE SET updated=excluded.updated,event_time=excluded.event_time,
                    region=excluded.region,magnitude=excluded.magnitude,depth=excluded.depth,batch_id=excluded.batch_id
                    WHERE excluded.updated>earthquakes.updated""",
                    (row['id'],row['updated'],row['time'],row['region'],row['magnitude'],row['depth'],batch_id))
                accepted+=1
            self.db.execute('INSERT INTO batches VALUES(?,?,?,?)',(batch_id,digest,accepted,rejected))
            self.db.execute('COMMIT')
            return {'accepted':accepted,'rejected':rejected,'replayed':False}
        except Exception:
            self.db.execute('ROLLBACK')
            raise
    def analytics(self):
        return [dict(row) for row in self.db.execute("""SELECT region,COUNT(*) AS events,
            ROUND(AVG(magnitude),3) AS average_magnitude,MAX(magnitude) AS max_magnitude,
            ROUND(AVG(depth),3) AS average_depth_km FROM earthquakes GROUP BY region ORDER BY events DESC,region""")]

def normalize_geojson(data):
    for feature in data['features']:
        p=feature.get('properties') or {}
        coordinates=(feature.get('geometry') or {}).get('coordinates') or []
        yield {'id':feature.get('id'),'updated':p.get('updated'),'time':p.get('time'),
               'region':p.get('net'),'magnitude':p.get('mag'),
               'depth':coordinates[2] if len(coordinates)>2 else None}
