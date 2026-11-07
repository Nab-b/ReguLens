"""Sinkronisasi Regulens dengan situs pemerintah.

Alur: baca sumber (data/sumber.json) -> kenali peraturan relevan -> bandingkan dengan
data/korpus.json -> tulis usulan ke data/pembaruan.json. Usulan baru masuk korpus hanya
setelah ditinjau (tombol Terima di aplikasi, atau: python src/sinkron.py --terima-semua).

Pemakaian:  python src/sinkron.py            (sinkron dan tulis usulan)
            python src/sinkron.py --terima-semua
Hanya memakai pustaka standar Python."""
import json, os, re, sys, time, html as H, datetime, urllib.request, urllib.parse

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
KORPUS, PEMB, SUMBER = [os.path.join(BASE, "data", n) for n in ("korpus.json", "pembaruan.json", "sumber.json")]
UA = "Mozilla/5.0 (Regulens sinkronisasi; riset akademik)"
BULAN = {b: i + 1 for i, b in enumerate("Januari Februari Maret April Mei Juni Juli Agustus September Oktober November Desember".split())}

# (awalan judul huruf kecil, singkatan di korpus, jenis, instansi)
KODE = [
 ("peraturan badan pengawas obat dan makanan", "PerBPOM", "Peraturan BPOM", "BPOM"),
 ("peraturan kepala badan pengawas obat dan makanan", "PerBPOM", "Peraturan BPOM", "BPOM"),
 ("peraturan bpom", "PerBPOM", "Peraturan BPOM", "BPOM"),
 ("perka bpom", "PerBPOM", "Peraturan BPOM", "BPOM"),
 ("peraturan menteri kesehatan", "Permenkes", "Peraturan Menteri", "Kemenkes"),
 ("keputusan menteri kesehatan", "Kepmenkes", "Keputusan Menteri", "Kemenkes"),
 ("peraturan pemerintah", "PP", "Peraturan Pemerintah", "Pemerintah"),
 ("peraturan presiden", "Perpres", "Peraturan Presiden", "Presiden"),
 ("undang-undang", "UU", "Undang-Undang", "DPR & Presiden"),
 ("keputusan menteri agama", "KMA", "Keputusan Menteri Agama", "Kementerian Agama"),
 ("peraturan menteri agama", "PMA", "Peraturan Menteri Agama", "Kementerian Agama"),
 ("keputusan kepala badan penyelenggara jaminan produk halal", "Kep. Kepala BPJPH", "Keputusan Kepala BPJPH", "BPJPH"),
 ("peraturan badan penyelenggara jaminan produk halal", "Peraturan BPJPH", "Peraturan BPJPH", "BPJPH"),
 ("peraturan menteri agraria", "Permen ATR/BPN", "Peraturan Menteri", "Kementerian ATR/BPN"),
 ("peraturan menteri lingkungan hidup", "Permen LH", "Peraturan Menteri", "KLH/BPLH"),
 ("peraturan menteri pekerjaan umum", "Permen PUPR", "Peraturan Menteri", "Kementerian PUPR"),
 ("peraturan menteri perdagangan", "Permendag", "Peraturan Menteri", "Kemendag"),
]
SINGKAT = sorted({k[1] for k in KODE}, key=len, reverse=True)
JUDUL = re.compile(r"(?P<jenis>(?:Peraturan|Keputusan|Undang|Perka|Surat)[^<>\n]*?)\s+No(?:mor|\.)?\s*(?P<no>\d+)\s+Tahun\s+(?P<th>\d{4})", re.I)

def kode(judul):
    j = judul.lower().strip()
    for aw, s, jen, ins in KODE:
        if j.startswith(aw): return s, jen, ins
    return None

def kunci(judul):
    m = JUDUL.search(judul or "")
    c = kode(judul or "")
    if not (m and c): return None
    return f"{c[0]}|{int(m.group('no'))}|{m.group('th')}", c, int(m.group("no")), m.group("th")

def kunci_korpus(r):
    out = []
    for s in SINGKAT:
        if r["k"].startswith(s):
            out += [f"{s}|{int(a)}|{b}" for a, b in re.findall(r"(\d+)/(\d{4})", r["k"])]
            break
    return out

