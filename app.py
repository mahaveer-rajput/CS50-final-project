from flask import Flask, render_template, request, redirect, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "mahaveer"  # REQUIRED for session

# Upload folder
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --------------------------
# Database connection helper
# --------------------------
def get_db_connection():
    conn = sqlite3.connect("gallery.db")
    conn.row_factory = sqlite3.Row
    return conn

# --------------------------
# Homepage
# --------------------------
@app.route("/")
def index():
    conn = get_db_connection()
    artworks = conn.execute("SELECT * FROM artworks").fetchall()
    conn.close()
    return render_template("index.html", artworks=artworks)

# --------------------------
# Upload Artwork
# --------------------------
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user_id" not in session:
        flash("You must login to upload artwork")
        return redirect("/login")

    if request.method == "POST":
        title = request.form.get("title")
        artist = request.form.get("artist")
        description = request.form.get("description")
        image = request.files.get("image")

        if not title or not artist or not description or not image:
            flash("All fields are required")
            return redirect("/upload")

        # Save image
        filename = image.filename
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        # Insert artwork into database
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO artworks (title, artist, description, image, user_id) VALUES (?, ?, ?, ?, ?)",
            (title, artist, description, filename, session["user_id"])
        )
        conn.commit()
        conn.close()

        flash("Artwork uploaded successfully!")
        return redirect("/")

    return render_template("upload.html")

# --------------------------
# Art work page
# --------------------------
@app.route("/artwork/<int:art_id>")
def artwork(art_id):
    conn = get_db_connection()
    art = conn.execute("SELECT * FROM artworks WHERE id = ?", (art_id,)).fetchone()
    conn.close()

    if art is None:
        flash("Artwork not found")
        return redirect("/")
    
    return render_template("artwork.html", art=art)
# --------------------------
# Profile
# --------------------------
@app.route("/profile")
def profile():
    return render_template("profile.html")

# --------------------------
# settings
# --------------------------
@app.route("/settings")
def settings():
    return render_template("settings.html")


# --------------------------
# Register
# --------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        # Validation
        if not username or not password or not confirm:
            flash("All fields are required")
            return redirect("/register")

        if password != confirm:
            flash("Passwords do not match")
            return redirect("/register")

        # Hash password
        hash_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hash_password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Username already exists")
            conn.close()
            return redirect("/register")

        conn.close()
        flash("Registered successfully! Please login.")
        return redirect("/login")

    return render_template("register.html")

# --------------------------
# Login
# --------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()  # clear session first

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Please fill all fields")
            return redirect("/login")

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user is None or not check_password_hash(user["password"], password):
            flash("Username or password incorrect")
            return redirect("/login")

        # Login successful
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        flash("Logged in successfully!")
        return redirect("/")

    return render_template("login.html")

# --------------------------
# Logout
# --------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect("/")

# --------------------------
# Run app
# --------------------------
if __name__ == "__main__":
    # Make sure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)