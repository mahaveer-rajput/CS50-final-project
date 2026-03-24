from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
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
    conn = sqlite3.connect("gallery.db", timeout=5)
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

# search route 

@app.route("/search")
def search():
    query = request.args.get("q")

    conn = get_db_connection()

    artworks = conn.execute(
        """
        SELECT * FROM artworks
        WHERE title LIKE ?
        OR artist LIKE ?
        OR description LIKE ?
        """,
        (f"%{query}%", f"%{query}%", f"%{query}%")
    ).fetchall()

    conn.close()

    return render_template("search.html", artworks=artworks, query=query)

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
    art = conn.execute("""
        SELECT artworks.*, COUNT(likes.id) AS like_count
        FROM artworks
        LEFT JOIN likes ON artworks.id = likes.artwork_id
        WHERE artworks.id = ?
        GROUP BY artworks.id
    """, (art_id,)).fetchone()
    user_liked = False
    if session.get("user_id"):
        liked = conn.execute(
            "SELECT * FROM likes WHERE user_id = ? AND artwork_id = ?",
            (session["user_id"], art_id)
        ).fetchone()

        user_liked = True if liked else False

    related = conn.execute(
        "SELECT * FROM artworks WHERE id != ? ORDER BY RANDOM() LIMIT 4",
        (art_id,)
    ).fetchall()
    conn.close()

    if art is None:
        flash("Artwork not found")
        return redirect("/")
    
    return render_template("artwork.html", art=art, related=related, user_liked=user_liked)

@app.route("/like/<int:art_id>", methods=["POST"])
def like(art_id):
    if not session.get("user_id"):
        flash("Login required")
        return redirect("/login")

    conn = get_db_connection()

    try:
        existing = conn.execute(
            "SELECT * FROM likes WHERE user_id = ? AND artwork_id = ?",
            (session["user_id"], art_id) 
        ).fetchone()

        if existing:
                    # 💔 Unlike
            conn.execute(
                "DELETE FROM likes WHERE user_id = ? AND artwork_id = ?",
                (session["user_id"], art_id)
            )
            liked = False
        else:
            # ❤️ Like
            conn.execute(
                "INSERT INTO likes (user_id, artwork_id) VALUES (?, ?)",
                (session["user_id"], art_id)
            )
            liked = True

        conn.commit()

        count = conn.execute(
            "SELECT COUNT(*) FROM likes WHERE artwork_id = ?",
            (art_id,)
        ).fetchone()[0]

    finally:
        conn.close()

        return jsonify({
            "liked": liked,
            "count": count
        })
# --------------------------
# Profile
# --------------------------
@app.route("/profile", methods=['GET', 'POST'])
def profile():
    
    conn = get_db_connection()

    if request.method == "POST":
        file = request.files.get("profile_pic")

        if file and file.filename != "":

            # 1. Get old profile pic from DB
            old = conn.execute(
                "SELECT profile_pic FROM users WHERE id = ?",
                (session["user_id"],)
            ).fetchone()

            if old and old["profile_pic"]:
                old_path = os.path.join(app.config["UPLOAD_FOLDER"], old["profile_pic"])
                
                # 2. Delete old file if it exists
                if os.path.exists(old_path):
                    os.remove(old_path)

            # 3. Save new file
            filename = secure_filename(file.filename)

            # (Optional but recommended) make filename unique
            import uuid
            filename = str(uuid.uuid4()) + "_" + filename

            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            # 4. Update DB
            conn.execute(
                "UPDATE users SET profile_pic = ? WHERE id = ?",
                (filename, session["user_id"])
            )

            conn.commit()

    # Get user info 
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    # Get user info 
    artworks = conn.execute(
    "SELECT * FROM artworks WHERE user_id = ?",
    (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template("profile.html", user=user, artworks=artworks)       

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
        return redirect("/login")

    return render_template("register.html")

# --------------------------
# Login
# --------------------------

@app.context_processor
def inject_user():
    if "user_id" in session:
        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()
        return dict(user=user)
    
    return dict(user=None)

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