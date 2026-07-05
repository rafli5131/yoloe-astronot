# 🚀 Pamagents YOLO Engine (APD Detection)

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-5.0.0-green.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-FP16%20GPU-red.svg)
![Ultralytics](https://img.shields.io/badge/YOLO-Ultralytics-orange.svg)

Engine pendeteksi objek GPU-Accelerated super cepat yang dirancang khusus untuk mendeteksi kedisiplinan penggunaan **Alat Pelindung Diri (APD / PPE)** pada pekerja, seperti Helm Proyek, Rompi Keselamatan (Safety Vest), dan Sepatu.

## ✨ Fitur Utama
- **🎥 Multi-Stream Support**: Melakukan *inference* pada beberapa stream CCTV RTSP atau file video lokal secara bersamaan dalam satu loop.
- **🛡️ Deteksi APD Tangguh**: Mengkombinasikan model YOLO dengan algoritma **Fallback Color-Detection** (Deteksi Warna Darurat) di ruang HSV untuk mendeteksi pakaian *high-visibility* secara akurat, bahkan ketika AI gagal mengenalinya.
- **⚙️ Konfigurasi Sepenuhnya Dinamis**: Atur kamera, *frame rate*, dan jenis APD yang wajib dideteksi langsung melalui `config.json` tanpa perlu mengubah kode sumber.
- **⚡ GPU Accelerated**: Berjalan murni di atas arsitektur NVIDIA CUDA menggunakan presisi komputasi FP16.
- **📊 Strict JSON Output**: Mengirimkan data dengan format Pydantic JSON yang tervalidasi. Log hanya akan diproduksi ketika **ditemukan pelanggaran APD** (Sangat ideal untuk Webhook integrasi).
- **📺 Live View GUI**: Umpan balik visual *real-time* yang menarik dengan kotak merah/hijau serta deskripsi lengkap kelengkapan tiap pekerja.

---

## 🛠️ Instalasi

Pastikan Anda memiliki [Python 3.10+](https://www.python.org/) dan driver NVIDIA CUDA terinstal.

```bash
# Clone repository ini
git clone <repository-url>
cd pamagents_yolo_engine

# Buat environment python
python3 -m venv venv
source venv/bin/activate

# Install semua dependencies
pip install -r requirements.txt
```

---

## ⚙️ Konfigurasi (`config.json`)

Anda bisa mengontrol semua fungsionalitas engine melalui file `config.json`.

```json
{
  "cameras": [
    {
      "camera_id": "CAM-PROJECT-01",
      "video_source": "video/contoh1.mp4"
    }
  ],
  "confidence_threshold": 0.3,
  "target_fps": 5,
  "model_path": "yoloe-26s-seg-pf.pt",
  "required_items": {
    "helmet": ["helmet", "hat", "hard hat"],
    "vest": ["vest", "jacket", "safety vest"]
  }
}
```

### Penjelasan Parameter:
- `cameras`: Daftar (array) sumber video. Bisa berisi URL `.m3u8` / `RTSP` dari CCTV, atau lokasi file lokal seperti `video/test.mp4`.
- `target_fps`: Batasi *frame rate* proses deteksi untuk menghemat sumber daya GPU pada komputer lokal/server.
- `required_items`: Bagian paling penting. Tentukan item APD wajib di sisi "kiri", dan daftar kelas/objek YOLO yang mewakilinya di sisi "kanan". Hapus atau tambah kunci (*key*) sesuai kebutuhan Anda.

---

## 🚀 Cara Menjalankan

Jalankan *engine* utama melalui environment python Anda:
```bash
python main.py
```

- Untuk menghentikan program dengan aman, klik pada salah satu jendela *Live View* dan tekan tombol **`q`** di keyboard, atau gunakan **`Ctrl+C`** di terminal Anda.

---

## 🧠 Cara Kerja Logic APD
1. **Pendeteksian Awal**: Model YOLO memindai frame dan mencari orang (`person`) serta item kandidat APD.
2. **Pemetaan Objek (Overlap)**: Jika sebuah helm atau rompi bertindihan (*overlap*) dengan sebuah kotak badan orang, APD tersebut dianggap sebagai kepunyaan orang itu.
3. **Penyelamatan Warna (Color Fallback)**: Jika atribut "vest" wajib tapi YOLO sama sekali gagal membuat kotak untuk rompi tersebut, sistem akan memindai baju orang tersebut. Jika ditemukan warna Neon Kuning/Oranye khas rompi proyek lebih dari 5%, pekerja dihitung memakai APD.
4. **Validasi Keselamatan**: Apabila pekerja kekurangan satu pun item dari `required_items`, ia ditandai **MERAH** di Live View dan diekspor ke dalam output JSON!

<br/>
<p align="center">
  <i>Built with ❤️ for Site Safety.</i>
</p>
