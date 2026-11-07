import sys, os, unittest, tempfile, zipfile, io, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import dokumen, sinkron

class TestDokumen(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        dokumen.DIR, dokumen.IDX, dokumen.TXT = os.path.join(d, "dok"), os.path.join(d, "dokumen.json"), os.path.join(d, "teks")
        sinkron.KORPUS = os.path.join(d, "k.json")
        json.dump({"regulasi": [{"id": "pb7-24", "k": "PerBPOM 7/2024", "st": "Berlaku"}, {"id": "pb34-18", "k": "PerBPOM 34/2018", "st": "Dicabut"}]}, open(sinkron.KORPUS, "w"))
    def test_txt_rujukan_cari(self):
        d = dokumen.unggah("kasus.txt", "Kasus A", "Industri menerapkan Peraturan BPOM Nomor 7 Tahun 2024 dan PerBPOM 34/2018 serta PP 99/2030 untuk CPOB.".encode())
        self.assertEqual(sorted(d["rujukan"]), ["pb34-18", "pb7-24"]); self.assertEqual(d["tak_dikenal"], ["PP 99/2030"])
        self.assertTrue(os.path.exists(os.path.join(dokumen.DIR, "Kasus A", "kasus.txt")))
        h = dokumen.cari("cpob industri"); self.assertEqual(len(h), 1); self.assertIn("CPOB", h[0]["kutipan"])
    def test_docx(self):
        b = io.BytesIO(); z = zipfile.ZipFile(b, "w"); z.writestr("word/document.xml", "<w:document><w:p><w:t>Sertifikat CDOB PBF</w:t></w:p></w:document>"); z.close()
        d = dokumen.unggah("a.docx", "Umum", b.getvalue()); self.assertTrue(d["teks"]); self.assertEqual(len(dokumen.cari("cdob")), 1)
    def test_aman_dan_tolak(self):
        d = dokumen.unggah("../../x.txt", "../../etc", b"halo")
        self.assertTrue(os.path.abspath(os.path.join(dokumen.DIR, *d["folder"].split("/"), d["nama"])).startswith(os.path.abspath(dokumen.DIR)))
        with self.assertRaises(ValueError): dokumen.unggah("virus.exe", "Umum", b"x")
    def test_hapus_ubah_duplikat(self):
        a = dokumen.unggah("a.txt", "F", b"satu"); b = dokumen.unggah("a.txt", "F", b"dua")
        self.assertNotEqual(a["nama"], b["nama"])
        self.assertTrue(dokumen.ubah(a["id"], "pb7-24")); self.assertEqual(dokumen.muat()["dokumen"][0]["reg_id"], "pb7-24")
        self.assertTrue(dokumen.hapus(a["id"])); self.assertEqual(len(dokumen.daftar()["dokumen"]), 1)
    def test_cocok(self):
        dokumen.unggah("sertifikat.txt", "Umum", "Salinan sertifikat ISO 13485 pabrikan dan surat penunjukan dari pabrikan untuk distribusi.".encode())
        r = dokumen.cocok([{"key": "a", "teks": "Sertifikat ISO 13485/CPAKB pabrikan"}, {"key": "b", "teks": "Label dan petunjuk penggunaan berbahasa Indonesia"}])
        self.assertIn("a", r); self.assertNotIn("b", r)
if __name__ == "__main__": unittest.main()
