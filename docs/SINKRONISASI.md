# Persetujuan sebelum masuk database (v2.5)
Peraturan baru dan perubahan status **tetap terdeteksi otomatis**, tetapi **hanya masuk database setelah Anda setujui** di panel Pembaruan (menu Peraturan): tombol **Terima ke korpus** atau **Abaikan**. Yang sudah Anda terima otomatis ditautkan ke Persyaratan Fasilitas/Produk dan ditandai Perlu ditinjau; yang Anda abaikan tidak muncul lagi. Peraturan hasil sinkronisasi atau unggahan PDF yang sudah masuk dapat dihapus dengan tombol **Hapus dari database** (peraturan bawaan tidak dapat dihapus).

- **Penyaring relevansi.** Peraturan tentang organisasi, kepegawaian, anggaran, dan sejenisnya (mis. "Organisasi dan Tata Kerja Unit Pelaksana Teknis") dilewati. Nama instansi (mis. "Badan Pengawas Obat dan Makanan") tidak lagi dihitung sebagai kata kunci. Tambahkan kata pengecualian sendiri di `data/sumber.json` (`kata_abaikan`).
- **Migrasi satu kali.** Pada start pertama versi ini, `data/pengaturan.json` diubah ke persetujuan manual (`terima_otomatis: false`, `versi: 2`) dan entri otomatis lama yang tidak relevan dan belum pernah Anda setujui dibersihkan (dicatat di log).
- Ingin kembali ke penerimaan otomatis tanpa persetujuan? Setel `terima_otomatis` ke `true`.

# Pembaruan Otomatis (v2.4)

## Mengapa sebelumnya data "tidak terupdate"
1. **Sinkronisasi hanya berjalan saat diminta**, dan tidak berjalan ketika aplikasi ditutup.
2. **`index.html` yang dibuka langsung (tanpa `python app.py`) tidak bisa membaca `data/korpus.json`** karena batasan keamanan browser, sehingga menampilkan data bawaan yang usang. Perubahan yang dibuat saat server hidup (sinkronisasi, PDF yang diunggah) tidak terlihat.
3. **Peraturan yang ditambahkan lewat formulir hanya disimpan di browser** (per alamat: `localhost` berbeda dari `file://`), bukan di `korpus.json`.
4. **Peraturan baru tidak ditautkan ke Persyaratan Fasilitas/Produk**; hanya muncul di daftar Peraturan.

## Cara kerja sekarang
- **Sinkron otomatis.** `python app.py` menyinkronkan di latar belakang saat dibuka dan setiap 6 jam selama berjalan. Pengaturan ada di `data/pengaturan.json`:
  - `sinkron_saat_mulai` (true/false) dan `jeda_jam`;
  - `terima_otomatis` (bawaan **false**): bila true, peraturan baru dan perubahan status langsung masuk `korpus.json` tanpa persetujuan dan ditandai **Otomatis, belum ditinjau**; bila false, semuanya menunggu persetujuan Anda. Riwayat tampil di panel Pembaruan dan `data/log_sinkron.json`;
  - `tautan_otomatis`: peraturan baru ditautkan ke Persyaratan Fasilitas/Produk yang beririsan produk dan aktivitasnya dan ditandai **Perlu ditinjau**.
  Bawaan sekarang persetujuan manual (lihat bagian pertama).
- **Saat aplikasi ditutup.** Jadwalkan `src/sinkron.py` (Windows: `jadwal_windows.bat`; Linux/macOS: cron; GitHub: workflow). Skrip itu menerapkan pengaturan yang sama.
- **Salinan `data/data.js`.** Setiap kali data berubah (sinkron, tambah peraturan, unggah/hapus dokumen), `data/data.js` ditulis ulang. `index.html` membacanya ketika dibuka langsung, jadi data terbaru tetap tampil walau server tidak berjalan (hanya baca; unggah dan sinkron manual butuh server). Panel Pembaruan menampilkan waktu salinan.
- **Tambah peraturan manual** (menu Dokumen & Korpus): bila server berjalan, tersimpan permanen di `data/korpus.json` dan otomatis ditautkan ke persyaratan terkait. Tanpa server, tersimpan di browser saja dan ditautkan di memori.
- **Unggah PDF peraturan** (judul berbentuk "... Nomor X Tahun Y tentang ..."): otomatis dilampirkan ke entri korpus yang ada, atau dibuat entri baru berstatus "Perlu verifikasi" dengan judul dari berkas. Memo biasa yang hanya menyebut peraturan tidak dianggap peraturan.
- **Yang tetap manual:** isi persyaratan dan daftar dokumen (perlu dibaca dari naskah). Entri otomatis harus Anda tinjau; tombol "Tandai sudah ditinjau" tersedia.

