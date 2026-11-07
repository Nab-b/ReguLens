import sys, os, unittest, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import sinkron

CONTOH = '''<div><a href="https://peraturan.bpk.go.id/Details/350939/peraturan-bpom-no-5-tahun-2026">Peraturan Badan Pengawas Obat dan Makanan Nomor 5 Tahun 2026</a>
<a href="https://peraturan.bpk.go.id/Details/350939/peraturan-bpom-no-5-tahun-2026">Pengawasan Pengelolaan Obat dan Bahan Obat di Fasilitas Lain</a>
Status Peraturan Mencabut 1. <a href="https://peraturan.bpk.go.id/Details/223930/x">Peraturan BPOM No. 24 Tahun 2021</a> tentang Pengawasan
Download file: <a href="https://peraturan.bpk.go.id/Download/414694/a.pdf">a.pdf</a>
CATATAN: Peraturan ini mulai berlaku pada tanggal 06 April 2026.</div>
<div><a href="https://peraturan.bpk.go.id/Details/343812/y">Peraturan Badan Pengawas Obat dan Makanan Nomor 32 Tahun 2025</a>
<a href="https://peraturan.bpk.go.id/Details/343812/y">Penyelenggaraan Pelatihan Bidang Keamanan Pangan</a>
Status Peraturan Mencabut <a href="https://peraturan.bpk.go.id/Details/181760/z">Peraturan BPOM No. 16 Tahun 2021</a></div>
<div><a href="https://peraturan.bpk.go.id/Details/1/q">Peraturan Badan Pengawas Obat dan Makanan Nomor 30 Tahun 2025</a>
<a href="https://peraturan.bpk.go.id/Details/1/q">Perubahan atas PerBPOM 14/2024 tentang Pengawasan Obat dan Makanan Daring</a>
Status Peraturan Mengubah <a href="https://peraturan.bpk.go.id/Details/297143/w">Peraturan BPOM No. 14 Tahun 2024</a></div>'''

