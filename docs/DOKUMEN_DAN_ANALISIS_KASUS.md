# Dokumen & Korpus dan Analisis Kasus (v2.5)

## Menu Dokumen & Korpus
Satu menu, dua bagian. **Berkas dokumen** (atas) adalah arsip berkas Anda; **Data peraturan / korpus** (bawah) adalah katalog peraturan yang dipakai semua analisis. Kartu dokumen punya tombol **Buat entri korpus** yang mengisi formulir korpus dengan templat dari dokumen (nama, jalur berkas sebagai `pdf`, dan peraturan yang disebut tetapi belum ada di database); lengkapi nama singkat (`k`), instansi, status, produk, aktivitas, lalu **Simpan ke korpus**.

### Berkas dokumen
Unggah aktif bila aplikasi dibuka lewat `python app.py` (atau `run_app.bat`).

1. Pilih folder (atau buat folder baru, boleh bertingkat seperti `Kasus/PBF`), pilih satu atau beberapa berkas, tekan **Unggah**.
2. Berkas disimpan di folder `dokumen/` pada proyek. Teksnya diekstrak dan diindeks (`data/dokumen.json`, `data/teks/`).
3. **Cari di dalam isi dokumen** menampilkan hasil berperingkat dengan kutipan.
4. Nama peraturan di dalam dokumen (mis. "PerBPOM 7/2024", "Peraturan BPOM Nomor 7 Tahun 2024") dikenali dan ditautkan ke korpus. Muncul peringatan bila dokumen merujuk peraturan yang **sudah dicabut**, dan daftar rujukan yang **tidak ada di database**.
5. PDF yang jelas berupa peraturan ("... Nomor X Tahun Y tentang ...") otomatis dilampirkan ke entri korpus yang ada, atau dibuat entri baru berstatus Perlu verifikasi (ditandai Otomatis). Selain itu, dokumen dapat dilampirkan ke satu peraturan ("Berkas milik: ..."); di menu Peraturan muncul tombol **Berkas lokal**, jadi PDF resmi yang Anda unduh bisa dibuka dari dalam aplikasi.

Jenis berkas: PDF, DOCX, PPTX, XLSX, TXT, MD, CSV, JSON, HTML (maks. 25 MB). Teks PDF terbaca bila `pdftotext` (poppler) atau paket `pypdf` terpasang (`pip install pypdf`); tanpa itu berkas tetap tersimpan tetapi isinya tidak dapat dicari.

## Menu Analisis Kasus (kasus di luar database)
Dari uraian atau dokumen kasus, menghasilkan **dasar hukum yang dikutip**, **persyaratan yang relevan**, dan **analisis kesenjangan dokumen** dalam sebuah laporan.

1. Tempel uraian kasus, atau pilih berkas (.txt/.md/.csv; .docx/.pdf/.pptx/.xlsx bila lewat `python app.py`, dibaca tanpa disimpan).
2. Tekan **Analisis** (atau **Deteksi** lebih dulu). Aplikasi menebak **fasilitas dan produk yang dimaksud** dan langsung memilih persyaratannya. Deteksi **memperhatikan peran**: pihak yang menjadi subjek kasus (mis. "PT X adalah PBF", "akan mengimpor") dihitung, sedangkan pihak lawan (mis. "dijual ke apotek", "dibeli dari industri farmasi", "pemasok") tidak. Contoh: kasus PBF yang mengimpor obat dan menjual ke apotek memilih PBF, Importir, Perizinan dasar usaha, dan SJPH halal, tanpa Apotek dan Industri Farmasi. Bagian "Dasar deteksi" menampilkan kutipan penyebabnya.
3. Ubah pilihan dengan mengklik chip **Fasilitas** dan **Produk** pada formulir. Filter produk, objek, aktivitas (boleh lebih dari satu), dan sejak tahun hanya dipakai bila belum ada fasilitas atau produk yang dipilih.
4. Hasil di layar: **dasar hukum yang dikutip** (dicabut/diubah/tidak ada di database beserta penggantinya), **kesiapan dokumen** (daftar periksa untuk mencatat dokumen yang **sudah Anda miliki**; yang belum dicentang menjadi kesenjangan; opsi "tampilkan hanya yang belum ada"; folder Dokumen menyarankan "kemungkinan bukti"), **persyaratan yang dianalisis**, peraturan yang tersaring, dan dokumen terkait di folder.
5. **Laporan** (3 bagian + lampiran): 1. Dasar hukum yang dikutip, 2. Kesiapan dokumen per persyaratan, 3. Kesenjangan beserta dasar hukumnya, lampiran uraian kasus. Tersedia **Unduh laporan (Word)**, **Unduh (.md)**, **Cetak laporan**, dan **Simpan ke folder Dokumen** (folder "Analisis Kasus", HTML). Temuan utama, rekomendasi, tenggat, dan titik benturan tidak lagi ditampilkan.

Uraian kasus dan centang daftar periksa hanya berlaku selama sesi (hilang bila halaman dimuat ulang); simpan laporannya bila ingin menyimpan hasil.

## Batasan
- Tebakan fasilitas/produk berbasis kata kunci dan konteks kalimat sederhana (peran subjek vs pihak lawan); uraian yang ambigu atau memakai istilah lain bisa meleset. Periksa chip terpilih dan "Dasar deteksi" sebelum membaca persentase kesiapan; ubah dengan mengklik chip.
- "Kemungkinan bukti" dari folder Dokumen dicocokkan dari kata penting butir (minimal separuhnya ada di dokumen); bisa keliru, jadi bukan pengganti pemeriksaan dokumen.
- Laporan analisis yang disimpan ke folder Dokumen ikut menjadi bahan pencarian "dokumen terkait" pada analisis berikutnya.
- Analisis adalah penyaringan dan pencocokan kata kunci serta nama peraturan. Ia tidak memahami fakta kasus, tidak menilai kepatuhan, dan bukan pendapat hukum.
- Deteksi produk/aktivitas hanya perkiraan berbasis kata kunci (mis. "serum", "krim", "notifikasi" dikenali sebagai kosmetik). Bila produk tidak terdeteksi, aplikasi memberi peringatan dan hasil mencakup semua produk; pilih produk secara manual lalu periksa filter sebelum membaca hasil.
- Tenggat terbatas pada yang tercatat di korpus.
- Berkas tersimpan tanpa enkripsi di komputer lokal; jangan mengunggah data rahasia pada komputer bersama.
- Tanpa `python app.py`, unggah berkas tidak aktif (bagian korpus tetap bisa dipakai) dan Analisis Kasus hanya menerima teks tempelan atau berkas teks.

## Mode berkas (server tidak berjalan)
Daftar dokumen tampil dari salinan `data/data.js` (dapat dibuka, difilter menurut nama dan isi); unggah dan hapus membutuhkan `python app.py`.
