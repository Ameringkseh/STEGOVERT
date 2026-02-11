import socket
import os
import sys
import time
from colorama import init, Fore, Style

# Coba import library Stegano
try:
    from stegano import lsb
except ImportError:
    print("Error: Library 'stegano' belum diinstall.")
    print("Ketik: pip install stegano")
    sys.exit()

# Inisialisasi Colorama
init(autoreset=True)

# KONFIGURASI DASAR
SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096 # Mengirim 4KB per paket (Layer 4 Segmentation)
DEFAULT_PORT = 5001

def get_local_ip():
    """Mendapatkan IP Address lokal perangkat"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    clear_screen()
    print(Fore.CYAN + "=" * 60)
    print(Fore.YELLOW + Style.BRIGHT + "      PY-STEGANO: HIDDEN MESSAGE NETWORK")
    print(Fore.CYAN + "=" * 60)
    print(f"IP Lokal Anda: {Fore.GREEN}{get_local_ip()}")
    print("-" * 60)

# --- BAGIAN 1: LOGIKA STEGANOGRAFI (MANIPULASI GAMBAR) ---

def embed_message(image_path, secret_message):
    """Menyisipkan pesan ke dalam gambar"""
    print(Fore.YELLOW + "\n[Proses] Menyisipkan pesan rahasia ke piksel gambar...")
    try:
        # Menggunakan algoritma LSB (Least Significant Bit)
        secret_image = lsb.hide(image_path, secret_message)
        output_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secret_packet.png")
        secret_image.save(output_name)
        print(Fore.GREEN + f"[Sukses] Pesan tersimpan di '{output_name}'")
        return output_name
    except Exception as e:
        print(Fore.RED + f"[Gagal] Error saat encoding: {e}")
        return None

def extract_message(image_path):
    """Membaca pesan dari gambar"""
    print(Fore.YELLOW + "\n[Proses] Mengekstrak bit rahasia dari gambar...")
    try:
        clear_message = lsb.reveal(image_path)
        return clear_message
    except Exception as e:
        return f"Gagal membaca pesan: {e}"

# --- BAGIAN 2: MODE PENGIRIM (CLIENT) ---

def start_sender():
    print(Fore.MAGENTA + "\n--- MODE PENGIRIM (SENDER) ---")
    
    # 1. Input Gambar & Pesan
    image_name = input(Fore.WHITE + "Masukkan nama file gambar (contoh: sampel.png): ")
    if not os.path.exists(image_name):
        print(Fore.RED + "File gambar tidak ditemukan!")
        input("Tekan Enter...")
        return

    pesan = input(Fore.WHITE + "Masukkan PESAN RAHASIA: ")
    
    # 2. Proses Steganografi
    ready_file = embed_message(image_name, pesan)
    if not ready_file: return

    # 3. Koneksi Jaringan (Layer 4 & 3)
    target_ip = input(Fore.WHITE + "\nMasukkan IP Tujuan (Receiver): ")
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP Socket
        print(f"{Fore.YELLOW}[Network] Menghubungkan ke {target_ip}:{DEFAULT_PORT}...")
        s.connect((target_ip, DEFAULT_PORT))
        print(f"{Fore.GREEN}[Network] Terhubung!")

        # 4. Protokol Pengiriman File
        filesize = os.path.getsize(ready_file)
        
        # Kirim Header dulu: "NamaFile<SEPARATOR>Ukuran"
        s.send(f"{ready_file}{SEPARATOR}{filesize}".encode())
        time.sleep(1) # Beri jeda agar receiver siap

        # Kirim File (Binary)
        print(f"{Fore.YELLOW}[Transfer] Mengirim paket data...")
        with open(ready_file, "rb") as f:
            while True:
                # Membaca file dalam potongan 4KB (Chunking)
                bytes_read = f.read(BUFFER_SIZE)
                if not bytes_read:
                    break
                s.sendall(bytes_read)
        
        print(f"{Fore.GREEN}[Sukses] File berhasil dikirim.")
        s.close()
        
        # Hapus file temporary agar jejak hilang (Opsional)
        # os.remove(ready_file) 

    except Exception as e:
        print(Fore.RED + f"[Error] Jaringan bermasalah: {e}")
    
    input("Tekan Enter untuk kembali...")

# --- BAGIAN 3: MODE PENERIMA (SERVER) ---

def start_receiver():
    print(Fore.MAGENTA + "\n--- MODE PENERIMA (RECEIVER) ---")
    
    # 1. Setup Server Socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", DEFAULT_PORT)) # Bind ke semua interface
    s.listen(1)
    
    my_ip = get_local_ip()
    print(Fore.CYAN + f"[*] Menunggu kiriman di {my_ip}:{DEFAULT_PORT}...")

    # 2. Menerima Koneksi
    client_socket, address = s.accept()
    print(Fore.GREEN + f"[+] Koneksi diterima dari {address[0]}")

    # 3. Menerima Header File
    received = client_socket.recv(BUFFER_SIZE).decode()
    filename, filesize = received.split(SEPARATOR)
    filename = "diterima_" + os.path.basename(filename) # Rename agar tidak menimpa
    received_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "received")
    os.makedirs(received_dir, exist_ok=True)
    filepath = os.path.join(received_dir, filename)
    filesize = int(filesize)

    # 4. Menerima Binary Data
    print(f"{Fore.YELLOW}[Transfer] Menerima file: {filename} ({filesize} bytes)...")
    
    with open(filepath, "wb") as f:
        bytes_received = 0
        while bytes_received < filesize:
            bytes_read = client_socket.recv(BUFFER_SIZE)
            if not bytes_read:    
                break
            f.write(bytes_read)
            bytes_received += len(bytes_read)

    print(Fore.GREEN + f"[Sukses] File tersimpan: {filepath}")
    client_socket.close()
    s.close()

    # 5. Decode Pesan Rahasia
    choice = input(Fore.WHITE + "\nApakah Anda ingin membuka pesan rahasia sekarang? (y/n): ")
    if choice.lower() == 'y':
        rahasia = extract_message(filepath)
        print(Fore.CYAN + "=" * 40)
        print(Fore.RED + "PESAN RAHASIA TERDETEKSI:")
        print(Fore.WHITE + Style.BRIGHT + rahasia)
        print(Fore.CYAN + "=" * 40)
    
    input("Tekan Enter untuk kembali...")

# --- MENU UTAMA ---

def main():
    while True:
        print_header()
        print("Pilih Peran Anda:")
        print(f"1. {Fore.MAGENTA}SENDER (Pengirim){Fore.WHITE}   - Sisipkan pesan & kirim gambar")
        print(f"2. {Fore.MAGENTA}RECEIVER (Penerima){Fore.WHITE} - Terima gambar & baca pesan")
        print("0. Keluar")
        
        pilihan = input(Fore.YELLOW + "\n[?] Masukkan Pilihan: ")
        
        if pilihan == '1':
            start_sender()
        elif pilihan == '2':
            start_receiver()
        elif pilihan == '0':
            sys.exit()
        else:
            print("Pilihan tidak valid.")

if __name__ == "__main__":
    main()