import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from korpus import muat, cari

class TestKorpus(unittest.TestCase):
    def setUp(self):
        self.d = muat(); self.ids = {r["id"] for r in self.d["regulasi"]}
    def test_id_unik(self): self.assertEqual(len(self.ids), len(self.d["regulasi"]))
    def test_sumber_valid(self):
        for grup in (self.d["fasilitas"], self.d["produk"]):
            for x in grup:
                for s in x["src"]: self.assertIn(s, self.ids, s)
        for langkah in self.d["peta"].values():
            for l in langkah:
                for s in l["s"]: self.assertIn(s, self.ids, s)
        for b in self.d["benturan"]:
            for s in b["s"]: self.assertIn(s, self.ids, s)
    def test_status_valid(self):
        for r in self.d["regulasi"]: self.assertIn(r["st"], {"Berlaku","Diubah","Dicabut","Draft","Cek"})
    def test_dicabut_punya_pengganti(self):
        for r in self.d["regulasi"]:
            if r["st"] == "Dicabut": self.assertTrue(r.get("dg"), r["k"])
    def test_perubahan_punya_summary(self):
        for r in self.d['regulasi']:
            if r['st'] in ('Diubah','Dicabut'): self.assertTrue(r.get('sp'), r['k'])
    def test_cari(self): self.assertTrue(cari("CPOB"))
if __name__ == "__main__": unittest.main()
