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
python -m venv venv
```

**Linux/macOS:**
```bash
python3 -m venv venv
```

### 3. Aktifkan Virtual Environment

**Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
source venv/bin/activate
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
python pystegano_gui.py
```

**Linux/macOS:**
```bash
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

## 🌐 Setup Jaringan & Firewall

Aplikasi ini menggunakan **port TCP 5001** untuk komunikasi. Pastikan port tersebut diizinkan di firewall.

### Windows Firewall

Buka **Command Prompt (Administrator)** dan jalankan:
```bash
netsh advfirewall firewall add rule name="STEGOVERT" dir=in action=allow protocol=TCP localport=5001
```

Atau secara manual:
1. Buka **Windows Defender Firewall** → **Advanced Settings**
2. Klik **Inbound Rules** → **New Rule**
3. Pilih **Port** → **TCP** → masukkan `5001`
4. Pilih **Allow the connection** → beri nama `STEGOVERT` → **Finish**

### Linux (UFW)

```bash
sudo ufw allow 5001/tcp
sudo ufw reload
```

### macOS

```bash
sudo pfctl -e
echo "pass in proto tcp from any to any port 5001" | sudo pfctl -ef -
```

### ✅ Checklist Koneksi

Sebelum menggunakan fitur kirim/terima, pastikan:
- [ ] Kedua perangkat terhubung ke **jaringan WiFi/LAN yang sama**
- [ ] **Receiver** menjalankan server terlebih dahulu (klik `START LISTENING`)
- [ ] **Sender** memasukkan **IP Address** receiver yang benar (terlihat di header aplikasi)
- [ ] Port `5001` **tidak diblokir** oleh firewall di kedua perangkat
- [ ] Tidak ada VPN yang aktif (bisa mengganggu koneksi lokal)

> 💡 **Tip:** Gunakan tombol `📡 PING` di aplikasi untuk menguji koneksi sebelum mengirim file.

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
