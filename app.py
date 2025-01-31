import os
import subprocess
import time
import json
import sys
import platform
import socket
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
import threading

# Konstanta
NGROK_PATH = r"C:\\Program Files\\ngrok\\ngrok.exe"
USER_HOME = os.path.expanduser("~")
NGROK_CONFIG_PATH = os.path.join(USER_HOME, "AppData", "Local", "ngrok", "ngrok.yml")
FLASK_PORT = 5001
LOG_FILE = os.path.join(USER_HOME, "flask_ngrok_activator.log")
MAX_RETRIES = 3

# Inisialisasi Flask
app = Flask(__name__)
app.secret_key = "your_secret_key"

# Komentar yang akan disimpan sementara (sebagai contoh)
messages = []

# Utility Functions
def log_message(level, message, exception=None):
    """Log messages with levels and optional exception details."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"[{timestamp}] {level}: {message}\n")
        if exception:
            log.write(f"DETAIL: {exception}\n")
    print(f"\n{level}: {message}")
    if exception:
        print(f"🔍 Detail Error: {exception}")

def find_available_port(start_port=5001):
    """Find an available port starting from a given port."""
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", start_port)) != 0:
                return start_port
            start_port += 1

def check_internet():
    """Check internet connection."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False

def install_dependencies():
    """Install missing Python dependencies."""
    print("\n🔧 Memeriksa dan menginstal dependensi yang hilang...")
    dependencies = ["flask", "requests", "elevate"]
    for dep in dependencies:
        try:
            __import__(dep)
        except ImportError:
            print(f"📦 Modul {dep} tidak ditemukan. Menginstal {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

def download_ngrok():
    """Download dan siapkan Ngrok jika tidak ditemukan."""
    import requests
    ngrok_url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-stable-windows-amd64.zip"
    download_path = os.path.join(USER_HOME, "Downloads", "ngrok.zip")
    extract_dir = r"C:\\Program Files\\ngrok"

    if os.path.isfile(NGROK_PATH):
        print("✅ Ngrok ditemukan.")
        return  # Ngrok sudah ada

    try:
        print(f"🔗 Mengunduh Ngrok dari: {ngrok_url}")
        response = requests.get(ngrok_url, stream=True)
        response.raise_for_status()

        # Simpan file ZIP
        with open(download_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        # Ekstrak file ZIP
        import zipfile
        with zipfile.ZipFile(download_path, "r") as zip_ref:
            os.makedirs(extract_dir, exist_ok=True)
            zip_ref.extractall(extract_dir)

        print(f"✅ Ngrok berhasil diekstrak ke {extract_dir}")
    except Exception as e:
        log_message("ERROR", "Gagal mengunduh atau mengekstrak Ngrok.", e)

def start_ngrok():
    """Mulai Ngrok."""
    print("🚀 Memulai Ngrok...")
    try:
        ngrok_process = subprocess.Popen(
            [NGROK_PATH, "http", str(FLASK_PORT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        time.sleep(5)  # Beri waktu untuk Ngrok memulai
        return ngrok_process
    except Exception as e:
        log_message("ERROR", "Gagal memulai Ngrok.", e)
        return None

def get_ngrok_url(ngrok_process):
    """Get ngrok public URL dengan retry."""
    import requests
    retries = 0

    while retries < MAX_RETRIES:
        try:
            response = requests.get("http://localhost:4040/api/tunnels")
            response_data = response.json()
            for tunnel in response_data.get("tunnels", []):
                if "http" in tunnel.get("public_url", ""):
                    return tunnel["public_url"]
            log_message("WARNING", "URL publik ngrok belum tersedia. Mencoba lagi...")
        except requests.ConnectionError as e:
            log_message("ERROR", "Gagal mendapatkan URL ngrok (koneksi gagal).", e)
        except Exception as e:
            log_message("ERROR", "Gagal mendapatkan URL ngrok.", e)
        retries += 1
        time.sleep(3)

    log_message("CRITICAL", "Tidak dapat mendapatkan URL publik Ngrok setelah beberapa percobaan. Memulai ulang ngrok...")
    # Restart ngrok process
    ngrok_process.terminate()
    return restart_ngrok()

def restart_ngrok():
    """Restart ngrok process dan coba kembali."""
    log_message("INFO", "Memulai ulang proses ngrok...")
    try:
        ngrok_process = start_ngrok()
        if not ngrok_process:
            log_message("CRITICAL", "Gagal memulai ulang Ngrok.")
            return None

        return get_ngrok_url(ngrok_process)
    except Exception as e:
        log_message("CRITICAL", "Gagal memulai ulang Ngrok.", e)
        return None

def monitor_exit(ngrok_process):
    """Monitor keyboard input untuk menghentikan Flask dan Ngrok."""
    while True:
        command = input("🖐 Tekan 'S' untuk menghentikan server: ").strip().lower()
        if command == "s":
            print("🛑 Menghentikan server Flask dan Ngrok...")
            ngrok_process.terminate()
            os._exit(0)  # Menghentikan Flask

# Global variable for cart items
cart_items = []

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/products")
def products():
    try:
        # Misalnya, kita mengambil data produk dari database atau variabel lain
        products_data = [
            {"id": 1, "name": "ColorWeave Bracelet", "price": 5000, "image": "bracelet1.jpg"},
            {"id": 2, "name": "ColorWeave Bracelet + Manik Manik", "price": 5000, "image": "bracelet2.jpg"}
        ]
        return render_template("products.html", products=products_data)
    except Exception as e:
        flash("❌ Terjadi kesalahan saat memuat halaman produk.", "error")
        log_message("ERROR", "Error rendering products page", e)
        return redirect(url_for("home"))


@app.route("/contact")
def contact():
    return render_template("contact.html", messages=messages)

@app.route("/submit_contact", methods=["POST"])
def submit_contact():
    name = request.form["name"]
    email = request.form["email"]
    message = request.form["message"]

    if not name or not email or not message:
        flash("❌ Semua bidang harus diisi!", "error")
        return redirect(url_for("contact"))

    messages.append({"name": name, "email": email, "message": message})

    with open("notepad.txt", "a", encoding="utf-8") as f:
        f.write(f"Name: {name}\nEmail: {email}\nMessage: {message}\n\n")
 
    flash("✅ Terima kasih atas pesan Anda! Kami akan segera menghubungi Anda.", "contact_success")  # Kategori 'contact_success'
    return redirect(url_for("contact"))

@app.route("/cart")
def cart():
    try:
        if not cart_items:
            flash("🛒 Keranjang Anda kosong!", "warning")

        cart_total = sum(item['price'] * item['quantity'] for item in cart_items)
        return render_template("cart.html", cart_items=cart_items, cart_total=cart_total)
    except Exception as e:
        log_message("ERROR", "Error rendering cart page", e)
        flash("❌ Terjadi kesalahan saat menampilkan keranjang.", "error")
        return redirect(url_for("home"))
    
@app.route("/update-cart/<int:item_id>", methods=["POST"])
def update_cart(item_id):
    quantity = int(request.form["quantity"])

    # Menemukan produk yang sesuai di cart_items
    product = next((item for item in cart_items if item["id"] == item_id), None)

    if product:
        # Memperbarui jumlah produk
        product["quantity"] = quantity
        flash("Jumlah produk berhasil diperbarui!", "success")
    else:
        flash("Produk tidak ditemukan di keranjang.", "error")

    return redirect(url_for("cart"))

@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    product_id = int(request.form.get("product_id"))
    product_data = {
        1: {"name": "ColorWeave Bracelet", "price": 5000, "image": "bracelet1.jpg"},
        2: {"name": "ColorWeave Bracelet + Manik Manik", "price": 5000, "image": "bracelet2.jpg"},
    }

    if product_id in product_data:
        product = next((item for item in cart_items if item["id"] == product_id), None)
        if product:
            product["quantity"] += 1
        else:
            cart_items.append({"id": product_id, "quantity": 1, **product_data[product_id]})
        flash("Produk berhasil ditambahkan ke keranjang!", "success")
    else:
        flash("Produk tidak ditemukan.", "error")

    return redirect(url_for("cart"))

@app.route("/remove-from-cart/<int:item_id>")
def remove_from_cart(item_id):
    global cart_items
    cart_items = [item for item in cart_items if item["id"] != item_id]
    flash("Item successfully removed from the cart.", "success")
    return redirect(url_for("cart"))


if __name__ == "__main__":
    if platform.system() != "Windows":
        log_message("ERROR", "Script ini hanya mendukung Windows.")
        exit(1)


    if not check_internet():
        log_message("ERROR", "Tidak ada koneksi internet. Periksa koneksi Anda.")
        exit(1)


    install_dependencies()
    download_ngrok()

    FLASK_PORT = find_available_port(FLASK_PORT)

    # Start Flask dan Ngrok
    flask_url = f"http://localhost:{FLASK_PORT}"
    print(f"⚡️ Flask berjalan di {flask_url}")
    ngrok_process = start_ngrok()
    ngrok_url = get_ngrok_url(ngrok_process)
    if ngrok_url:
        print(f"🌍 Ngrok berjalan di {ngrok_url}")
    else:
        log_message("CRITICAL", "Ngrok gagal berjalan.")

    # Start monitoring thread for exit
    threading.Thread(target=monitor_exit, args=(ngrok_process,), daemon=True).start()

    try:
        app.run(port=FLASK_PORT)
    except KeyboardInterrupt:
        print("\n❌ Program dihentikan.")
        ngrok_process.terminate()
