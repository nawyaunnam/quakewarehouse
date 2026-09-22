import unittest
from engine import Warehouse

class WarehouseTests(unittest.TestCase):
    def setUp(self):
        self.w=Warehouse(':memory:')
        self.row={'id':'a','updated':2,'time':1,'region':'us','magnitude':2.5,'depth':10}
    def tearDown(self): self.w.close()
    def test_batch_replay(self):
        self.w.ingest('b',[self.row])
        self.assertTrue(self.w.ingest('b',[self.row])['replayed'])
        self.assertEqual(self.w.analytics()[0]['events'],1)
    def test_revision_order(self):
        self.w.ingest('b',[self.row])
        self.w.ingest('c',[dict(self.row,updated=4,magnitude=3)])
        self.w.ingest('d',[dict(self.row,updated=3,magnitude=2)])
        self.assertEqual(self.w.analytics()[0]['max_magnitude'],3)
    def test_quarantine(self):
        result=self.w.ingest('b',[self.row,dict(self.row,id='bad',magnitude=None)])
        self.assertEqual(result['rejected'],1)
        self.assertEqual(self.w.db.execute('SELECT COUNT(*) FROM quarantine').fetchone()[0],1)
    def test_conflicting_batch_rolls_back(self):
        self.w.ingest('b',[self.row])
        with self.assertRaises(ValueError): self.w.ingest('b',[dict(self.row,magnitude=4)])
        self.assertEqual(self.w.analytics()[0]['max_magnitude'],2.5)
    def test_invalid_numeric(self):
        result=self.w.ingest('b',[dict(self.row,magnitude=float('nan')),dict(self.row,time=5)])
        self.assertEqual(result['rejected'],2)
    def test_cross_batch_dedup(self):
        self.w.ingest('a',[self.row]); self.w.ingest('b',[self.row])
        self.assertEqual(self.w.analytics()[0]['events'],1)
