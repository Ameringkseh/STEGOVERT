"""
STEGOVERT - Advanced Steganography Gaming-Style Application
Aplikasi untuk menyembunyikan pesan rahasia dalam gambar dan mengirimnya melalui jaringan.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import socket
import os
import sys
import threading
import time
import math
import base64
import hashlib
import winsound
import io

# Optional imports
try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

# Import stegano library
try:
    from stegano import lsb
except ImportError:
    print("Error: Library 'stegano' belum diinstall.")
    print("Ketik: pip install stegano")
    sys.exit()

# ===================== KONFIGURASI =====================
SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096
DEFAULT_PORT = 5001
APP_VERSION = "3.0.0"
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Color Scheme - Cyberpunk Gaming Style
COLORS = {
    "bg_dark": "#0a0a0f",
    "bg_card": "#12121a",
    "bg_card_hover": "#1a1a25",
    "accent_cyan": "#00d4ff",
    "accent_magenta": "#ff00aa",
    "accent_purple": "#8b5cf6",
    "accent_green": "#00ff88",
    "accent_orange": "#ff6b35",
    "text_primary": "#ffffff",
    "text_secondary": "#a0a0b0",
    "border_glow": "#00d4ff",
    "success": "#00ff88",
    "error": "#ff4466",
    "warning": "#ffaa00"
}

# Compatibility for removed toggle
COLORS_DARK = COLORS
COLORS_LIGHT = COLORS

# ===================== UTILITY FUNCTIONS =====================
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


def encrypt_message(message, password):
    """Encrypt message using XOR cipher with password-derived key"""
    if not password:
        return message
    # Create key from password using SHA256
    key = hashlib.sha256(password.encode()).digest()
    # XOR encrypt
    encrypted = []
    for i, char in enumerate(message.encode('utf-8')):
        encrypted.append(char ^ key[i % len(key)])
    # Base64 encode for safe storage
    return "ENC:" + base64.b64encode(bytes(encrypted)).decode('utf-8')


def decrypt_message(encrypted_msg, password):
    """Decrypt message using XOR cipher with password-derived key"""
    if not encrypted_msg.startswith("ENC:"):
        return encrypted_msg  # Not encrypted
    if not password:
        return "[ENCRYPTED - PASSWORD REQUIRED]"
    try:
        # Remove prefix and decode base64
        encoded = encrypted_msg[4:]
        encrypted_bytes = base64.b64decode(encoded)
        # Create key from password
        key = hashlib.sha256(password.encode()).digest()
        # XOR decrypt
        decrypted = []
        for i, byte in enumerate(encrypted_bytes):
            decrypted.append(byte ^ key[i % len(key)])
        return bytes(decrypted).decode('utf-8')
    except Exception:
        return "[DECRYPTION FAILED - WRONG PASSWORD?]"


def play_sound(sound_type):
    """Play system sound effects"""
    try:
        if sound_type == "success":
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        elif sound_type == "error":
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC)
        elif sound_type == "send":
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
        elif sound_type == "receive":
            winsound.PlaySound("SystemNotification", winsound.SND_ALIAS | winsound.SND_ASYNC)
    except Exception:
        pass  # Sound not available


def ping_host(ip, port, timeout=3):
    """Test connection to host"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        s.close()
        return True
    except Exception:
        return False


def generate_qr_code(data):
    """Generate QR code image from data"""
    if not HAS_QRCODE:
        return None
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=6,
            border=2
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#00d4ff", back_color="#0a0a0f")
        return img.convert("RGB")
    except Exception as e:
        print(f"QR Error: {e}")
        return None


def estimate_capacity(image_path):
    """Estimate how many characters can be hidden in an image"""
    try:
        img = Image.open(image_path)
        width, height = img.size
        # LSB uses 3 bits per pixel (RGB), 8 bits per character
        total_pixels = width * height
        # Conservative estimate: use only 10% of capacity for safety
        max_chars = (total_pixels * 3) // 8 // 10
        return max_chars, width, height
    except Exception:
        return 0, 0, 0


def format_size(bytes_size):
    """Format bytes to human readable size"""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    else:
        return f"{bytes_size / (1024 * 1024):.1f} MB"


# ===================== ANIMATED BUTTON CLASS =====================
class GlowButton(ctk.CTkButton):
    """Custom animated button with glow effect"""
    def __init__(self, master, glow_color=COLORS["accent_cyan"], **kwargs):
        self.glow_color = glow_color
        super().__init__(master, **kwargs)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        self.configure(border_color=self.glow_color, border_width=2)
    
    def _on_leave(self, event):
        self.configure(border_color=self.glow_color, border_width=0)


