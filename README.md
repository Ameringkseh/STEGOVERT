# STEGOVERT - Steganography Application

Aplikasi steganografi berbasis Python untuk menyembunyikan pesan rahasia di dalam gambar.

## 📋 Persyaratan

- Python 3.10 atau lebih baru
- Windows / Linux / macOS

## 🚀 Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/Ameringkseh/STEGOVERT.git
cd STEGOVERT
```

### 2. Buat Virtual Environment

**Windows:**
```bash
python -m venv Steganography
```

**Linux/macOS:**
```bash
python3 -m venv Steganography
```

### 3. Aktifkan Virtual Environment

**Windows (Command Prompt):**
```bash
Steganography\Scripts\activate
```

**Windows (PowerShell):**
```bash
.\Steganography\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
source Steganography/bin/activate
```

> ⚠️ **Catatan:** Jika menggunakan PowerShell dan mendapat error tentang execution policy, jalankan perintah berikut terlebih dahulu:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## ▶️ Menjalankan Aplikasi

Setelah semua dependencies terinstall, jalankan aplikasi dengan perintah:

**Windows:**
```bash
cd Steganography
python pystegano_gui.py
```

**Linux/macOS:**
```bash
cd Steganography
python3 pystegano_gui.py
```

## 📦 Dependencies

Aplikasi ini menggunakan library berikut:
- `customtkinter` - Modern GUI framework
- `pillow` - Image processing
- `opencv-python` - Computer vision
- `stegano` - Steganography library
- `cryptography` - Encryption
- `qrcode` - QR code generation
- Dan lainnya (lihat `requirements.txt`)

## 🔧 Troubleshooting

### Error: "python is not recognized"
Pastikan Python sudah terinstall dan ditambahkan ke PATH. Download Python di [python.org](https://www.python.org/downloads/)

### Error: "pip is not recognized"
Gunakan `python -m pip` sebagai pengganti `pip`:
```bash
python -m pip install -r requirements.txt
```

### Error saat install opencv-python
Coba update pip terlebih dahulu:
```bash
python -m pip install --upgrade pip
pip install opencv-python
```

## 📄 Lisensi

Lihat file [LICENSE](LICENSE) untuk informasi lebih lanjut.
