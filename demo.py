import json
import tempfile
from pathlib import Path
from engine import Warehouse

rows=[{'id':'a','updated':100,'time':90,'region':'us','magnitude':3.1,'depth':8},
      {'id':'b','updated':110,'time':95,'region':'ci','magnitude':2.1,'depth':4},
      {'id':'bad','updated':110,'time':95,'region':'ci','magnitude':None,'depth':4}]
with tempfile.TemporaryDirectory() as d:
    warehouse=Warehouse(Path(d)/'warehouse.db')
    first=warehouse.ingest('batch-1',rows)
    retry=warehouse.ingest('batch-1',rows)
    warehouse.ingest('revision',[dict(rows[0],updated=120,magnitude=3.3)])
    print(json.dumps({'first':first,'retry':retry,'analytics':warehouse.analytics()},indent=2))
    warehouse.close()