# Mode manual (terima_otomatis = false)

# Sinkronisasi Otomatis dengan Situs Pemerintah

## Cara kerja
1. `src/sinkron.py` membaca sumber di `data/sumber.json` (JDIH BPK: daftar Peraturan BPOM dan pencarian kata kunci; JDIH BPJPH; JDIH BPOM).
2. Peraturan yang relevan (kata kunci farmasi, halal, perizinan, ruang, lingkungan, dsb.) dibandingkan dengan `data/korpus.json`.
3. Hasilnya ditulis ke `data/pembaruan.json`: **peraturan baru** (dikategorikan otomatis menurut produk dan aktivitas) dan **usulan perubahan status** (mis. "PerBPOM 5/2026 mencabut PerBPOM 24/2021").
4. Pada menu **Peraturan**, panel **Pembaruan** di bagian atas, Anda meninjau dan menekan **Terima** atau **Abaikan**. Yang diterima masuk ke `data/korpus.json` dan langsung tampil di semua tab.

Peraturan baru yang diterima ditandai `otomatis` dan "Perlu verifikasi" bila tanggal berlakunya tidak terbaca. Ringkasan isi **tidak** dibuat otomatis; baca naskah resmi.

## Apa yang ikut tersinkron di Persyaratan Fasilitas dan Persyaratan Produk
| Hal | Perlakuan |
|---|---|
| **Dasar hukum (tag sumber)** | Otomatis bergerak saat Anda menerima usulan status: peraturan pengganti ditambahkan ke daftar dasar hukum fasilitas/produk terkait, Peta Perizinan, dan titik benturan. Peraturan lama tampil dicoret. |
| **Penanda "Perlu ditinjau"** | Otomatis muncul pada entri fasilitas/produk yang dasar hukumnya dicabut atau diubah, lengkap dengan keterangan dan tombol **Tandai sudah ditinjau**. |
| **Usulan tautan** | Peraturan baru yang Anda terima dicocokkan dengan produk dan aktivitas tiap entri; hasilnya muncul di panel Pembaruan (menu Peraturan) sebagai usulan yang perlu Anda terima. |
| **Isi persyaratan dan daftar dokumen** | **Tidak** ditulis ulang otomatis. Isinya harus dibaca dari naskah peraturan; mesin hanya memberi tanda dan tautan PDF agar Anda memperbaruinya (edit `data/korpus.json`). |

Alasannya: mengubah persyaratan secara otomatis dari teks peraturan berisiko salah, sedangkan tanda dan tautan aman dan tetap menghemat waktu penelusuran.

## Menjalankan
- Manual: `python src/sinkron.py` (atau tombol **Sinkronkan sekarang** bila aplikasi dibuka lewat `python app.py`).
- Harian di Windows: klik dua kali `jadwal_windows.bat` (Task Scheduler pukul 07.00).
- Harian di Linux/macOS: `crontab -e` lalu `0 7 * * * cd /jalur/regulens_project && python3 src/sinkron.py`.
- Harian di GitHub: unggah proyek, aktifkan `.github/workflows/sinkron.yml`.
- Terima semuanya tanpa tinjauan (tidak disarankan): `python src/sinkron.py --terima-semua`.
- Setelah menerima pembaruan, jalankan `python src/buat_dokumen.py` untuk memperbarui dokumen di `docs/`.

## Batasan penting
- **Belum diuji pada situs asli.** Lingkungan pengembangan tidak memiliki akses internet. Pembaca halaman JDIH BPK dirancang dari struktur halaman yang saya periksa dan diuji dengan contoh HTML tiruan (tests/test_sinkron.py). Bila situs mengubah tampilan, atau memblokir akses otomatis (galat 403), perbarui `data/sumber.json` (mis. `user_agent`) atau pembaca di `src/sinkron.py`.
- Sumber bertipe `umum` (JDIH BPJPH dan JDIH BPOM) hanya mengenali tautan yang teksnya memuat "Nomor X Tahun Y"; halaman yang dimuat dengan JavaScript tidak terbaca.
- Parameter pencarian `keyword` pada JDIH BPK belum diverifikasi; sumber `jenis=230` (Peraturan BPOM) yang strukturnya sudah diperiksa.
- Aplikasi yang dibuka langsung sebagai berkas (`file://`) tidak dapat menarik data atau memanggil sinkronisasi karena batasan keamanan browser. Gunakan `python app.py`.
- Usulan status memakai hubungan "Mencabut/Mengubah" pada situs sumber; tetap perlu ditinjau.
- Hormati ketentuan penggunaan situs sumber; jeda antar-permintaan diatur `jeda_detik`.
