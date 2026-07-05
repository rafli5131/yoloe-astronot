# Changelog

Semua perubahan penting pada proyek ini akan dicatat di file ini.

## [Unreleased]

### Added (Ditambahkan)
- **Dukungan Multi-Kamera**: Engine sekarang dapat memproses beberapa sumber video/CCTV secara bersamaan (paralel) melalui array `cameras` di `config.json`.
- **Konfigurasi APD Dinamis**: Kriteria APD (helm, rompi, sepatu) dan kata kunci (keyword) kelas YOLO sekarang sepenuhnya bisa diatur (ditambah/dikurangi) langsung melalui blok `required_items` di `config.json`.
- **Deteksi Warna Darurat (Fallback Color Detection)**: Menambahkan algoritma pengecekan warna di ruang HSV untuk mendeteksi pakaian High-Visibility (Neon Orange, Kuning Stabilo, Hijau) untuk mengatasi *false negatives* ketika YOLO gagal mendeteksi kelas rompi/jaket.
- **Live View UI**: Menambahkan antarmuka *real-time* berbasis OpenCV. Menampilkan kotak merah (Pelanggaran/Missing APD) dan kotak hijau (APD Lengkap) secara langsung di video.
- **Looping Video Lokal**: Menambahkan fitur auto-rewind pada `VideoStreamer` agar file video lokal (seperti `.mp4`) terus berulang tanpa henti untuk keperluan *testing*.

### Changed (Diubah)
- **Format Payload JSON**: Mengubah format output menjadi skema `ApdViolation`. Output JSON kini memuat `camera_id`, `timestamp`, `person_bbox`, dan rincian `missing_apd`, serta **hanya dicetak apabila terjadi pelanggaran APD**.
- **Normalisasi Kecepatan Pemutaran**: Pembacaan file offline sekarang disinkronkan dengan `target_fps` sehingga video lokal tidak berputar terlalu cepat.
- **Logika Overlap yang Diperlonggar**: Penentuan apakah APD menempel pada badan pekerja kini lebih akurat dengan mengecek *center point* dari kotak APD, atau minimal 10% overlap area.

### Removed (Dihapus)
- Menghapus pembatasan deteksi yang *hardcoded* (statis) dari `main.py` sehingga engine kini sepenuhnya *data-driven* dari config.