class TestSinkron(unittest.TestCase):
    def test_parse(self):
        h = sinkron.parse_bpk(CONTOH, "uji")
        self.assertEqual(len(h), 3)
        self.assertEqual(h[0]["mencabut"], ["Peraturan BPOM No. 24 Tahun 2021"])
        self.assertEqual(h[0]["tgl_berlaku"], "2026-04-06")
        self.assertTrue(h[0]["pdf"].endswith("a.pdf"))
        self.assertEqual(h[2]["mengubah"], ["Peraturan BPOM No. 14 Tahun 2024"])
    def test_kunci(self):
        self.assertEqual(sinkron.kunci("Peraturan Badan Pengawas Obat dan Makanan Nomor 5 Tahun 2026")[0], "PerBPOM|5|2026")
        self.assertEqual(sinkron.kunci("Peraturan BPOM No. 24 Tahun 2021")[0], "PerBPOM|24|2021")
    def test_alur_penuh(self):
        d = tempfile.mkdtemp()
        sinkron.KORPUS, sinkron.PEMB, sinkron.SUMBER = [os.path.join(d, n) for n in ("k.json", "p.json", "s.json")]
        json.dump({"regulasi": [{"id": "pb24-21", "k": "PerBPOM 24/2021", "st": "Berlaku", "pr": [], "ak": [], "r": "", "t": "", "j": "", "ins": "", "tg": "", "ob": "U"},
                                {"id": "pb14-24", "k": "PerBPOM 14/2024", "st": "Berlaku", "pr": [], "ak": [], "r": "", "t": "", "j": "", "ins": "", "tg": "", "ob": "U"}]}, open(sinkron.KORPUS, "w"))
        json.dump({"kata_kunci": ["obat"], "sumber": [{"nama": "uji", "tipe": "bpk", "url": "http://x", "halaman": 1}]}, open(sinkron.SUMBER, "w"))
        o = sinkron.jalankan(lambda url, params=None: CONTOH)
        self.assertEqual([k["k"] for k in o["kandidat"]], ["PerBPOM 30/2025", "PerBPOM 5/2026"])  # 32/2025 (pangan) tidak relevan
        dua = {(u["k"], u["ke"], u["oleh"]) for u in o["usulan"]}
        self.assertIn(("PerBPOM 24/2021", "Dicabut", "PerBPOM 5/2026"), dua)
        self.assertIn(("PerBPOM 14/2024", "Diubah", "PerBPOM 30/2025"), dua)
        for u in list(o["usulan"]): sinkron.terima_usulan(u["id"])
        for k in list(o["kandidat"]): sinkron.terima_kandidat(k["id"])
        kor = json.load(open(sinkron.KORPUS))["regulasi"]
        st = {r["id"]: r for r in kor}
        self.assertEqual(st["pb24-21"]["st"], "Dicabut"); self.assertEqual(st["pb14-24"]["st"], "Diubah")
        self.assertEqual(len(kor), 4)
        o2 = sinkron.jalankan(lambda url, params=None: CONTOH)  # idempoten
        self.assertEqual(o2["kandidat"], [])

    def test_dasar_hukum_ikut_berubah(self):
        d = tempfile.mkdtemp()
        sinkron.KORPUS, sinkron.PEMB, sinkron.SUMBER = [os.path.join(d, n) for n in ("k.json", "p.json", "s.json")]
        reg = lambda i, k, st, pr, ak: {"id": i, "k": k, "st": st, "pr": pr, "ak": ak, "r": "", "t": "", "j": "", "ins": "", "tg": "", "ob": "U"}
        json.dump({"regulasi": [reg("pb24-21", "PerBPOM 24/2021", "Berlaku", ["obat"], ["distribusi"])],
                   "fasilitas": [{"n": "Apotek", "pr": ["obat"], "ak": ["distribusi"], "src": ["pb24-21"], "dok": []},
                                 {"n": "Industri Kosmetik", "pr": ["kosmetik"], "ak": ["produksi"], "src": [], "dok": []}],
                   "produk": [{"n": "Obat", "pr": "obat", "ak": ["registrasi"], "src": [], "dok": []}],
                   "peta": {"distribusi": [{"t": "x", "s": ["pb24-21"]}]}, "benturan": []}, open(sinkron.KORPUS, "w"))
        json.dump({"kata_kunci": ["obat"], "sumber": [{"nama": "uji", "tipe": "bpk", "url": "http://x", "halaman": 1}]}, open(sinkron.SUMBER, "w"))
        o = sinkron.jalankan(lambda url, params=None: CONTOH)
        for k in list(o["kandidat"]): sinkron.terima_kandidat(k["id"])      # PerBPOM 5/2026 masuk korpus
        kor = json.load(open(sinkron.KORPUS)); pe = json.load(open(sinkron.PEMB))
        baru = [t for t in pe["tautan"] if t["k"] == "PerBPOM 5/2026"]
        self.assertTrue(any(t["n"] == "Apotek" for t in baru))               # cocok produk dan aktivitas
        self.assertFalse(any(t["n"] == "Industri Kosmetik" for t in baru))   # tidak beririsan
        for u in list(pe["usulan"]): sinkron.terima_usulan(u["id"])
        kor = json.load(open(sinkron.KORPUS)); apotek = kor["fasilitas"][0]
        self.assertTrue(any(r["k"] == "PerBPOM 5/2026" and r["id"] in apotek["src"] for r in kor["regulasi"]))
        self.assertTrue(apotek.get("tinjau"))                                # ditandai perlu ditinjau
        self.assertTrue(any(r["id"] in kor["peta"]["distribusi"][0]["s"] for r in kor["regulasi"] if r["k"] == "PerBPOM 5/2026"))
        sinkron.tandai_tinjau("fasilitas", "Apotek")
        self.assertFalse(json.load(open(sinkron.KORPUS))["fasilitas"][0].get("tinjau"))
        tid = baru[0]["id"]
        self.assertTrue(sinkron.terima_tautan(tid))
        self.assertFalse(any(x["id"] == tid for x in json.load(open(sinkron.PEMB))["tautan"]))

if __name__ == "__main__": unittest.main()
