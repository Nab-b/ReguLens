"""Mengunduh semua PDF peraturan yang tautan langsungnya tersedia ke folder pdf/.
Jalankan dengan koneksi internet: python src/unduh_pdf.py"""
import os, re, urllib.request
from korpus import muat
OUT = os.path.join(os.path.dirname(__file__), "..", "pdf")
os.makedirs(OUT, exist_ok=True)
for r in muat()["regulasi"]:
    if not r.get("pdf"): continue
    nama = re.sub(r"[^A-Za-z0-9]+", "_", r["k"]).strip("_") + ".pdf"
    try:
        urllib.request.urlretrieve(r["pdf"], os.path.join(OUT, nama))
        print("OK   ", nama)
    except Exception as e:
        print("GAGAL", nama, e)