def teks(x): return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", x))).strip()

def tgl(t):
    m = re.search(r"mulai berlaku pada tanggal\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", t)
    if m and m.group(2).capitalize() in BULAN:
        return datetime.date(int(m.group(3)), BULAN[m.group(2).capitalize()], int(m.group(1))).isoformat()

def ambil(url, params=None):
    if params: url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

A = re.compile(r'<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S | re.I)
HEAD = re.compile(r"(Dicabut dengan|Diubah dengan|Mencabut|Mengubah)", re.I)

def parse_bpk(h, sumber):
    """Daftar hasil pencarian peraturan.bpk.go.id: judul 'Nomor X Tahun Y', tentang, status, unduhan."""
    anc = [(m.start(), m.end(), m.group(1), teks(m.group(2))) for m in A.finditer(h)]
    mulai = [a for a in anc if "/Details/" in a[2] and re.match(r"^(Peraturan|Keputusan|Undang)", a[3]) and re.search(r"\bNomor\s+\d+\s+Tahun\s+\d{4}", a[3])]
    hasil = []
    for i, a in enumerate(mulai):
        akhir = mulai[i + 1][0] if i + 1 < len(mulai) else len(h)
        seg = h[a[0]:akhir]; sa = [x for x in anc if a[0] <= x[0] < akhir]
        idd = re.search(r"/Details/(\d+)", a[2]).group(1)
        tentang = next((x[3] for x in sa if f"/Details/{idd}" in x[2] and x[3] != a[3]), "")
        pdf = next((x[2] for x in sa if "/Download/" in x[2]), "")
        rel = {"Mencabut": [], "Mengubah": [], "Dicabut dengan": [], "Diubah dengan": []}
        heads = [(m.start(), m.group(1).capitalize() if False else m.group(1)) for m in HEAD.finditer(seg)]
        for x in sa:
            if x[0] == a[0] or f"/Details/{idd}" in x[2] or "/Details/" not in x[2]: continue
            pos = x[0] - a[0]; cur = [hd for p, hd in heads if p < pos]
            if cur and re.match(r"^(Peraturan|Perka|Keputusan|Undang)", x[3]):
                key = next(k for k in rel if k.lower() == cur[-1].lower())
                rel[key].append(x[3])
        hasil.append({"judul": a[3], "tentang": tentang, "url": a[2], "pdf": pdf, "sumber": sumber,
                      "tgl_berlaku": tgl(teks(seg)), "mencabut": rel["Mencabut"], "mengubah": rel["Mengubah"],
                      "dicabut_oleh": rel["Dicabut dengan"], "diubah_oleh": rel["Diubah dengan"]})
    return hasil

def parse_umum(h, sumber, url_dasar):
    hasil = []
    for m in A.finditer(h):
        t = teks(m.group(2))
        if JUDUL.search(t) and kode(t):
            hasil.append({"judul": t, "tentang": "", "url": urllib.parse.urljoin(url_dasar, m.group(1)), "pdf": "", "sumber": sumber,
                          "tgl_berlaku": None, "mencabut": [], "mengubah": [], "dicabut_oleh": [], "diubah_oleh": []})
    return hasil

def klasifikasi(t):
    t = t.lower(); pr = []
    for k, v in (("kosmetik", "kosmetik"), ("kuasi", "kuasi"), ("suplemen", "suplemen"), ("bahan alam", "ot"), ("tradisional", "ot"), ("alat kesehatan", "alkes"), ("obat", "obat")):
        if k in t and v not in pr: pr.append(v)
    ak = [a for a, ks in (("produksi", ("pembuatan", "produksi")), ("distribusi", ("distribusi", "peredaran", "pengelolaan")), ("impor", ("impor", "pemasukan")),
          ("ekspor", ("ekspor",)), ("registrasi", ("registrasi", "notifikasi", "izin edar")), ("label", ("label", "penandaan", "iklan", "promosi")),
          ("halal", ("halal",)), ("pengawasan", ("pengawasan", "penarikan", "farmakovigilans")), ("usaha", ("perizinan berusaha", "berbasis risiko", "ruang", "lingkungan", "bangunan gedung"))) if any(k in t for k in ks)]
    return pr, ak

def muat(p, d):
    try:
        with open(p, encoding="utf-8") as f: return json.load(f)
    except Exception: return d

def _p(n): return os.path.join(os.path.dirname(os.path.abspath(KORPUS)), n)

DEF_PENG = {"sinkron_saat_mulai": False, "jeda_jam": 6, "terima_otomatis": False, "tautan_otomatis": False}
def pengaturan():
    d = dict(DEF_PENG); d.update(muat(_p("pengaturan.json"), {})); return d

def simpan(p, d):
    with open(p, "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=1)
    if os.path.abspath(p) in (os.path.abspath(KORPUS), os.path.abspath(PEMB), os.path.abspath(_p("log_sinkron.json"))):
        try:
            import snapshot; snapshot.tulis()
        except Exception: pass

def _log(aksi, detail):
    lg = muat(_p("log_sinkron.json"), [])
    lg.append({"waktu": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "aksi": aksi, "detail": detail})
    simpan(_p("log_sinkron.json"), lg[-200:])

ABAIKAN_DEFAULT = ["organisasi dan tata kerja", "unit pelaksana teknis", "jabatan fungsional", "jabatan pimpinan", "pegawai", "aparatur", "anggaran",
    "remunerasi", "tunjangan", "kode etik", "seleksi", "pakaian dinas", "rencana strategis", "reformasi birokrasi", "tata naskah", "kearsipan",
    "penilaian kinerja", "barang milik negara", "pengadaan barang", "gratifikasi", "pengendalian intern", "tugas belajar", "disiplin", "pelatihan"]
NAMA_INSTANSI = re.compile(r"badan pengawas obat dan makanan|badan penyelenggara jaminan produk halal|kementerian kesehatan|kementerian agama|menteri kesehatan", re.I)

def relevan_teks(t, kk, abaikan=None):
    """Relevan bila tema (tanpa nama instansi) memuat kata kunci farmasi dan tidak memuat kata kunci kepegawaian/organisasi."""
    t = NAMA_INSTANSI.sub(" ", (t or "")).lower()
    if any(a in t for a in (abaikan or ABAIKAN_DEFAULT)): return False
    return any(k in t for k in kk)

def relevan(item, kk, abaikan=None):
    j = item["judul"]
    return relevan_teks(item["tentang"] or (j.split("tentang", 1)[1] if "tentang" in j.lower() else ""), kk, abaikan)

def jalankan(ambil_fn=ambil):
    global UA
    kor = muat(KORPUS, {"regulasi": []}); cfg = muat(SUMBER, {"sumber": [], "kata_kunci": []})
    UA = cfg.get("user_agent", UA)
    lama = muat(PEMB, {"kandidat": [], "usulan": [], "abaikan": []})
    indeks = {}
    for r in kor["regulasi"]:
        for k in kunci_korpus(r): indeks[k] = r
    semua, status_sumber = [], []
    for s in cfg["sumber"]:
        n, galat = 0, None
        for p in range(1, s.get("halaman", 1) + 1):
            try:
                params = dict(s.get("params", {}))
                if p > 1: params["p"] = p
                h = ambil_fn(s["url"], params or None)
                it = parse_bpk(h, s["nama"]) if s["tipe"] == "bpk" else parse_umum(h, s["nama"], s["url"])
                semua += it; n += len(it)
            except Exception as e:
                galat = f"{type(e).__name__}: {e}"; break
            time.sleep(cfg.get("jeda_detik", 1.5) if ambil_fn is ambil else 0)
        status_sumber.append({"nama": s["nama"], "jumlah": n, "galat": galat})
    abaikan = set(lama.get("abaikan", []))
    kand = {k["id"]: k for k in lama.get("kandidat", [])}
    usulan = {u["id"]: u for u in lama.get("usulan", [])}
    for it in semua:
        kk = kunci(it["judul"])
        if not kk: continue
        kunci_, (sing, jen, ins), no, th = kk
        rid = re.sub(r"[^a-z0-9]+", "-", kunci_.lower()).strip("-")
        if kunci_ not in indeks and relevan(it, cfg["kata_kunci"], list(set(ABAIKAN_DEFAULT + cfg.get("kata_abaikan", [])))) and rid not in abaikan:
            kand[rid] = {"id": rid, "k": f"{sing} {no}/{th}", "jenis": jen, "ins": ins, "judul": it["judul"], "tentang": it["tentang"], "url": it["url"], "pdf": it["pdf"],
                         "sumber": it["sumber"], "tgl_berlaku": it["tgl_berlaku"], "mencabut": it["mencabut"], "mengubah": it["mengubah"], "ditemukan": datetime.date.today().isoformat()}
        oleh = f"{sing} {no}/{th}"
        def tambah(daftar, ke, syarat, dibalik=False):
            for ref in daftar:
                k2 = kunci(ref)
                if not k2: continue
                tgt = indeks.get(k2[0])
                if dibalik:   # item ini sendiri dicabut/diubah oleh ref
                    tgt, oleh_ = indeks.get(kunci_), f"{k2[1][0]} {k2[2]}/{k2[3]}"
                else: oleh_ = oleh
                if tgt and tgt["st"] in syarat and tgt["id"] != oleh_:
                    uid = f"{tgt['id']}>{ke}>{re.sub(r'[^a-z0-9]+','-',oleh_.lower())}"
                    if uid not in abaikan: usulan[uid] = {"id": uid, "regulasi_id": tgt["id"], "k": tgt["k"], "dari": tgt["st"], "ke": ke, "oleh": oleh_, "sumber": f"{it['sumber']} ({it['url']})"}
        tambah(it["mencabut"], "Dicabut", ("Berlaku", "Diubah", "Cek", "Draft"))
        tambah(it["mengubah"], "Diubah", ("Berlaku",))
        tambah(it["dicabut_oleh"], "Dicabut", ("Berlaku", "Diubah", "Cek"), True)
        tambah(it["diubah_oleh"], "Diubah", ("Berlaku",), True)
    kand = {k: v for k, v in kand.items() if not any(x in indeks for x in [f"{v['k'].rsplit(' ',1)[0]}|{int(v['k'].rsplit(' ',1)[1].split('/')[0])}|{v['k'].split('/')[1]}"])}
    out = {"diperbarui": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "sumber": status_sumber,
           "kandidat": sorted(kand.values(), key=lambda x: x["k"]), "usulan": list(usulan.values()), "tautan": lama.get("tautan", []), "abaikan": sorted(abaikan)}
    simpan(PEMB, out)
    g = [s["nama"] for s in status_sumber if s["galat"]]
    if out["kandidat"] or out["usulan"] or g:
        _log("sinkron", f"{len(out['kandidat'])} peraturan baru, {len(out['usulan'])} usulan status" + (f"; sumber gagal dibaca: {len(g)}" if g else ""))
    if pengaturan().get("terima_otomatis") and (out["kandidat"] or out["usulan"]):
        n1, n2 = len(out["kandidat"]), len(out["usulan"])
        for u in list(out["usulan"]): terima_usulan(u["id"])
        for k in list(out["kandidat"]): terima_kandidat(k["id"], manual=False)
        out = muat(PEMB, out); out["diterapkan"] = {"kandidat": n1, "usulan": n2}
    return out

def _kor(): return muat(KORPUS, {"regulasi": []})


def _cari_reg(kor, nama):
    ks = set(kunci_korpus({"k": nama}))
    return next((r for r in kor["regulasi"] if ks & set(kunci_korpus(r))), None) if ks else None

def terapkan_pergantian(kor, lama_id, baru, ket):
    """Peraturan lama dicabut/diubah: tambahkan peraturan pengganti ke dasar hukum dan tandai entri 'perlu ditinjau'."""
    n, hari = 0, datetime.date.today().isoformat()
    for jenis in ("fasilitas", "produk"):
        for x in kor.get(jenis, []):
            if lama_id in x["src"]:
                if baru and baru["id"] not in x["src"]: x["src"].append(baru["id"])
                catat = {"reg": lama_id, "oleh": baru["id"] if baru else None, "ket": ket, "tgl": hari}
                tj = x.setdefault("tinjau", [])
                if not any(t["reg"] == lama_id and t["oleh"] == catat["oleh"] for t in tj): tj.append(catat); n += 1
    for grup in list(kor.get("peta", {}).values()):
        for l in grup:
            if baru and lama_id in l["s"] and baru["id"] not in l["s"]: l["s"].append(baru["id"])
    for b in kor.get("benturan", []):
        if baru and lama_id in b["s"] and baru["id"] not in b["s"]: b["s"].append(baru["id"])
    return n

def usul_tautan(kor, reg, batas=6):
    """Usulan menautkan peraturan baru ke entri fasilitas/produk yang beririsan produk dan aktivitasnya."""
    hasil = []
    for jenis in ("fasilitas", "produk"):
        for x in kor.get(jenis, []):
            if reg["id"] in x["src"]: continue
            xp = x["pr"] if isinstance(x["pr"], list) else [x["pr"]]
            semua = "lintas" in xp or len(xp) >= 6
            if not (semua or not reg["pr"] or any(p in xp for p in reg["pr"])): continue
            irisan = set(reg["ak"]) & set(x["ak"])
            if irisan: hasil.append((len(irisan), {"id": f"{reg['id']}>{jenis}>{x['n']}", "reg_id": reg["id"], "k": reg["k"], "jenis": jenis, "n": x["n"]}))
    return [h[1] for h in sorted(hasil, key=lambda h: -h[0])[:batas]]

def terima_tautan(tid):
    pe = muat(PEMB, {}); kor = _kor()
    t = next((x for x in pe.get("tautan", []) if x["id"] == tid), None)
    if not t: return False
    reg = next((r for r in kor["regulasi"] if r["id"] == t["reg_id"]), None)
    x = next((x for x in kor.get(t["jenis"], []) if x["n"] == t["n"]), None)
    if x and reg and reg["id"] not in x["src"]:
        x["src"].append(reg["id"])
        x.setdefault("tinjau", []).append({"reg": reg["id"], "oleh": None, "ket": f"Dasar hukum baru ditambahkan ({reg['k']}); periksa apakah persyaratan perlu disesuaikan.", "tgl": datetime.date.today().isoformat()})
    pe["tautan"] = [y for y in pe["tautan"] if y["id"] != tid]
    simpan(KORPUS, kor); simpan(PEMB, pe); return True

def tandai_tinjau(jenis, n):
    kor = _kor()
    for x in kor.get(jenis, []):
        if x["n"] == n: x.pop("tinjau", None)
    simpan(KORPUS, kor); return True

def auto_tautan(kor, reg, batas=8):
    """Tautkan peraturan ke persyaratan fasilitas/produk yang beririsan produk dan aktivitasnya, lalu tandai 'perlu ditinjau'."""
    n, hari = 0, datetime.date.today().isoformat()
    for t in usul_tautan(kor, reg, batas):
        x = next((x for x in kor.get(t["jenis"], []) if x["n"] == t["n"]), None)
        if x and reg["id"] not in x["src"]:
            x["src"].append(reg["id"])
            x.setdefault("tinjau", []).append({"reg": reg["id"], "oleh": None, "ket": f"Dasar hukum baru ditambahkan otomatis ({reg['k']}); periksa apakah persyaratan perlu disesuaikan.", "tgl": hari}); n += 1
    return n

def tambah_regulasi(reg, auto=True):
    """Tambah peraturan ke data/korpus.json (permanen) dan tautkan otomatis ke persyaratan terkait."""
    kor = _kor(); r = dict(reg)
    if not r.get("k") or not r.get("t") or str(r["k"]).startswith("("): return {"ok": False, "pesan": "Kolom k (nama singkat) dan t (judul) wajib diisi."}
    r.setdefault("id", re.sub(r"[^a-z0-9]+", "-", str(r["k"]).lower()).strip("-"))
    r.setdefault("pengguna", not r.get("otomatis"))
    for k, v in (("j", "Peraturan"), ("ins", ""), ("st", "Cek"), ("tg", ""), ("ob", "U"), ("pr", []), ("ak", []), ("r", ""), ("v", 0)): r.setdefault(k, v)
    ks = set(kunci_korpus(r))
    for x in kor["regulasi"]:
        if x["id"] == r["id"] or (ks and ks & set(kunci_korpus(x))): return {"ok": False, "pesan": f"{r['k']} sudah ada di korpus.", "id": x["id"]}
    kor["regulasi"].append(r)
    n = auto_tautan(kor, r) if auto else 0
    simpan(KORPUS, kor); _log("peraturan ditambahkan", f"{r['k']}; {n} persyaratan ditautkan otomatis")
    return {"ok": True, "id": r["id"], "tautan": n, "pesan": f"{r['k']} ditambahkan dan ditautkan ke {n} persyaratan."}

def hapus_regulasi(rid, paksa=False):
    """Hapus peraturan yang ditambahkan otomatis/oleh pengguna beserta tautannya di persyaratan, peta, dan benturan."""
    kor = _kor(); r = next((x for x in kor["regulasi"] if x["id"] == rid), None)
    if not r: return {"ok": False, "pesan": "Peraturan tidak ditemukan."}
    if not paksa and not (r.get("otomatis") or r.get("pengguna")): return {"ok": False, "pesan": "Hanya peraturan yang ditambahkan otomatis atau oleh pengguna yang dapat dihapus."}
    kor["regulasi"] = [x for x in kor["regulasi"] if x["id"] != rid]
    for jn in ("fasilitas", "produk"):
        for x in kor.get(jn, []):
            x["src"] = [i for i in x["src"] if i != rid]
            if x.get("tinjau"):
                x["tinjau"] = [t for t in x["tinjau"] if t.get("reg") != rid and t.get("oleh") != rid]
                if not x["tinjau"]: x.pop("tinjau")
    for g in kor.get("peta", {}).values():
        for l in g: l["s"] = [i for i in l["s"] if i != rid]
    for b in kor.get("benturan", []): b["s"] = [i for i in b["s"] if i != rid]
    simpan(KORPUS, kor)
    pe = muat(PEMB, {}); pe.setdefault("abaikan", []).append(rid)
    pe["kandidat"] = [k for k in pe.get("kandidat", []) if k["id"] != rid]; simpan(PEMB, pe)
    _log("peraturan dihapus", r["k"]); return {"ok": True, "pesan": f"{r['k']} dihapus dari database."}

def migrasi_pengaturan():
    """Versi 2: peraturan baru harus disetujui dulu. Pengaturan lama diubah dan entri otomatis yang tidak relevan dibersihkan (sekali)."""
    p = _p("pengaturan.json"); d = muat(p, {})
    if d.get("versi", 0) >= 2: return 0
    d.update({"versi": 2, "terima_otomatis": False}); d.setdefault("sinkron_saat_mulai", True); d.setdefault("jeda_jam", 6); d.setdefault("tautan_otomatis", True)
    simpan(p, d)
    kk = muat(SUMBER, {}).get("kata_kunci", []) or ["obat", "kosmetik", "kesehatan", "halal"]
    n = 0
    for r in list(_kor()["regulasi"]):
        if r.get("otomatis") and not r.get("disetujui") and not relevan_teks(r.get("t", ""), kk):
            if hapus_regulasi(r["id"], paksa=True)["ok"]: n += 1
    if n: _log("pembersihan", f"{n} peraturan otomatis yang tidak relevan dihapus")
    return n

def tandai_reg_ditinjau(rid):
    kor = _kor()
    for r in kor["regulasi"]:
        if r["id"] == rid: r["otomatis"] = False
    simpan(KORPUS, kor); return True

def terima_kandidat(kid, manual=True):
    pe = muat(PEMB, {}); kor = _kor()
    c = next((k for k in pe.get("kandidat", []) if k["id"] == kid), None)
    if not c: return False
    pr, ak = klasifikasi(c["judul"] + " " + c["tentang"])
    ok = c["tgl_berlaku"] and c["tgl_berlaku"] <= datetime.date.today().isoformat()
    rel = "; ".join(filter(None, [("Mencabut: " + ", ".join(c["mencabut"])) if c["mencabut"] else "", ("Mengubah: " + ", ".join(c["mengubah"])) if c["mengubah"] else ""]))
    kor["regulasi"].append({"id": c["id"], "k": c["k"], "j": c["jenis"], "t": c["tentang"] or c["judul"], "ins": c["ins"], "st": "Berlaku" if ok else "Cek",
        "tg": ("Berlaku " + c["tgl_berlaku"]) if c["tgl_berlaku"] else "-", "ob": "U", "pr": pr, "ak": ak,
        "r": f"Terdeteksi otomatis dari {c['sumber']} pada {c['ditemukan']}. Ringkasan belum disusun; baca naskah resmi. {rel}".strip(),
        "mg": "; ".join(c["mencabut"] + c["mengubah"]) or None, "pdf": c["pdf"] or None, "lk": c["url"], "v": 0, "otomatis": True, "disetujui": bool(manual)})
    for r in kor["regulasi"][-1:]:
        for k in [k for k, v in list(r.items()) if v is None]: del r[k]
    pe["kandidat"] = [k for k in pe["kandidat"] if k["id"] != kid]
    baru = kor["regulasi"][-1]
    if pengaturan().get("tautan_otomatis"):
        n = auto_tautan(kor, baru); _log("peraturan baru", f"{baru['k']} masuk korpus; {n} persyaratan ditautkan otomatis")
    else:
        ada = {t["id"] for t in pe.get("tautan", [])}
        pe.setdefault("tautan", []).extend(t for t in usul_tautan(kor, baru) if t["id"] not in ada)
    simpan(KORPUS, kor); simpan(PEMB, pe); return True

def terima_usulan(uid):
    pe = muat(PEMB, {}); kor = _kor()
    u = next((x for x in pe.get("usulan", []) if x["id"] == uid), None)
    if not u: return False
    r = next((x for x in kor["regulasi"] if x["id"] == u["regulasi_id"]), None)
    if r:
        r["st"] = u["ke"]; r["dg"] = u["oleh"] if u["ke"] == "Dicabut" else "Diubah " + u["oleh"]
        r["sp"] = f"{u['oleh']} {'mencabut' if u['ke']=='Dicabut' else 'mengubah'} peraturan ini menurut {u['sumber']}. Usulan otomatis: baca naskah resmi untuk rincian perubahan."
        baru = _cari_reg(kor, u["oleh"])
        terapkan_pergantian(kor, r["id"], baru, f"{r['k']} {'dicabut' if u['ke']=='Dicabut' else 'diubah'} oleh {u['oleh']}; periksa apakah persyaratan dan dokumen perlu disesuaikan.")
    pe["usulan"] = [x for x in pe["usulan"] if x["id"] != uid]
    simpan(KORPUS, kor); simpan(PEMB, pe)
    if r: _log("status berubah", f"{r['k']} menjadi {u['ke']} oleh {u['oleh']}")
    return True

def abaikan(jenis, iid):
    pe = muat(PEMB, {}); pe.setdefault("abaikan", []).append(iid)
    pe["kandidat"] = [k for k in pe.get("kandidat", []) if k["id"] != iid]; pe["usulan"] = [u for u in pe.get("usulan", []) if u["id"] != iid]; pe["tautan"] = [t for t in pe.get("tautan", []) if t["id"] != iid]
    simpan(PEMB, pe); return True

if __name__ == "__main__":
    o = jalankan()
    for s in o["sumber"]: print(("GALAT " + s["galat"]) if s["galat"] else "OK", s["nama"], s["jumlah"])
    print(f"{len(o['kandidat'])} peraturan baru, {len(o['usulan'])} usulan perubahan status")
    if "--terima-semua" in sys.argv:
        for u in list(o["usulan"]): terima_usulan(u["id"])
        for k in list(o["kandidat"]): terima_kandidat(k["id"])
        print("Semua usulan diterima ke data/korpus.json (status tetap ditandai belum diverifikasi).")
