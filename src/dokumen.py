"""Folder dokumen Regulens: unggah berkas, ekstrak teks, indeks, cari, dan kenali rujukan peraturan.

Berkas disimpan di dokumen/<folder>/, indeks di data/dokumen.json, teks hasil ekstraksi di data/teks/<id>.txt.
Teks dari .txt/.md/.csv/.json/.html, .docx/.pptx/.xlsx (pustaka standar) dan .pdf (butuh 'pdftotext' atau paket pypdf;
bila tidak ada, berkas tetap tersimpan tetapi isinya tidak dapat dicari)."""
import os, re, io, json, base64, zipfile, uuid, html as H, datetime, subprocess, shutil
import sinkron

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DIR, IDX, TXT = [os.path.join(BASE, p) for p in ("dokumen", os.path.join("data", "dokumen.json"), os.path.join("data", "teks"))]
EXT = {".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".md", ".csv", ".json", ".html", ".htm"}
MAKS = 25 * 1024 * 1024
AWALAN = {"perbpom": "PerBPOM", "perkbpom": "PerBPOM", "peraturan bpom": "PerBPOM", "peraturan badan pengawas obat dan makanan": "PerBPOM",
          "permenkes": "Permenkes", "peraturan menteri kesehatan": "Permenkes", "pp": "PP", "peraturan pemerintah": "PP", "uu": "UU", "undang-undang": "UU",
          "perpres": "Perpres", "peraturan presiden": "Perpres", "kma": "KMA", "keputusan menteri agama": "KMA", "kep. kepala bpjph": "Kep. Kepala BPJPH",
          "keputusan kepala bpjph": "Kep. Kepala BPJPH", "peraturan bpjph": "Peraturan BPJPH", "permen atr/bpn": "Permen ATR/BPN", "permen lhk": "Permen LHK",
          "permen pupr": "Permen PUPR", "permendag": "Permendag"}
POLA = re.compile(r"\b(" + "|".join(sorted((re.escape(a) for a in AWALAN), key=len, reverse=True)) + r")\.?\s*(?:No\.?|Nomor)?\s*(\d+)\s*(?:/|\s+Tahun\s+)\s*(\d{4})", re.I)

def aman(n):
    n = re.sub(r"[^\w.\- ]", "_", os.path.basename(n or "")).strip(" .")
    return n or "berkas"

def aman_folder(f):
    p = [aman(x) for x in re.split(r"[\\/]+", f or "") if x and x not in (".", "..")]
    return "/".join(p) or "Umum"

def muat():
    try:
        with open(IDX, encoding="utf-8") as f: return json.load(f)
    except Exception: return {"dokumen": []}

def simpan_idx(d):
    os.makedirs(os.path.dirname(IDX), exist_ok=True)
    with open(IDX, "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=1)
    try:
        import snapshot; snapshot.tulis()
    except Exception: pass

def _xml(z, cocok):
    out = []
    for n in sorted(z.namelist()):
        if cocok(n):
            x = z.read(n).decode("utf-8", "replace"); x = re.sub(r"</(w:p|a:p|row|si)>", "\n", x)
            out.append(re.sub(r"<[^>]+>", " ", x))
    return H.unescape(re.sub(r"[ \t]+", " ", "\n".join(out)))

def ekstrak(nama, data):
    e = os.path.splitext(nama)[1].lower()
    try:
        if e in (".txt", ".md", ".csv", ".json"): return data.decode("utf-8", "replace")
        if e in (".html", ".htm"): return H.unescape(re.sub(r"<[^>]+>", " ", data.decode("utf-8", "replace")))
        if e in (".docx", ".pptx", ".xlsx"):
            z = zipfile.ZipFile(io.BytesIO(data))
            return _xml(z, {".docx": lambda n: n.startswith("word/") and n.endswith(".xml") and "/_rels" not in n and "document" in n or n.startswith("word/header") or n.startswith("word/footer"),
                            ".pptx": lambda n: n.startswith("ppt/slides/slide") and n.endswith(".xml"),
                            ".xlsx": lambda n: n == "xl/sharedStrings.xml"}[e])
        if e == ".pdf":
            if shutil.which("pdftotext"):
                r = subprocess.run(["pdftotext", "-layout", "-", "-"], input=data, capture_output=True, timeout=120)
                if r.returncode == 0: return r.stdout.decode("utf-8", "replace")
            try:
                from pypdf import PdfReader
                return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
            except Exception: return ""
    except Exception: return ""
    return ""

def rujukan(teks):
    """Kenali nama peraturan dalam teks dan cocokkan dengan korpus. Kembali (id_terkenal, teks_tak_dikenal)."""
    kor = sinkron.muat(sinkron.KORPUS, {"regulasi": []}); idx = {}
    for r in kor["regulasi"]:
        for k in sinkron.kunci_korpus(r): idx.setdefault(k, r["id"])
    ada, tak = [], []
    for m in POLA.finditer(teks or ""):
        k = f"{AWALAN[m.group(1).lower()]}|{int(m.group(2))}|{m.group(3)}"
        if k in idx:
            if idx[k] not in ada: ada.append(idx[k])
        else:
            nama = f"{AWALAN[m.group(1).lower()]} {int(m.group(2))}/{m.group(3)}"
            if nama not in tak: tak.append(nama)
    return ada, tak

JENIS = {s: (jen, ins) for _, s, jen, ins in sinkron.KODE}

def deteksi_peraturan(teks):
    """Bila teks diawali judul peraturan ('... Nomor X Tahun Y tentang ...'), kembalikan identitasnya."""
    awal = (teks or "")[:2500]; m = POLA.search(awal)
    if not m or m.start() > 700: return None
    sisa = awal[m.end(): m.end() + 400]
    if not re.search(r"tentang", sisa, re.I): return None
    t = re.search(r"tentang\s+(.{8,220}?)(?:\n\s*\n|\s{3,}|DENGAN RAHMAT|Menimbang|MENIMBANG|$)", sisa, re.I | re.S)
    judul = re.sub(r"\s+", " ", t.group(1)).strip(" .,:;") if t else ""
    if judul.isupper(): judul = judul.title()
    return {"awalan": AWALAN[m.group(1).lower()], "no": int(m.group(2)), "th": m.group(3), "judul": judul}

def _urus_peraturan(teks, berkas, nama):
    """Dari berkas yang jelas berupa peraturan: lampirkan ke entri korpus yang ada, atau buat entri baru otomatis."""
    det = deteksi_peraturan(teks)
    if not det: return None, False
    kor = sinkron.muat(sinkron.KORPUS, {"regulasi": []}); kunci = f"{det['awalan']}|{det['no']}|{det['th']}"
    for r in kor["regulasi"]:
        if kunci in sinkron.kunci_korpus(r): return r["id"], False
    jen, ins = JENIS.get(det["awalan"], ("Peraturan", ""))
    pr, ak = sinkron.klasifikasi(det["judul"] or nama)
    r = sinkron.tambah_regulasi({"k": f"{det['awalan']} {det['no']}/{det['th']}", "j": jen, "t": det["judul"] or os.path.splitext(nama)[0], "ins": ins, "st": "Cek", "tg": det["th"],
        "ob": "U", "pr": pr, "ak": ak, "r": f"Dibuat otomatis dari berkas {nama} yang diunggah. Status dan ringkasan belum ditinjau.", "pdf": berkas, "v": 0, "otomatis": True})
    return (r.get("id") if r.get("ok") else None), bool(r.get("ok"))

def unggah(nama, folder, data, reg_id=None, pr=None, ak=None):
    nama = aman(nama); e = os.path.splitext(nama)[1].lower()
    if e not in EXT: raise ValueError(f"Jenis berkas {e or '(tanpa ekstensi)'} tidak didukung")
    if len(data) > MAKS: raise ValueError("Berkas melebihi 25 MB")
    folder = aman_folder(folder); tujuan = os.path.join(DIR, *folder.split("/")); os.makedirs(tujuan, exist_ok=True)
    dasar, n = os.path.splitext(nama); final = nama; i = 1
    while os.path.exists(os.path.join(tujuan, final)): i += 1; final = f"{dasar} ({i}){e}"
    with open(os.path.join(tujuan, final), "wb") as f: f.write(data)
    teks = ekstrak(final, data); did = uuid.uuid4().hex[:10]
    if teks.strip():
        os.makedirs(TXT, exist_ok=True)
        with open(os.path.join(TXT, did + ".txt"), "w", encoding="utf-8") as f: f.write(teks)
    ada, tak = rujukan(teks)
    reg_baru = False
    if not reg_id and teks.strip():
        reg_id, reg_baru = _urus_peraturan(teks, "dokumen/" + folder + "/" + final, final)
    d = {"id": did, "nama": final, "folder": folder, "tipe": e[1:], "ukuran": len(data), "tgl": datetime.date.today().isoformat(),
         "berkas": "dokumen/" + folder + "/" + final, "teks": bool(teks.strip()), "cuplikan": re.sub(r"\s+", " ", teks).strip()[:200],
         "rujukan": ada, "tak_dikenal": tak, "reg_id": reg_id or None, "reg_baru": reg_baru, "pr": pr or [], "ak": ak or []}
    idx = muat(); idx["dokumen"].append(d); simpan_idx(idx); return d

def daftar():
    d = muat()["dokumen"]
    folder = set()
    for x in d:
        p = x["folder"].split("/")
        for i in range(1, len(p) + 1): folder.add("/".join(p[:i]))
    if os.path.isdir(DIR):
        for r, ds, _ in os.walk(DIR):
            for s in ds: folder.add(os.path.relpath(os.path.join(r, s), DIR).replace(os.sep, "/"))
    return {"dokumen": d, "folder": sorted(folder)}

def buat_folder(nama):
    f = aman_folder(nama); os.makedirs(os.path.join(DIR, *f.split("/")), exist_ok=True); return f

def hapus(did):
    idx = muat(); d = next((x for x in idx["dokumen"] if x["id"] == did), None)
    if not d: return False
    p = os.path.abspath(os.path.join(BASE, d["berkas"]))
    if p.startswith(os.path.abspath(DIR) + os.sep) and os.path.exists(p): os.remove(p)
    t = os.path.join(TXT, did + ".txt")
    if os.path.exists(t): os.remove(t)
    idx["dokumen"] = [x for x in idx["dokumen"] if x["id"] != did]
    kor = sinkron.muat(sinkron.KORPUS, None)
    if kor:
        for r in kor["regulasi"]:
            if r.get("pdf") == d["berkas"]: r.pop("pdf", None)
        sinkron.simpan(sinkron.KORPUS, kor)
    simpan_idx(idx); return True

def ubah(did, reg_id=None, lepas=False):
    idx = muat(); d = next((x for x in idx["dokumen"] if x["id"] == did), None)
    if not d: return False
    d["reg_id"] = None if lepas else reg_id; simpan_idx(idx); return True

def cari(q, batas=20):
    kata = [k for k in re.findall(r"\w{3,}", (q or "").lower())]
    if not kata: return []
    hasil = []
    for d in muat()["dokumen"]:
        t = ""
        p = os.path.join(TXT, d["id"] + ".txt")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f: t = f.read()
        tl = (d["nama"] + " " + t).lower()
        skor = sum(min(tl.count(k), 20) * (3 if k in d["nama"].lower() else 1) for k in kata)
        if skor:
            i = next((tl.find(k) - len(d["nama"]) - 1 for k in kata if tl.find(k) > len(d["nama"])), 0); i = max(i, 0)
            hasil.append({**d, "skor": skor, "kutipan": re.sub(r"\s+", " ", t[max(i - 80, 0):i + 160]).strip()})
    return sorted(hasil, key=lambda x: -x["skor"])[:batas]


def cocok(items, ambang=0.5, batas=3):
    """Untuk tiap butir daftar periksa, cari dokumen di folder yang kemungkinan menjadi buktinya (kata penting butir ada di dokumen)."""
    henti = set("yang dan atau untuk dengan dari pada dalam akan adalah ini itu juga serta oleh sebagai tidak dapat sudah telah harus ada bagi karena sehingga kepada antara terhadap atas".split())
    docs = []
    for dk in muat()["dokumen"]:
        p = os.path.join(TXT, dk["id"] + ".txt"); t = ""
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f: t = f.read()
        docs.append((dk, (dk["nama"] + " " + t).lower()))
    out = {}
    for it in items:
        kata = {w for w in re.findall(r"[a-z0-9]{4,}", (it.get("teks") or "").lower()) if w not in henti}
        if len(kata) < 2: continue
        hit = []
        for dk, t in docs:
            n = sum(1 for w in kata if w in t)
            if n >= 2 and n / len(kata) >= ambang: hit.append((n / len(kata), dk))
        if hit: out[it["key"]] = [{"nama": dk["nama"], "folder": dk["folder"], "berkas": dk["berkas"], "skor": round(s, 2)} for s, dk in sorted(hit, key=lambda h: -h[0])[:batas]]
    return out
