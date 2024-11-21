from flask import Flask, render_template
import os

app = Flask(__name__)

# Log lokasi folder templates dan static
print("Templates folder:", os.path.join(app.root_path, 'templates'))
print("Static folder:", os.path.join(app.root_path, 'static'))

@app.route("/")
def home():
    return render_template("home.html")  # Halaman Home

@app.route("/about")
def about():
    return render_template("about.html")  # Halaman Tentang Kami

@app.route("/products")
def products():
    return render_template("products.html")  # Halaman Produk

@app.route("/contact")
def contact():
    return render_template("contact.html")  # Halaman Kontak

if __name__ == "__main__":
    app.run(debug=True)