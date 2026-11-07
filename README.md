# Regulens v2.5 - Pemantau Regulasi Farmasi

Aplikasi web (satu berkas `index.html`, tanpa server) untuk merekap status peraturan farmasi (berlaku, diubah, dicabut, rancangan), ringkasan perubahan, persyaratan fasilitas, persyaratan produk, peta perizinan lintas instansi, dan titik benturan antar-peraturan. Semua temuan wajib bersumber dari korpus `data/korpus.json`.

## Menjalankan
- Disarankan: `python app.py` atau klik `run_app.bat` (server lokal http://localhost:8765; panel **Pembaruan** di menu Peraturan dan sinkronisasi aktif).
- Cara cepat: buka `index.html` di browser (tanpa sinkronisasi).

## Struktur
- `index.html` aplikasi; `data/korpus.json` korpus peraturan, fasilitas, produk, peta, benturan
- `src/korpus.py` pencarian korpus (CLI: `python src/korpus.py CPOB`)
- `src/unduh_pdf.py` unduh massal PDF peraturan (butuh internet)
- `tests/` uji integritas korpus: `python -m unittest discover -s tests`
- `docs/` panduan, rencana, logbook, daftar peraturan, detail dokumen, peta, sumber
- `Regulens_Presentasi.pptx` latar belakang dan rancangan

## Menambah peraturan
Bagian **Data peraturan (korpus)** pada menu **Dokumen & Korpus** menerima JSON; atau edit `data/korpus.json`. Peringatan: ringkasan bersifat indikatif, bukan nasihat hukum.

## Isi baru v1.2
80 entri peraturan, riwayat perubahan, aktivitas ekspor/pengawasan dan penarikan/perizinan usaha/halal, ATR/BPN, PUPR, lingkungan, dan dokumen Word rancangan (`docs/Rancangan_Proyek_Regulens.docx`).

## Sinkronisasi otomatis (v1.4)
`src/sinkron.py` memantau JDIH BPK/BPJPH/BPOM dan mengusulkan peraturan baru serta perubahan status; Anda meninjau di panel Pembaruan pada menu Peraturan. Dasar hukum di Persyaratan Fasilitas/Persyaratan Produk ikut diperbarui dan entri yang terdampak ditandai "Perlu ditinjau"; isi persyaratan tidak ditulis ulang otomatis. Lihat `docs/SINKRONISASI.md` (termasuk batasan: belum diuji pada situs asli).

## Dokumen dan Analisis Kasus (v1.9)
Menu **Dokumen & Korpus**: unggah berkas ke folder `dokumen/`, cari isinya, dan kaitkan dengan peraturan di korpus. Menu **Analisis Kasus**: analisis kasus di luar database dengan filter dan daftar periksa dokumen. Lihat `docs/DOKUMEN_DAN_ANALISIS_KASUS.md`. Unggah berkas memerlukan `python app.py`.

Catatan: port server dapat diubah dengan variabel lingkungan `REGULENS_PORT` (mis. `set REGULENS_PORT=8800` di Windows, lalu `python app.py`).

## Pembaruan otomatis (v2.4)
Sinkronisasi berjalan otomatis saat `python app.py` dibuka dan tiap 6 jam; peraturan baru dan perubahan status terdeteksi otomatis dan **menunggu persetujuan Anda** (panel Pembaruan di menu Peraturan); yang disetujui ditautkan ke Persyaratan Fasilitas/Produk (ditandai Perlu ditinjau). Data terbaru juga disalin ke `data/data.js` agar `index.html` yang dibuka langsung tetap mutakhir. Atur di `data/pengaturan.json`; lihat `docs/SINKRONISASI.md`. PDF peraturan yang diunggah otomatis menjadi entri korpus.

## Versi 2.5
Persetujuan manual sebelum peraturan masuk database (dengan penyaring relevansi dan tombol Hapus dari database); Analisis Kasus memilih fasilitas/produk yang dimaksud dengan memperhatikan peran, dan laporan kini 3 bagian + lampiran.
