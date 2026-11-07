"""Membuat ulang dokumen markdown di docs/ dari data/korpus.json (jalankan setelah menerima pembaruan)."""
import json, os
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
d = json.load(open(os.path.join(B, "data", "korpus.json"), encoding="utf-8")); R = {r["id"]: r for r in d["regulasi"]}
L = {"ot": "Obat bahan alam", "obat": "Obat", "alkes": "Alkes", "kosmetik": "Kosmetik", "kuasi": "Kuasi", "suplemen": "Suplemen"}
pr = lambda a: "Lintas produk" if len(a) >= 6 else (", ".join(L[x] for x in a) or "-")
src = lambda ids: ", ".join(R[i]["k"] for i in ids if i in R)
W = lambda n, t: open(os.path.join(B, "docs", n), "w", encoding="utf-8").write(t)
o = ["# Daftar Peraturan Regulens\n", f"Diperbarui: {d.get('diperbarui','-')}. Total {len(R)} entri. Status Cek = belum diverifikasi ke dokumen resmi.\n"]
for r in d["regulasi"]:
    o.append(f"## {r['k']} - {r['t']}\n- Jenis/instansi: {r['j']} / {r['ins']}\n- Status: {r['st']} ({r['tg']})\n- Produk: {pr(r['pr'])}\n- Aktivitas: {', '.join(r['ak']) or '-'}\n- Ringkasan: {r['r']}")
    for k, l in (("sp", "Summary perubahan"), ("mg", "Menggantikan/mengubah"), ("dg", "Diganti/diubah oleh")):
        if r.get(k): o.append(f"- {l}: {r[k]}")
    o.append(f"- PDF/halaman: {r.get('pdf') or r.get('lk') or 'cari di https://peraturan.bpk.go.id atau https://jdih.pom.go.id'}\n")
W("DAFTAR_PERATURAN.md", "\n".join(o))
h = ["# Riwayat Perubahan Peraturan (status Diubah dan Dicabut)\n", "| Peraturan | Status | Diganti/diubah oleh | Summary perubahan |", "|---|---|---|---|"]
h += [f"| {r['k']} | {r['st']} | {r.get('dg','-')} | {r.get('sp','-')} |" for r in d["regulasi"] if r["st"] in ("Diubah", "Dicabut")]
W("RIWAYAT_PERUBAHAN.md", "\n".join(h))
o = ["# Detail Dokumen Persyaratan\n", "Indikatif; verifikasi ke OSS dan instansi terkait.\n", "# A. Persyaratan Fasilitas\n"]
for k in ("fasilitas", "produk"):
    if k == "produk": o.append("# B. Persyaratan Produk\n")
    for x in d[k]:
        o.append(f"## {x['n']}\nInstansi: {x['ins']}\n" + ("\n> **Perlu ditinjau:** dasar hukum berubah ("+"; ".join(t['ket'] for t in x['tinjau'])+")\n" if x.get('tinjau') else "") + "\n**Alur**"); o += [f"{i+1}. {a}" for i, a in enumerate(x["alur"])]
        o.append("\n**Ringkasan persyaratan**"); o += [f"- {p}" for p in x["pre"]]
        for g in x["dok"]: o.append(f"\n**{g['g']}**"); o += [f"- {z}" for z in g["d"]]
        o.append(f"\nDasar hukum (korpus): {src(x['src'])}\n")
W("DETAIL_DOKUMEN_PERSYARATAN.md", "\n".join(o))
o = ["# Peta Perizinan Lintas Instansi dan Titik Benturan\n"]
for a, st in d["peta"].items():
    o.append(f"## Aktivitas: {a}"); o += [f"{i+1}. **{s['t']}** ({s['i']}) - {s['p']}. Sumber: {src(s['s'])}" for i, s in enumerate(st)]; o.append("")
o.append("## Titik benturan (analisis atas korpus, bukan pendapat hukum)"); o += [f"- **{b['t']}**: {b['d']} Sumber: {src(b['s'])}" for b in d["benturan"]]
W("PETA_PERIZINAN_DAN_BENTURAN.md", "\n".join(o))
print("dokumen diperbarui:", len(R), "peraturan")