# ===================== MAIN APPLICATION =====================
class StegovertApp(ctk.CTk, TkinterDnD.DnDWrapper if HAS_DND else object):
    def __init__(self):
        super().__init__()
        if HAS_DND:
            self.TkdndVersion = TkinterDnD._require(self)
        
        # Window Configuration
        self.title("⚡ STEGOVERT - Covert Message System")
        self.geometry("1000x700")
        self.minsize(900, 650)
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Load assets
        self.logo_image = None
        try:
            logo_path = os.path.join(ASSETS_DIR, "logo.png")
            if os.path.exists(logo_path):
                # Set window icon
                icon_img = Image.open(logo_path)
                self.iconphoto(False, ImageTk.PhotoImage(icon_img))
                
                # Prepare for header
                self.logo_image = ctk.CTkImage(
                    light_image=Image.open(logo_path),
                    dark_image=Image.open(logo_path),
                    size=(50, 50)
                )
        except Exception as e:
            print(f"Error loading assets: {e}")
        
        # Variables
        self.selected_image_path = None
        self.encoded_image_path = None
        self.received_image_path = None
        self.server_socket = None
        self.server_running = False
        self.current_theme = "dark"
        self.animation_running = True
        
        # Set default theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create UI
        self._create_header()
        self._create_main_content()
        self._create_status_bar()
        
        # Start animation loop
        self._start_animations()
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    # ==================== ANIMATIONS ====================
    def _start_animations(self):
        """Start UI animations"""
        self._pulse_animation()
    
    def _pulse_animation(self):
        """Pulse animation for active elements"""
        if self.animation_running:
            self.after(50, self._pulse_animation)
    
    # ==================== HEADER ====================
    def _create_header(self):
        """Create cyberpunk-style header"""
        # Main header container
        header_frame = ctk.CTkFrame(
            self, 
            height=80, 
            corner_radius=0,
            fg_color=COLORS["bg_card"],
            border_width=2,
            border_color=COLORS["accent_cyan"]
        )
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Left section - Logo & Title
        left_section = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_section.pack(side="left", padx=20, fill="y")
        
        # Animated Logo
        self.logo_label = ctk.CTkLabel(
            left_section, 
            text="◈" if not self.logo_image else "",
            image=self.logo_image,
            font=ctk.CTkFont(size=40, weight="bold"),
            text_color=COLORS["accent_cyan"]
        )
        self.logo_label.pack(side="left", padx=(0, 10), pady=15)
        
        # Title with gradient effect
        title_frame = ctk.CTkFrame(left_section, fg_color="transparent")
        title_frame.pack(side="left", pady=15)
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="STEGOVERT",
            font=ctk.CTkFont(family="Consolas", size=28, weight="bold"),
            text_color=COLORS["accent_cyan"]
        )
        title_label.pack(anchor="w")
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="COVERT MESSAGE SYSTEM",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLORS["text_secondary"]
        )
        subtitle_label.pack(anchor="w")
        
        # Center section - Stats
        center_section = ctk.CTkFrame(header_frame, fg_color="transparent")
        center_section.pack(side="left", expand=True, fill="both", padx=20)
        
        stats_frame = ctk.CTkFrame(center_section, fg_color="transparent")
        stats_frame.pack(expand=True)
        
        # IP Display with gaming style
        ip_frame = ctk.CTkFrame(
            stats_frame, 
            fg_color=COLORS["bg_dark"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["accent_purple"]
        )
        ip_frame.pack(pady=20)
        
        ip_icon = ctk.CTkLabel(ip_frame, text="🌐", font=ctk.CTkFont(size=14))
        ip_icon.pack(side="left", padx=(10, 5), pady=8)
        
        ip_label = ctk.CTkLabel(
            ip_frame,
            text=f"LOCAL IP: {get_local_ip()}",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=COLORS["accent_purple"]
        )
        ip_label.pack(side="left", padx=(0, 10), pady=8)
        
        # Right section - Version info
        right_section = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_section.pack(side="right", padx=20, fill="y")
        
        version_frame = ctk.CTkFrame(
            right_section, 
            fg_color=COLORS["bg_dark"],
            corner_radius=8
        )
        version_frame.pack(pady=22)
        
        ctk.CTkLabel(
            version_frame,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=COLORS["accent_green"]
        ).pack(padx=15, pady=8)
    
    # ==================== MAIN CONTENT ====================
    def _create_main_content(self):
        """Create main content area with gaming-style tabs"""
        # Tab container
        tab_container = ctk.CTkFrame(self, fg_color="transparent")
        tab_container.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Custom tab buttons
        tab_buttons_frame = ctk.CTkFrame(tab_container, fg_color="transparent")
        tab_buttons_frame.pack(fill="x", pady=(0, 10))
        
        self.current_tab = "sender"
        
        # Tab buttons with gaming style
        self.sender_tab_btn = ctk.CTkButton(
            tab_buttons_frame,
            text="⚡ TRANSMIT",
            command=lambda: self._switch_tab("sender"),
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            fg_color=COLORS["accent_cyan"],
            text_color=COLORS["bg_dark"],
            hover_color=COLORS["accent_purple"],
            height=45,
            corner_radius=10,
            width=200
        )
        self.sender_tab_btn.pack(side="left", padx=5)
        
        self.receiver_tab_btn = ctk.CTkButton(
            tab_buttons_frame,
            text="📡 RECEIVE",
            command=lambda: self._switch_tab("receiver"),
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            fg_color=COLORS["bg_card"],
            text_color=COLORS["text_secondary"],
            hover_color=COLORS["bg_card_hover"],
            height=45,
            corner_radius=10,
            width=200,
            border_width=1,
            border_color=COLORS["accent_cyan"]
        )
        self.receiver_tab_btn.pack(side="left", padx=5)
        
        self.about_tab_btn = ctk.CTkButton(
            tab_buttons_frame,
            text="ℹ️ INTEL",
            command=lambda: self._switch_tab("about"),
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            fg_color=COLORS["bg_card"],
            text_color=COLORS["text_secondary"],
            hover_color=COLORS["bg_card_hover"],
            height=45,
            corner_radius=10,
            width=150,
            border_width=1,
            border_color=COLORS["accent_cyan"]
        )
        self.about_tab_btn.pack(side="left", padx=5)
        
        # Content frames
        self.content_frame = ctk.CTkScrollableFrame(
            tab_container, 
            fg_color=COLORS["bg_card"],
            corner_radius=15,
            border_width=2,
            border_color=COLORS["accent_cyan"],
            label_text=""
        )
        self.content_frame.pack(fill="both", expand=True)
        
        # Create tab contents
        self.sender_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.receiver_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.about_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        self._build_sender_tab()
        self._build_receiver_tab()
        self._build_about_tab()
        
        # Show sender tab by default
        self.sender_frame.pack(fill="both", expand=True, padx=15, pady=15)
    
    def _switch_tab(self, tab_name):
        """Switch between tabs with animation"""
        self.current_tab = tab_name
        
        # Hide all frames
        self.sender_frame.pack_forget()
        self.receiver_frame.pack_forget()
        self.about_frame.pack_forget()
        
        # Reset all tab buttons
        for btn in [self.sender_tab_btn, self.receiver_tab_btn, self.about_tab_btn]:
            btn.configure(
                fg_color=COLORS["bg_card"],
                text_color=COLORS["text_secondary"],
                border_width=1
            )
        
        # Show selected tab and highlight button
        if tab_name == "sender":
            self.sender_frame.pack(fill="both", expand=True, padx=15, pady=15)
            self.sender_tab_btn.configure(
                fg_color=COLORS["accent_cyan"],
                text_color=COLORS["bg_dark"],
                border_width=0
            )
        elif tab_name == "receiver":
            self.receiver_frame.pack(fill="both", expand=True, padx=15, pady=15)
            self.receiver_tab_btn.configure(
                fg_color=COLORS["accent_magenta"],
                text_color=COLORS["text_primary"],
                border_width=0
            )
        elif tab_name == "about":
            self.about_frame.pack(fill="both", expand=True, padx=15, pady=15)
            self.about_tab_btn.configure(
                fg_color=COLORS["accent_purple"],
                text_color=COLORS["text_primary"],
                border_width=0
            )
    
    # ==================== SENDER TAB ====================
    def _build_sender_tab(self):
        """Build the Sender tab UI with gaming style"""
        # Main container with 2 columns
        main_frame = ctk.CTkFrame(self.sender_frame, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)
        
        # Configure grid
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Left Panel - IMAGE SECTION
        left_panel = ctk.CTkFrame(
            main_frame, 
            fg_color=COLORS["bg_dark"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["accent_purple"]
        )
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        
        # Panel header
        header_left = ctk.CTkFrame(left_panel, fg_color="transparent")
        header_left.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header_left, 
            text="📷 PAYLOAD IMAGE",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color=COLORS["accent_purple"]
        ).pack(side="left")
        
        # Status indicator
        self.image_status_indicator = ctk.CTkLabel(
            header_left,
            text="● AWAITING",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLORS["warning"]
        )
        self.image_status_indicator.pack(side="right")
        
        # Image Preview with glow border
        image_container = ctk.CTkFrame(
            left_panel,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=2,
            border_color=COLORS["accent_purple"]
        )
        image_container.pack(padx=15, pady=10, fill="both", expand=True)
        
        self.sender_image_label = ctk.CTkLabel(
            image_container, 
            text="[ NO IMAGE LOADED ]\n\n⬇ DROP OR BROWSE ⬇",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=COLORS["text_secondary"],
            corner_radius=10
        )
        # Fix height for image container (min height 400px)
        self.sender_image_label.pack(fill="both", expand=True, padx=10, pady=10, ipady=180)
        
        # Remove Image Button (Initially hidden)
        self.remove_img_btn = ctk.CTkButton(
            image_container,
            text="✕",
            width=30,
            height=30,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["error"],
            hover_color="#ff1133",
            corner_radius=15,
            command=self._clear_image
        )
        
        # Drag and Drop Support
        if HAS_DND:
            self.sender_image_label.drop_target_register(DND_FILES)
            self.sender_image_label.dnd_bind("<<Drop>>", self._on_drop)
        
        # Browse Button
        browse_btn = ctk.CTkButton(
            left_panel,
            text="📁 SELECT IMAGE FILE",
            command=self._browse_image,
            height=45,
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color=COLORS["accent_purple"],
            hover_color=COLORS["accent_magenta"],
            corner_radius=8
        )
        browse_btn.pack(padx=15, pady=(15, 5), fill="x")
        
        # Capacity Info Label
        self.capacity_label = ctk.CTkLabel(
            left_panel,
            text="",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLORS["text_secondary"]
        )
        self.capacity_label.pack(padx=15, pady=(0, 10))
        
        # Right Panel - MESSAGE & NETWORK
        right_panel = ctk.CTkFrame(
            main_frame, 
            fg_color=COLORS["bg_dark"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["accent_cyan"]
        )
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)
        
        # Secret Message Section
        msg_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        msg_header.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            msg_header, 
            text="🔐 SECRET MESSAGE",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color=COLORS["accent_cyan"]
        ).pack(side="left")

        # Refresh Button (Sender)
        self.refresh_sender_btn = ctk.CTkButton(
            msg_header,
            text="↻",
            width=30,
            height=30,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_card_hover"],
            text_color=COLORS["accent_cyan"],
            corner_radius=15,
            command=self._reset_sender_tab
        )
        self.refresh_sender_btn.pack(side="right", padx=5)
        
        self.char_count_label = ctk.CTkLabel(
            msg_header,
            text="0 chars",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLORS["text_secondary"]
        )
        self.char_count_label.pack(side="right")
        
        # Message textbox with custom styling
        self.message_textbox = ctk.CTkTextbox(
            right_panel, 
            height=100,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["accent_cyan"],
            corner_radius=8
        )
        self.message_textbox.pack(fill="x", padx=15, pady=5)
        self.message_textbox.insert("0.0", "")
        self.message_textbox.bind("<KeyRelease>", self._update_char_count)
        
        # Password Encryption Section
        password_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        password_frame.pack(fill="x", padx=15, pady=(5, 0))
        
        ctk.CTkLabel(
            password_frame, 
            text="🔑 PASSWORD (Optional):",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLORS["accent_magenta"]
        ).pack(side="left")
        
        self.sender_password_entry = ctk.CTkEntry(
            password_frame, 
            placeholder_text="Encryption key",
            width=150,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=COLORS["bg_card"],
            border_color=COLORS["accent_magenta"],
            show="•"
        )
        self.sender_password_entry.pack(side="left", padx=10)
        
        self.show_pass_var = ctk.BooleanVar(value=False)
        self.show_pass_btn = ctk.CTkCheckBox(
            password_frame,
            text="Show",
            variable=self.show_pass_var,
            command=self._toggle_password_visibility,
            font=ctk.CTkFont(family="Consolas", size=10),
            checkbox_width=18,
            checkbox_height=18
        )
        self.show_pass_btn.pack(side="left")
        
        # Encode Button
        self.encode_btn = ctk.CTkButton(
            right_panel,
            text="🔒 ENCODE MESSAGE",
            command=self._encode_message,
            height=45,
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color=COLORS["accent_green"],
            hover_color="#00cc70",
            text_color=COLORS["bg_dark"],
            corner_radius=8
        )
        self.encode_btn.pack(padx=15, pady=(10, 15), fill="x")
        
        # Network Section
        network_frame = ctk.CTkFrame(
            right_panel,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["accent_orange"]
        )
        network_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            network_frame, 
            text="🌐 TARGET COORDINATES",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=COLORS["accent_orange"]
        ).pack(pady=(10, 5))
        
        # IP Input Row
        ip_frame = ctk.CTkFrame(network_frame, fg_color="transparent")
        ip_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            ip_frame, 
            text="IP:",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=(0, 5))
        
        self.target_ip_entry = ctk.CTkEntry(
            ip_frame, 
            placeholder_text="xxx.xxx.xxx.xxx",
            width=150,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["accent_orange"]
        )
        self.target_ip_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(
            ip_frame, 
            text="PORT:",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=(15, 5))
        
        self.target_port_entry = ctk.CTkEntry(
            ip_frame, 
            placeholder_text="5001",
            width=80,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["accent_orange"]
        )
        self.target_port_entry.pack(side="left", padx=5)
        self.target_port_entry.insert(0, str(DEFAULT_PORT))
        
        # Ping Test Button
        self.ping_btn = ctk.CTkButton(
            ip_frame,
            text="📡 PING",
            command=self._ping_target,
            width=70,
            height=28,
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            fg_color=COLORS["accent_purple"],
            hover_color=COLORS["accent_magenta"],
            corner_radius=5
        )
        self.ping_btn.pack(side="left", padx=(15, 0))
        
        # Ping Status
        self.ping_status = ctk.CTkLabel(
            network_frame,
            text="",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLORS["text_secondary"]
        )
        self.ping_status.pack(pady=(0, 5))
        
        # Progress Bar
        self.progress_frame = ctk.CTkFrame(network_frame, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=15, pady=5)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="READY",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color=COLORS["text_secondary"]
        )
        self.progress_label.pack(side="left", padx=(0, 10))
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=200,
            height=12,
            corner_radius=6,
            progress_color=COLORS["accent_cyan"],
            fg_color=COLORS["bg_dark"]
        )
        self.progress_bar.pack(side="left", fill="x", expand=True)
        self.progress_bar.set(0)
        
        self.progress_percent = ctk.CTkLabel(
            self.progress_frame,
            text="0%",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color=COLORS["accent_cyan"]
        )
        self.progress_percent.pack(side="left", padx=(10, 0))
        
        # Send Button
        self.send_btn = ctk.CTkButton(
            network_frame,
            text="📤 TRANSMIT PAYLOAD",
            command=self._send_file,
            height=45,
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color=COLORS["accent_orange"],
            hover_color="#ff8855",
            text_color=COLORS["bg_dark"],
            corner_radius=8,
            state="disabled"
        )
        self.send_btn.pack(padx=15, pady=15, fill="x")
        
        # Log Section
        log_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        log_header.pack(fill="x", padx=15, pady=(5, 0))
        
        ctk.CTkLabel(
            log_header, 
            text="📋 TRANSMISSION LOG",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        
        self.sender_log = ctk.CTkTextbox(
            right_panel, 
            height=150, 
            state="disabled",
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=COLORS["bg_dark"],
            corner_radius=5
        )
        self.sender_log.pack(fill="x", padx=15, pady=(5, 15))
    
    def _update_char_count(self, event=None):
        """Update character count"""
        text = self.message_textbox.get("0.0", "end").strip()
        self.char_count_label.configure(text=f"{len(text)} chars")
    
    def _toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.show_pass_var.get():
            self.sender_password_entry.configure(show="")
        else:
            self.sender_password_entry.configure(show="•")
    
    def _ping_target(self):
        """Test connection to target"""
        target_ip = self.target_ip_entry.get().strip()
        if not target_ip:
            self.ping_status.configure(text="⚠️ Enter IP first", text_color=COLORS["warning"])
            return
        
        try:
            port = int(self.target_port_entry.get().strip() or DEFAULT_PORT)
        except ValueError:
            port = DEFAULT_PORT
        
        self.ping_status.configure(text="📡 Testing...", text_color=COLORS["accent_cyan"])
        self.ping_btn.configure(state="disabled")
        self.update()
        
        # Run ping in thread
        def do_ping():
            result = ping_host(target_ip, port)
            self.after(0, lambda: self._ping_result(result, target_ip, port))
        
        thread = threading.Thread(target=do_ping)
        thread.daemon = True
        thread.start()
    
    def _ping_result(self, success, ip, port):
        """Handle ping result"""
        self.ping_btn.configure(state="normal")
        if success:
            self.ping_status.configure(
                text=f"✅ {ip}:{port} ONLINE", 
                text_color=COLORS["success"]
            )
            play_sound("success")
        else:
            self.ping_status.configure(
                text=f"❌ {ip}:{port} UNREACHABLE", 
                text_color=COLORS["error"]
            )
            play_sound("error")
    
    def _on_drop(self, event):
        """Handle file drop event"""
        filepath = event.data
        if filepath:
            # Clean up filepath (remove {} if present from tkinterdnd)
            if filepath.startswith("{") and filepath.endswith("}"):
                filepath = filepath[1:-1]
            
            if os.path.isfile(filepath):
                # Check extension
                ext = os.path.splitext(filepath)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.bmp']:
                    self.selected_image_path = filepath
                    self._display_image(filepath, self.sender_image_label, (280, 200))
                    self._log_sender(f"[+] Dropped: {os.path.basename(filepath)}")
                    self._update_status(f"Payload loaded: {os.path.basename(filepath)}")
                    self.image_status_indicator.configure(text="● LOADED", text_color=COLORS["success"])
                    
                    # Show remove button
                    self.remove_img_btn.place(relx=1.0, x=-10, y=10, anchor="ne")
                    
                    # Show capacity info
                    max_chars, width, height = estimate_capacity(filepath)
                    file_size = os.path.getsize(filepath)
                    self.capacity_label.configure(
                        text=f"📐 {width}x{height} | 💾 {format_size(file_size)} | 📝 ~{max_chars:,} chars max"
                    )
                else:
                    messagebox.showwarning("⚠️ Invalid File", "Please drop an image file (PNG, JPG, BMP)")
    
    def _clear_image(self):
        """Clear selected image"""
        self.selected_image_path = None
        
        # Create a transparent 1x1 image to force clear
        empty_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        empty_ctk = ctk.CTkImage(light_image=empty_img, dark_image=empty_img, size=(1, 1))
        
        self.sender_image_label.configure(text="[ NO IMAGE LOADED ]\n\n⬇ DROP OR BROWSE ⬇", image=empty_ctk)
        self.sender_image_label._image = empty_ctk # Keep reference
        
        self.image_status_indicator.configure(text="● AWAITING", text_color=COLORS["warning"])
        self.capacity_label.configure(text="")
        self._log_sender("[-] Image cleared")
        self._update_status("Payload cleared")
        
        # Hide remove button
        self.remove_img_btn.place_forget()

    def _reset_sender_tab(self):
        """Reset Sender Tab to default state"""
        self._clear_image()
        self.message_textbox.delete("0.0", "end")
        self._update_char_count()
        self.sender_password_entry.delete(0, "end")
        self.target_ip_entry.delete(0, "end")
        self.target_port_entry.delete(0, "end")
        self.target_port_entry.insert(0, str(DEFAULT_PORT))
        self.ping_status.configure(text="")
        self.progress_bar.set(0)
        self.progress_percent.configure(text="0%")
        self.progress_label.configure(text="READY")
        self.send_btn.configure(state="disabled")
        self._log_sender("[*] Sender tab reset")
        play_sound("click")

    def _browse_image(self):
        """Open file dialog to select image"""
        filepath = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp"), ("All Files", "*.*")]
        )
        if filepath:
            self.selected_image_path = filepath
            self._display_image(filepath, self.sender_image_label, (280, 200))
            self._log_sender(f"[+] Loaded: {os.path.basename(filepath)}")
            self._update_status(f"Payload loaded: {os.path.basename(filepath)}")
            self.image_status_indicator.configure(text="● LOADED", text_color=COLORS["success"])
            
            # Show remove button
            self.remove_img_btn.place(relx=1.0, x=-10, y=10, anchor="ne")
            
            # Show capacity info
            max_chars, width, height = estimate_capacity(filepath)
            file_size = os.path.getsize(filepath)
            self.capacity_label.configure(
                text=f"📐 {width}x{height} | 💾 {format_size(file_size)} | 📝 ~{max_chars:,} chars max"
            )
    
    def _display_image(self, path, label, size):
        """Display image in a label"""
        try:
            img = Image.open(path)
            img.thumbnail(size)
            photo = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            label.configure(image=photo, text="")
            label.image = photo
        except Exception as e:
            label.configure(text=f"[ERROR]\n{e}")
    
    def _encode_message(self):
        """Encode secret message into the selected image"""
        if not self.selected_image_path:
            messagebox.showwarning("⚠️ Warning", "Select an image first!")
            return
        
        message = self.message_textbox.get("0.0", "end").strip()
        if not message:
            messagebox.showwarning("⚠️ Warning", "Enter a secret message!")
            return
        
        try:
            self._log_sender("[~] Encoding message...")
            self._update_status("Encoding payload...")
            
            # Get password and encrypt if provided
            password = self.sender_password_entry.get().strip()
            if password:
                message = encrypt_message(message, password)
                self._log_sender("[+] Message encrypted with password")
            
            # Use LSB steganography
            secret_image = lsb.hide(self.selected_image_path, message)
            output_path = os.path.join(os.path.dirname(self.selected_image_path), "secret_packet.png")
            secret_image.save(output_path)
            
            self.encoded_image_path = output_path
            self._log_sender(f"[✓] Encoded: secret_packet.png")
            self._update_status("Message encoded successfully!")
            self.send_btn.configure(state="normal")
            play_sound("success")
            
            enc_status = " (Encrypted)" if password else ""
            messagebox.showinfo("✅ Success", f"Message encoded{enc_status}!\nSaved as: secret_packet.png")
            
        except Exception as e:
            self._log_sender(f"[✗] Error: {e}")
            play_sound("error")
            messagebox.showerror("❌ Error", f"Failed to encode: {e}")
    
    def _send_file(self):
        """Send the encoded file to receiver"""
        if not self.encoded_image_path:
            messagebox.showwarning("⚠️ Warning", "Encode a message first!")
            return
        
        target_ip = self.target_ip_entry.get().strip()
        if not target_ip:
            messagebox.showwarning("⚠️ Warning", "Enter target IP address!")
            return
        
        try:
            port = int(self.target_port_entry.get().strip() or DEFAULT_PORT)
        except ValueError:
            port = DEFAULT_PORT
        
        # Run in thread to prevent UI freeze
        thread = threading.Thread(target=self._send_file_thread, args=(target_ip, port))
        thread.daemon = True
        thread.start()
    
    def _send_file_thread(self, target_ip, port):
        """Thread function to send file with progress bar"""
        try:
            self._log_sender(f"[~] Connecting to {target_ip}:{port}...")
            self._update_status(f"Establishing connection...")
            self.after(0, lambda: self.progress_label.configure(text="CONNECTING"))
            self.after(0, lambda: self.progress_bar.set(0.1))
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((target_ip, port))
            
            self._log_sender("[+] Connected! Transmitting...")
            self.after(0, lambda: self.progress_label.configure(text="TRANSMITTING"))
            
            filesize = os.path.getsize(self.encoded_image_path)
            filename = os.path.basename(self.encoded_image_path)
            
            # Send header
            s.send(f"{filename}{SEPARATOR}{filesize}".encode())
            time.sleep(0.5)
            
            # Send file with progress
            bytes_sent = 0
            with open(self.encoded_image_path, "rb") as f:
                while True:
                    bytes_read = f.read(BUFFER_SIZE)
                    if not bytes_read:
                        break
                    s.sendall(bytes_read)
                    bytes_sent += len(bytes_read)
                    # Update progress
                    progress = bytes_sent / filesize
                    percent = int(progress * 100)
                    self.after(0, lambda p=progress: self.progress_bar.set(p))
                    self.after(0, lambda pct=percent: self.progress_percent.configure(text=f"{pct}%"))
            
            self._log_sender("[✓] Transmission complete!")
            self._update_status("Payload transmitted!")
            self.after(0, lambda: self.progress_label.configure(text="COMPLETE"))
            self.after(0, lambda: self.progress_bar.set(1.0))
            self.after(0, lambda: self.progress_percent.configure(text="100%"))
            s.close()
            
            play_sound("send")
            self.after(0, lambda: messagebox.showinfo("✅ Success", "Payload transmitted successfully!"))
            
        except socket.timeout:
            self._log_sender("[✗] Connection timeout!")
            self._update_status("Connection timeout")
            self.after(0, lambda: self.progress_label.configure(text="FAILED"))
            self.after(0, lambda: self.progress_bar.set(0))
            play_sound("error")
            self.after(0, lambda: messagebox.showerror("❌ Error", "Connection timeout!\nMake sure receiver is running."))
        except ConnectionRefusedError:
            self._log_sender("[✗] Connection refused!")
            self._update_status("Connection refused")
            self.after(0, lambda: self.progress_label.configure(text="FAILED"))
            self.after(0, lambda: self.progress_bar.set(0))
            play_sound("error")
            self.after(0, lambda: messagebox.showerror("❌ Error", "Connection refused!\nMake sure receiver is running."))
        except Exception as e:
            self._log_sender(f"[✗] Error: {e}")
            self._update_status("Transmission failed")
            self.after(0, lambda: self.progress_label.configure(text="ERROR"))
            self.after(0, lambda: self.progress_bar.set(0))
            play_sound("error")
            self.after(0, lambda: messagebox.showerror("❌ Error", f"Failed to send: {e}"))
    
    def _log_sender(self, text):
        """Add text to sender log"""
        self.sender_log.configure(state="normal")
        self.sender_log.insert("end", f"{text}\n")
        self.sender_log.see("end")
        self.sender_log.configure(state="disabled")
    
    # ==================== RECEIVER TAB ====================
    def _build_receiver_tab(self):
        """Build the Receiver tab UI with gaming style"""
        main_frame = ctk.CTkFrame(self.receiver_frame, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)
        
        # Top Section - Server Controls
        control_frame = ctk.CTkFrame(
            main_frame,
            fg_color=COLORS["bg_dark"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["accent_magenta"]
        )
        control_frame.pack(fill="x", pady=(0, 10))
        
        # Server Status with gaming style
        status_container = ctk.CTkFrame(control_frame, fg_color="transparent")
        status_container.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(
            status_container, 
            text="SERVER STATUS:",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=5)
        
        self.server_status_indicator = ctk.CTkLabel(
            status_container,
            text="● OFFLINE",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color=COLORS["error"]
        )
        self.server_status_indicator.pack(side="left", padx=5)
        
        # Server Buttons
        btn_container = ctk.CTkFrame(control_frame, fg_color="transparent")
        btn_container.pack(side="right", padx=20, pady=15)
        
        self.start_server_btn = ctk.CTkButton(
            btn_container,
            text="▶ START LISTENING",
            command=self._start_server,
            width=160,
            height=40,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            fg_color=COLORS["accent_green"],
            hover_color="#00cc70",
            text_color=COLORS["bg_dark"],
            corner_radius=8
        )
        self.start_server_btn.pack(side="left", padx=5)
        
        self.stop_server_btn = ctk.CTkButton(
            btn_container,
            text="■ STOP SERVER",
            command=self._stop_server,
            width=140,
            height=40,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_card_hover"],
            text_color=COLORS["error"],
            border_width=1,
            border_color=COLORS["error"],
            corner_radius=8,
            state="disabled"
        )
        self.stop_server_btn.pack(side="left", padx=5)
        
        # QR Code Button
        self.qr_btn = ctk.CTkButton(
            btn_container,
            text="📱 QR",
            command=self._show_qr_code,
            width=60,
            height=40,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            fg_color=COLORS["accent_purple"],
            hover_color=COLORS["accent_magenta"],
            corner_radius=8
        )
        self.qr_btn.pack(side="left", padx=5)
        
        # Middle Section
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Left - Received Image
        left_panel = ctk.CTkFrame(
            content_frame,
            fg_color=COLORS["bg_dark"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["accent_purple"]
        )
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        
        # Header
        header_left = ctk.CTkFrame(left_panel, fg_color="transparent")
        header_left.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header_left, 
            text="📷 RECEIVED PAYLOAD",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color=COLORS["accent_purple"]
        ).pack(side="left")

        # Refresh Button (Receiver)
        self.refresh_receiver_btn = ctk.CTkButton(
            header_left,
            text="↻",
            width=30,
            height=30,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_card_hover"],
            text_color=COLORS["accent_purple"],
            corner_radius=15,
            command=self._reset_receiver_tab
        )
        self.refresh_receiver_btn.pack(side="right", padx=5)
        
        self.receiver_status_indicator = ctk.CTkLabel(
            header_left,
            text="● WAITING",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLORS["warning"]
        )
        self.receiver_status_indicator.pack(side="right")
        
        # Image container
        image_container = ctk.CTkFrame(
            left_panel,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=2,
            border_color=COLORS["accent_purple"]
        )
        image_container.pack(padx=15, pady=10, fill="both", expand=True)
        
        self.receiver_image_label = ctk.CTkLabel(
            image_container,
            text="[ AWAITING INCOMING DATA ]\n\n📡 Start server to listen",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=COLORS["text_secondary"],
            corner_radius=10
        )
        # Fix height for image container (min height 400px)
        self.receiver_image_label.pack(fill="both", expand=True, padx=10, pady=10, ipady=180)
        
        # Password for decryption
        recv_password_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        recv_password_frame.pack(fill="x", padx=15, pady=(5, 0))
        
        ctk.CTkLabel(
            recv_password_frame, 
            text="🔑 PASSWORD:",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLORS["accent_magenta"]
        ).pack(side="left")
        
        self.receiver_password_entry = ctk.CTkEntry(
            recv_password_frame, 
            placeholder_text="Decryption key",
            width=150,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=COLORS["bg_card"],
            border_color=COLORS["accent_magenta"],
            show="•"
        )
        self.receiver_password_entry.pack(side="left", padx=10)
        
        self.recv_show_pass_var = ctk.BooleanVar(value=False)
        self.recv_show_pass_btn = ctk.CTkCheckBox(
            recv_password_frame,
            text="Show",
            variable=self.recv_show_pass_var,
            command=self._toggle_receiver_password_visibility,
            font=ctk.CTkFont(family="Consolas", size=10),
            checkbox_width=18,
            checkbox_height=18
        )
        self.recv_show_pass_btn.pack(side="left")
        
        # Reveal Button
        self.reveal_btn = ctk.CTkButton(
            left_panel,
            text="🔓 DECRYPT MESSAGE",
            command=self._reveal_message,
            height=45,
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color=COLORS["accent_purple"],
            hover_color=COLORS["accent_magenta"],
            corner_radius=8,
            state="disabled"
        )
        self.reveal_btn.pack(padx=15, pady=15, fill="x")
        
        # Right - Message & Log
        right_panel = ctk.CTkFrame(
            content_frame,
            fg_color=COLORS["bg_dark"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["accent_cyan"]
        )
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)
        
        # Revealed Message Header
        ctk.CTkLabel(
            right_panel, 
            text="💬 DECRYPTED MESSAGE",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color=COLORS["accent_cyan"]
        ).pack(pady=(15, 10), padx=15, anchor="w")
        
        self.revealed_message_box = ctk.CTkTextbox(
            right_panel, 
            height=200, 
            state="disabled",
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["accent_cyan"],
            corner_radius=8
        )
        self.revealed_message_box.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            right_panel, 
            text="📋 CONNECTION LOG",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLORS["text_secondary"]
        ).pack(pady=(20, 5), anchor="w", padx=15)
        
        self.receiver_log = ctk.CTkTextbox(
            right_panel, 
            height=150, 
            state="disabled",
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=COLORS["bg_dark"],
            corner_radius=5
        )
        self.receiver_log.pack(fill="both", padx=15, pady=(0, 15), expand=True)
    
    def _start_server(self):
        """Start the receiver server"""
        self.server_running = True
        self.start_server_btn.configure(state="disabled")
        self.stop_server_btn.configure(state="normal")
        self.server_status_indicator.configure(text="● LISTENING", text_color=COLORS["accent_green"])
        self._update_status(f"Server listening on port {DEFAULT_PORT}")
        
        # Start server in thread
        thread = threading.Thread(target=self._server_thread)
        thread.daemon = True
        thread.start()
        
        self._log_receiver(f"[+] Server started on {get_local_ip()}:{DEFAULT_PORT}")
    
    def _show_qr_code(self):
        """Show QR code with IP:Port for easy sharing"""
        if not HAS_QRCODE:
            messagebox.showinfo("ℹ️ Info", "QR Code library not installed.\nInstall with: pip install qrcode[pil]")
            return
        
        ip = get_local_ip()
        data = f"{ip}:{DEFAULT_PORT}"
        qr_img = generate_qr_code(data)
        
        if qr_img:
            # Create popup window
            qr_window = ctk.CTkToplevel(self)
            qr_window.title("📱 Connection QR Code")
            qr_window.geometry("280x350")
            qr_window.configure(fg_color=COLORS["bg_dark"])
            qr_window.resizable(False, False)
            
            ctk.CTkLabel(
                qr_window,
                text="📡 SCAN TO CONNECT",
                font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
                text_color=COLORS["accent_cyan"]
            ).pack(pady=(20, 10))
            
            # Convert PIL image to CTk
            qr_photo = ctk.CTkImage(light_image=qr_img, dark_image=qr_img, size=(180, 180))
            qr_label = ctk.CTkLabel(qr_window, image=qr_photo, text="")
            qr_label.pack(pady=10)
            
            ctk.CTkLabel(
                qr_window,
                text=data,
                font=ctk.CTkFont(family="Consolas", size=16, weight="bold"),
                text_color=COLORS["accent_magenta"]
            ).pack(pady=5)
            
            ctk.CTkButton(
                qr_window,
                text="CLOSE",
                command=qr_window.destroy,
                fg_color=COLORS["accent_purple"],
                hover_color=COLORS["accent_magenta"],
                width=100
            ).pack(pady=15)
            
            qr_window.grab_set()
    
    def _reset_receiver_tab(self):
        """Reset Receiver Tab to default state"""
        # Create a transparent 1x1 image to force clear
        empty_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        empty_ctk = ctk.CTkImage(light_image=empty_img, dark_image=empty_img, size=(1, 1))
        
        self.receiver_image_label.configure(
            text="[ AWAITING INCOMING DATA ]\n\n📡 Start server to listen", 
            image=empty_ctk
        )
        self.receiver_image_label._image = empty_ctk
        
        self.receiver_password_entry.delete(0, "end")
        self.revealed_message_box.configure(state="normal")
        self.revealed_message_box.delete("0.0", "end")
        self.revealed_message_box.configure(state="disabled")
        
        self.receiver_status_indicator.configure(text="● WAITING", text_color=COLORS["warning"])
        self.reveal_btn.configure(state="disabled")
        
        self._log_receiver("[*] Receiver tab reset")
        play_sound("click")
    
    def _stop_server(self):
        """Stop the receiver server"""
        self.server_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        self.start_server_btn.configure(state="normal")
        self.stop_server_btn.configure(state="disabled")
        self.server_status_indicator.configure(text="● OFFLINE", text_color=COLORS["error"])
        self._update_status("Server stopped")
        self._log_receiver("[!] Server stopped")
    
    def _server_thread(self):
        """Thread function to run server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", DEFAULT_PORT))
            self.server_socket.listen(1)
            self.server_socket.settimeout(1)
            
            while self.server_running:
                try:
                    client_socket, address = self.server_socket.accept()
                    self._log_receiver(f"[+] Connection from {address[0]}")
                    self._update_status(f"Receiving from {address[0]}...")
                    
                    # Receive header
                    received = client_socket.recv(BUFFER_SIZE).decode()
                    filename, filesize = received.split(SEPARATOR)
                    filename = "received_" + os.path.basename(filename)
                    filesize = int(filesize)
                    
                    self._log_receiver(f"[~] Receiving: {filename} ({filesize} bytes)")
                    
                    output_path = os.path.join(os.getcwd(), filename)
                    with open(output_path, "wb") as f:
                        bytes_received = 0
                        while bytes_received < filesize:
                            bytes_read = client_socket.recv(BUFFER_SIZE)
                            if not bytes_read:
                                break
                            f.write(bytes_read)
                            bytes_received += len(bytes_read)
                    
                    client_socket.close()
                    
                    self.received_image_path = output_path
                    self._log_receiver(f"[✓] Saved: {filename}")
                    self._update_status("Payload received!")
                    
                    # Update UI
                    self.after(0, lambda p=output_path: self._display_image(p, self.receiver_image_label, (280, 200)))
                    self.after(0, lambda: self.reveal_btn.configure(state="normal"))
                    self.after(0, lambda: self.receiver_status_indicator.configure(text="● RECEIVED", text_color=COLORS["success"]))
                    self.after(0, lambda: messagebox.showinfo("📥 Received", f"Payload received: {filename}"))
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.server_running:
                        self._log_receiver(f"[!] Error: {e}")
        
        except Exception as e:
            self._log_receiver(f"[✗] Server error: {e}")
        finally:
            if self.server_socket:
                try:
                    self.server_socket.close()
                except:
                    pass
    
    def _toggle_receiver_password_visibility(self):
        """Toggle receiver password visibility"""
        if self.recv_show_pass_var.get():
            self.receiver_password_entry.configure(show="")
        else:
            self.receiver_password_entry.configure(show="•")
    
    def _reveal_message(self):
        """Reveal the hidden message from received image"""
        if not self.received_image_path:
            messagebox.showwarning("⚠️ Warning", "No payload received yet!")
            return
        
        try:
            self._log_receiver("[~] Extracting message...")
            self._update_status("Decrypting...")
            
            message = lsb.reveal(self.received_image_path)
            
            if message:
                # Check if message is encrypted and decrypt if password provided
                password = self.receiver_password_entry.get().strip()
                if message.startswith("ENC:"):
                    if password:
                        message = decrypt_message(message, password)
                        self._log_receiver("[+] Message decrypted with password")
                    else:
                        self._log_receiver("[!] Encrypted message - password required")
                        message = "[🔒 ENCRYPTED MESSAGE]\n\nEnter the password and click Decrypt again."
                
                self.revealed_message_box.configure(state="normal")
                self.revealed_message_box.delete("0.0", "end")
                self.revealed_message_box.insert("0.0", message)
                self.revealed_message_box.configure(state="disabled")
                
                self._log_receiver("[✓] Message revealed!")
                self._update_status("Message revealed!")
                play_sound("success")
            else:
                messagebox.showinfo("ℹ️ Info", "No hidden message found.")
                
        except Exception as e:
            self._log_receiver(f"[✗] Error: {e}")
            play_sound("error")
            messagebox.showerror("❌ Error", f"Decryption failed: {e}")
    
    def _log_receiver(self, text):
        """Add text to receiver log"""
        self.receiver_log.configure(state="normal")
        self.receiver_log.insert("end", f"{text}\n")
        self.receiver_log.see("end")
        self.receiver_log.configure(state="disabled")
    
    # ==================== ABOUT TAB ====================
    def _build_about_tab(self):
        """Build the About tab UI with gaming style"""
        frame = ctk.CTkFrame(self.about_frame, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Center content
        center_frame = ctk.CTkFrame(frame, fg_color="transparent")
        center_frame.pack(expand=True)
        
        # Logo with glow effect simulation
        logo_frame = ctk.CTkFrame(
            center_frame,
            fg_color=COLORS["bg_card"],
            corner_radius=20,
            border_width=3,
            border_color=COLORS["accent_cyan"]
        )
        logo_frame.pack(pady=20)
        
        ctk.CTkLabel(
            logo_frame, 
            text="◈",
            font=ctk.CTkFont(size=80, weight="bold"),
            text_color=COLORS["accent_cyan"]
        ).pack(padx=30, pady=20)
        
        # App Name
        ctk.CTkLabel(
            center_frame, 
            text="STEGOVERT", 
            font=ctk.CTkFont(family="Consolas", size=36, weight="bold"),
            text_color=COLORS["accent_cyan"]
        ).pack(pady=(10, 0))
        
        ctk.CTkLabel(
            center_frame,
            text="COVERT MESSAGE SYSTEM",
            font=ctk.CTkFont(family="Consolas", size=14),
            text_color=COLORS["accent_magenta"]
        ).pack(pady=5)
        
        ctk.CTkLabel(
            center_frame,
            text=f"VERSION {APP_VERSION}",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLORS["text_secondary"]
        ).pack(pady=10)
        
        # Description Card
        desc_frame = ctk.CTkFrame(
            center_frame,
            fg_color=COLORS["bg_dark"],
            corner_radius=15,
            border_width=1,
            border_color=COLORS["accent_purple"]
        )
        desc_frame.pack(fill="x", pady=20, padx=20)
        
        desc_text = """
