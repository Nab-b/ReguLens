# Panduan Pengguna Regulens
1. **Peraturan**: panel Pembaruan di bagian atas, lalu cari nomor/judul; saring status, objek (fasilitas/produk), produk (obat, alkes, kosmetik, kuasi, obat bahan alam, suplemen, lintas produk), dan aktivitas (produksi, distribusi, impor, ekspor, registrasi/notifikasi, pengawasan dan penarikan, perizinan usaha, label). Peraturan berstatus Diubah/Dicabut menampilkan summary perubahan. Tombol Unduh PDF membuka berkas resmi; bila belum ada tautan langsung, tombol mengarah ke pencarian BPK/JDIH. Tombol CSV mengekspor daftar.
2. **Persyaratan Fasilitas**: alur, ringkasan persyaratan, dan detail dokumen (NIB, KKPR, lingkungan, PBG/SLF, sertifikat standar, teknis, mutu).
3. **Persyaratan Produk** (aktivitas: registrasi/notifikasi, impor, label, pengawasan, ekspor, halal): alur dari kualifikasi pendaftar sampai label, dengan detail dokumen (administratif, mutu, nonklinik/klinik, penandaan).
4. **Peta Perizinan**: urutan izin lintas instansi per aktivitas dan titik benturan; klik tag sumber untuk membuka peraturannya.
5. **Dokumen & Korpus**: satu menu untuk dua hal. Bagian atas = berkas dokumen (unggah, cari isi, kaitkan dengan peraturan, tombol Buat entri korpus). Bagian bawah = data peraturan (tambah JSON, unduh, hapus tambahan).
## Analisis kasus berikutnya
Tambahkan peraturan terkait ke korpus, lalu telusuri melalui filter produk dan aktivitas. Catat temuan beserta tag sumbernya.

Entri Persyaratan Fasilitas/Persyaratan Produk yang dasar hukumnya berubah ditandai **Perlu ditinjau** (dasar hukum pengganti ditambahkan otomatis setelah Anda menerima usulan status; isi persyaratan tetap Anda perbarui sendiri). Panel **Pembaruan** (di bagian atas menu Peraturan): daftar peraturan baru dan usulan perubahan status dari situs pemerintah; tinjau lalu Terima atau Abaikan. Tombol Sinkronkan aktif bila aplikasi dibuka lewat `python app.py`.

6. **Analisis Kasus**: tempel uraian kasus, atur filter, tekan Analisis; hasil berupa dasar hukum yang dikutip, kesiapan dokumen (daftar periksa), dan persyaratan terpilih; fasilitas/produk yang dimaksud ditebak otomatis dan dapat diubah lewat chip. Lihat `docs/DOKUMEN_DAN_ANALISIS_KASUS.md`.

Catatan: bila `python app.py` berjalan, peraturan baru terdeteksi otomatis dan menunggu persetujuan Anda di panel Pembaruan (menu Peraturan); entri yang disetujui ditautkan otomatis ke persyaratan dan perlu Anda tinjau.
