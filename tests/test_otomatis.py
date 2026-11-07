import sys, os, unittest, tempfile, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import sinkron, dokumen
sys.path.insert(0, os.path.dirname(__file__))
from test_sinkron import CONTOH

def reg(i, k, st, pr, ak): return {"id": i, "k": k, "st": st, "pr": pr, "ak": ak, "r": "", "t": "", "j": "", "ins": "", "tg": "", "ob": "U"}

class TestOtomatis(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        sinkron.KORPUS, sinkron.PEMB, sinkron.SUMBER = [os.path.join(self.d, n) for n in ("k.json", "p.json", "s.json")]
        dokumen.DIR, dokumen.IDX, dokumen.TXT = os.path.join(self.d, "dok"), os.path.join(self.d, "dokumen.json"), os.path.join(self.d, "teks")
        json.dump({"regulasi": [reg("pb24-21", "PerBPOM 24/2021", "Berlaku", ["obat"], ["distribusi"])],
                   "fasilitas": [{"n": "Apotek", "pr": ["obat"], "ak": ["distribusi"], "src": ["pb24-21"], "dok": []},
                                 {"n": "Industri Kosmetik", "pr": ["kosmetik"], "ak": ["produksi"], "src": [], "dok": []}],
                   "produk": [{"n": "Kosmetik", "pr": "kosmetik", "ak": ["registrasi", "label"], "src": [], "dok": []}],
                   "peta": {}, "benturan": []}, open(sinkron.KORPUS, "w"))
        json.dump({"kata_kunci": ["obat"], "sumber": [{"nama": "uji", "tipe": "bpk", "url": "http://x", "halaman": 1}]}, open(sinkron.SUMBER, "w"))
    def korpus(self): return json.load(open(sinkron.KORPUS))
    def test_tambah_otomatis_tertaut_dan_snapshot(self):
        r = sinkron.tambah_regulasi({"k": "PerBPOM 1/2027", "t": "Notifikasi kosmetik baru", "pr": ["kosmetik"], "ak": ["registrasi"], "pdf": "dokumen/Umum/x.pdf"})
        self.assertTrue(r["ok"]); self.assertEqual(r["tautan"], 1)
        k = self.korpus()
        prod = k["produk"][0]; self.assertIn("perbpom-1-2027", prod["src"]); self.assertTrue(prod["tinjau"])
        self.assertNotIn("perbpom-1-2027", k["fasilitas"][1]["src"])         # tak beririsan aktivitas
        self.assertFalse(sinkron.tambah_regulasi({"k": "PerBPOM 1/2027", "t": "dobel"})["ok"])
        js = open(os.path.join(self.d, "data.js"), encoding="utf-8").read()   # data.js ikut diperbarui otomatis
        self.assertTrue(js.startswith("window.REGULENS_DATA=")); self.assertIn("PerBPOM 1/2027", js)
        self.assertFalse(sinkron.tambah_regulasi({"k": "(isi nama)", "t": "x"})["ok"])
    def test_sinkron_terima_otomatis(self):
        json.dump({"terima_otomatis": True, "tautan_otomatis": True}, open(os.path.join(self.d, "pengaturan.json"), "w"))
        o = sinkron.jalankan(lambda url, params=None: CONTOH)
        self.assertEqual(o["kandidat"], []); self.assertEqual(o["usulan"], []); self.assertTrue(o["diterapkan"]["kandidat"] >= 1)
        k = self.korpus(); st = {r["id"]: r for r in k["regulasi"]}
        self.assertEqual(st["pb24-21"]["st"], "Dicabut")
        self.assertTrue(any(r.get("otomatis") for r in k["regulasi"]))
        self.assertTrue(any(x["n"] == "Apotek" and "perbpom-5-2026" in x["src"] for x in k["fasilitas"]))
        lg = json.load(open(os.path.join(self.d, "log_sinkron.json"))); self.assertTrue(any(l["aksi"] == "status berubah" for l in lg))
        self.assertIn("PerBPOM 5/2026", open(os.path.join(self.d, "data.js"), encoding="utf-8").read())
    def test_sinkron_default_tetap_manual(self):
        o = sinkron.jalankan(lambda url, params=None: CONTOH); self.assertTrue(o["kandidat"]); self.assertEqual(self.korpus()["regulasi"][0]["st"], "Berlaku")
    def test_pdf_peraturan_otomatis_jadi_entri(self):
        txt = ("PERATURAN BADAN PENGAWAS OBAT DAN MAKANAN NOMOR 77 TAHUN 2030\nTENTANG\nPENGAWASAN KOSMETIK TERBARU\n\nDENGAN RAHMAT TUHAN YANG MAHA ESA\n").encode()
        d = dokumen.unggah("pbpom-77-2030.txt", "Peraturan", txt)
        self.assertTrue(d["reg_baru"]); k = self.korpus(); r = [x for x in k["regulasi"] if x["k"] == "PerBPOM 77/2030"][0]
        self.assertTrue(r["otomatis"]); self.assertEqual(r["pdf"], d["berkas"]); self.assertIn("kosmetik", r["pr"]); self.assertIn("Pengawasan Kosmetik", r["t"])
        d2 = dokumen.unggah("salinan.txt", "Peraturan", txt)               # nomor sama -> dilampirkan ke entri yang ada
        self.assertEqual(d2["reg_id"], r["id"]); self.assertFalse(d2["reg_baru"])
        memo = dokumen.unggah("memo.txt", "Umum", b"Memo internal tentang rencana. Merujuk PerBPOM 77/2030 untuk kosmetik.")
        self.assertIsNone(memo["reg_id"])                                  # memo biasa tidak dianggap peraturan
        dokumen.hapus(d["id"]); self.assertNotIn("pdf", [x for x in self.korpus()["regulasi"] if x["k"] == "PerBPOM 77/2030"][0])
    def test_relevansi_tidak_memuat_organisasi(self):
        kk = ["obat", "kosmetik"]
        self.assertFalse(sinkron.relevan_teks("Perubahan Kedua atas PerBPOM 19/2023 tentang Organisasi dan Tata Kerja Unit Pelaksana Teknis pada Badan Pengawas Obat dan Makanan", kk))
        self.assertFalse(sinkron.relevan_teks("Pengelolaan Pegawai pada Badan Pengawas Obat dan Makanan", kk))   # 'obat' hanya dari nama instansi
        self.assertTrue(sinkron.relevan_teks("Penarikan dan Pemusnahan Obat", kk))
    def test_hapus_regulasi_dan_tautan(self):
        r = sinkron.tambah_regulasi({"k": "PerBPOM 5/2031", "t": "Distribusi obat uji", "pr": ["obat"], "ak": ["distribusi"]})
        k = self.korpus(); self.assertTrue(k["fasilitas"][0]["tinjau"]); self.assertTrue(k["regulasi"][-1]["pengguna"])
        self.assertFalse(sinkron.hapus_regulasi("pb24-21")["ok"])                       # peraturan bawaan tidak bisa dihapus
        self.assertTrue(sinkron.hapus_regulasi(r["id"])["ok"]); k = self.korpus()
        self.assertNotIn(r["id"], k["fasilitas"][0]["src"]); self.assertFalse(k["fasilitas"][0].get("tinjau"))
        self.assertIn(r["id"], json.load(open(sinkron.PEMB))["abaikan"])
    def test_migrasi_pengaturan_dan_pembersihan(self):
        r = sinkron.tambah_regulasi({"k": "PerBPOM 9/2031", "t": "Organisasi dan Tata Kerja Unit", "otomatis": True, "pr": ["obat"], "ak": ["distribusi"]})
        sinkron.tambah_regulasi({"k": "PerBPOM 8/2031", "t": "Penarikan obat uji", "otomatis": True, "disetujui": True, "pr": ["obat"], "ak": ["distribusi"]})
        json.dump({"terima_otomatis": True}, open(os.path.join(self.d, "pengaturan.json"), "w"))
        self.assertEqual(sinkron.migrasi_pengaturan(), 1)
        ks = [x["k"] for x in self.korpus()["regulasi"]]; self.assertNotIn("PerBPOM 9/2031", ks); self.assertIn("PerBPOM 8/2031", ks)   # yang disetujui manual aman
        self.assertFalse(sinkron.pengaturan()["terima_otomatis"]); self.assertEqual(sinkron.migrasi_pengaturan(), 0)
    def test_terima_manual_ditandai_disetujui(self):
        o = sinkron.jalankan(lambda url, params=None: CONTOH)
        sinkron.terima_kandidat(o["kandidat"][0]["id"]); self.assertTrue([x for x in self.korpus()["regulasi"] if x.get("otomatis")][0]["disetujui"])
if __name__ == "__main__": unittest.main()
