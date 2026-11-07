"""Menjalankan Regulens secara lokal dengan sinkronisasi: python app.py  (http://localhost:8765)"""
import http.server, socketserver, webbrowser, os, json, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
import sinkron, dokumen, snapshot, base64, urllib.parse, threading, time
PORT = int(os.environ.get("REGULENS_PORT", "8765"))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class H(http.server.SimpleHTTPRequestHandler):
    def _json(self, d, kode=200):
        b = json.dumps(d, ensure_ascii=False).encode("utf-8")
        self.send_response(kode); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/api/status": return self._json({"ok": True, "pengaturan": sinkron.pengaturan()})
        if u.path == "/api/dokumen": return self._json(dokumen.daftar())
        if u.path == "/api/dokumen/cari": return self._json({"hasil": dokumen.cari(urllib.parse.parse_qs(u.query).get("q", [""])[0])})
        return super().do_GET()
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try: body = json.loads(self.rfile.read(n) or b"{}")
        except Exception: body = {}
        p = self.path
        try:
            if p == "/api/sinkron":
                o = sinkron.jalankan()
                g = [s["nama"] for s in o["sumber"] if s["galat"]]
                return self._json({"pesan": f"{len(o['kandidat'])} peraturan baru, {len(o['usulan'])} usulan status." + (f" Sumber gagal dibaca: {', '.join(g)}." if g else "")})
            if p == "/api/terima":
                j = body.get("jenis")
                ok = sinkron.terima_kandidat(body.get("id")) if j == "kandidat" else sinkron.terima_tautan(body.get("id")) if j == "tautan" else sinkron.terima_usulan(body.get("id"))
                return self._json({"ok": ok})
            if p == "/api/dokumen/unggah":
                d = dokumen.unggah(body.get("nama"), body.get("folder"), base64.b64decode(body.get("b64", "")), body.get("reg_id"), body.get("pr"), body.get("ak"))
                return self._json({"ok": True, "dokumen": d})
            if p == "/api/korpus/tambah":
                hasil = [sinkron.tambah_regulasi(r) for r in body.get("regulasi", [])]
                return self._json({"hasil": hasil, "pesan": " ".join(h["pesan"] for h in hasil)})
            if p == "/api/korpus/hapus": return self._json(sinkron.hapus_regulasi(body.get("id")))
            if p == "/api/korpus/ditinjau": return self._json({"ok": sinkron.tandai_reg_ditinjau(body.get("id"))})
            if p == "/api/dokumen/cocok": return self._json({"cocok": dokumen.cocok(body.get("items", []))})
            if p == "/api/dokumen/hapus": return self._json({"ok": dokumen.hapus(body.get("id"))})
            if p == "/api/dokumen/ubah": return self._json({"ok": dokumen.ubah(body.get("id"), body.get("reg_id"), body.get("lepas", False))})
            if p == "/api/dokumen/folder": return self._json({"folder": dokumen.buat_folder(body.get("nama"))})
            if p == "/api/ekstrak":
                t = dokumen.ekstrak(body.get("nama", ""), base64.b64decode(body.get("b64", "")))
                return self._json({"teks": t})
            if p == "/api/tinjau": return self._json({"ok": sinkron.tandai_tinjau(body.get("jenis"), body.get("id"))})
            if p == "/api/abaikan": return self._json({"ok": sinkron.abaikan(body.get("jenis"), body.get("id"))})
        except Exception as e:
            return self._json({"pesan": f"Galat: {e}"}, 500)
        self._json({"pesan": "tidak dikenal"}, 404)

def _latar():
    """Sinkronisasi otomatis di latar belakang: saat aplikasi dibuka, lalu setiap jeda_jam jam."""
    pg = sinkron.pengaturan()
    if os.environ.get("REGULENS_TANPA_SINKRON") == "1" or not pg.get("sinkron_saat_mulai"): return
    time.sleep(3)
    while True:
        try: o = sinkron.jalankan(); print("Sinkronisasi otomatis selesai:", len(o["kandidat"]), "menunggu,", o.get("diterapkan", {}))
        except Exception as e: print("Sinkronisasi otomatis gagal:", e)
        time.sleep(max(1, float(sinkron.pengaturan().get("jeda_jam", 6))) * 3600)

sinkron.migrasi_pengaturan()
snapshot.tulis()
threading.Thread(target=_latar, daemon=True).start()
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), H) as httpd:
    print(f"Regulens berjalan di http://localhost:{PORT}/index.html  (Ctrl+C untuk berhenti)")
    webbrowser.open(f"http://localhost:{PORT}/index.html")
    httpd.serve_forever()
