"""Pemuat dan pencari korpus. Seluruh analisis hanya memakai data/korpus.json."""
import json, os
DATA = os.path.join(os.path.dirname(__file__), "..", "data", "korpus.json")

def muat():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)

def cari(kata, status=None, produk=None, aktivitas=None):
    kata = (kata or "").lower()
    hasil = []
    for r in muat()["regulasi"]:
        if status and r["st"] != status: continue
        if produk and not (produk in r["pr"] or (produk == "lintas" and len(r["pr"]) >= 6)): continue
        if aktivitas and aktivitas not in r["ak"]: continue
        if kata and kata not in (r["k"] + r["t"] + r["r"]).lower(): continue
        hasil.append(r)
    return hasil

if __name__ == "__main__":
    import sys
    for r in cari(" ".join(sys.argv[1:])):
        print(f'[{r["st"]}] {r["k"]} - {r["t"]}')