STEGOVERT adalah aplikasi steganografi tingkat lanjut 
untuk menyembunyikan pesan rahasia di dalam gambar 
menggunakan teknik LSB (Least Significant Bit) 
dan mengirimnya melalui jaringan TCP.

╔═══════════════════════════════════════╗
║  TRANSMIT : Pilih gambar → Encode → Kirim  ║
║  RECEIVE  : Start Server → Terima → Decrypt ║
╚═══════════════════════════════════════╝

⚠️ Pastikan kedua perangkat terhubung ke jaringan yang sama!
        """
        
        ctk.CTkLabel(
            desc_frame,
            text=desc_text,
            font=ctk.CTkFont(family="Consolas", size=12),
            justify="center",
            text_color=COLORS["text_primary"]
        ).pack(pady=20, padx=20)
        
        # Credits
        ctk.CTkLabel(
            center_frame,
            text="[ DEVELOPED WITH PYTHON & CUSTOMTKINTER ]",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLORS["text_secondary"]
        ).pack(pady=15)
    
    # ==================== STATUS BAR ====================
    def _create_status_bar(self):
        """Create gaming-style status bar"""
        status_frame = ctk.CTkFrame(
            self, 
            height=35, 
            corner_radius=0,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["accent_cyan"]
        )
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)
        
        # Left status
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="⚡ SYSTEM READY",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLORS["accent_green"]
        )
        self.status_label.pack(side="left", padx=15, pady=8)
        
        # Right version
        version_label = ctk.CTkLabel(
            status_frame,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLORS["text_secondary"]
        )
        version_label.pack(side="right", padx=15, pady=8)
        
        # Center decoration
        deco_label = ctk.CTkLabel(
            status_frame,
            text="══════════════════════════════════════════════════════════════════",
            font=ctk.CTkFont(family="Consolas", size=8),
            text_color=COLORS["accent_cyan"]
        )
        deco_label.pack(expand=True, pady=12)
    
    def _update_status(self, text):
        """Update status bar text"""
        self.status_label.configure(text=f"⚡ {text.upper()}")
    
    def _on_closing(self):
        """Handle window close event"""
        self.animation_running = False
        if self.server_running:
            self._stop_server()
        self.destroy()


# ===================== MAIN =====================
if __name__ == "__main__":
    app = StegovertApp()
    app.mainloop()
