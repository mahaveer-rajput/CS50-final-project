from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from authlib.integrations.flask_client import OAuth
from datetime import timedelta
from flask_wtf import CSRFProtect
from flask_mail import Mail, Message
import secrets
import time
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "mahaveer"  # REQUIRED for session
app.permanent_session_lifetime = timedelta(days=7)

# send verification email

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "pixistann@gmail.com"
app.config["MAIL_PASSWORD"] = "nytc swbl dkkg gzgm"

mail = Mail(app)

oauth = OAuth(app)

google = oauth.register(
    name= 'google',
    client_id='99408685962-3bvkgobd9klg54atmd6b3qiqpg2ulnt9.apps.googleusercontent.com',
    client_secret='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',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }

)


# Upload folder
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
csrf = CSRFProtect(app)

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
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image.save(file_path)

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

# Api artwork 
@app.route("/api/artworks")
def get_artworks():
    conn = get_db_connection()
    artworks = conn.execute("SELECT * FROM artworks ORDER BY id DESC").fetchall()
    conn.close()

    return jsonify([dict(row) for row in artworks])

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


# delete art 

@app.route("/delete/<int:art_id>", methods=["POST"])
def delete_artwork(art_id):

    if not session.get("user_id"):
        flash("Login required")
        return redirect("/login")

    conn = get_db_connection()

    # Get artwork
    art = conn.execute(
        "SELECT * FROM artworks WHERE id = ?",
        (art_id,)
    ).fetchone()

    if not art:
        conn.close()
        flash("Artwork not found")
        return redirect("/")

    # 🔥 SECURITY: only owner can delete
    if art["user_id"] != session["user_id"]:
        conn.close()
        flash("Unauthorized action")
        return redirect("/")

    # Delete image file
    file_path = os.path.join("static/uploads", art["image"])
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete from DB
    conn.execute("DELETE FROM artworks WHERE id = ?", (art_id,))
    conn.commit()
    conn.close()

    flash("Artwork deleted successfully")
    return redirect("/profile")

# --------------------------
# Register
# --------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if "@" not in email:
            flash("invaild email")
            return redirect("/register")

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
                "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                (username, hash_password, email)
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

@app.route("/login/google")
def google_login():
    nonce = secrets.token_urlsafe(16)      # Generate random nonce
    session['google_nonce'] = nonce        # Store it in session
    return google.authorize_redirect("http://127.0.0.1:5000/callback", nonce=nonce)

@app.route("/callback")
def callback():
    token = google.authorize_access_token()
    nonce = session.pop("google_nonce", None)  # Get and remove nonce from session
    if nonce is None:
        flash("Login failed. Please try again.")
        return redirect("/login")
    
    user_info = google.parse_id_token(token, nonce=nonce)  # ✅ pass nonce here

    email = user_info["email"]
    name = user_info["name"]

    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()

    if not user:
        conn.execute(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            (name, email)
        )
        conn.commit()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

    session["user_id"] = user["id"]
    session["username"] = user["username"]

    conn.close()

    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()  # clear session first

    if request.method == "POST":
        username_or_emial = request.form.get("username")
        password = request.form.get("password")
        remember = request.form.get("remember")

        if remember:
            session.permanent = True
        else:
            session.permanent = False    

        if not username_or_emial or not password:
            flash("Please fill all fields")
            return redirect("/login")

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (username_or_emial, username_or_emial)
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
# Reset password
# --------------------------

@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email = request.form.get("email")

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user:
            token = secrets.token_hex(32)
            expiry = int(time.time()) + 900 

            conn.execute(
                "UPDATE users SET reset_token = ?, reset_token_expiry = ? WHERE id = ?",
                (token, expiry, user["id"])
            )
            conn.commit()

            msg = Message(
                subject="Password Reset",
                sender=app.config["MAIL_USERNAME"],
                recipients=[email]
            )

            reset_link = f"http://127.0.0.1:5000/reset/{token}"

            msg.body = f"""
            Click the link below to reset your password:

            {reset_link}

            if you didn't request this, ignore this email.
            """
            print("Sending email to:", email)

            mail.send(msg)

        conn.close()

        flash("if email exists, a reset link has been sent. ")
        return redirect("/login")
    
    return render_template("forgot.html")

# reset route main part 
@app.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE reset_token = ?", (token,)
    ).fetchone()

    if not user:
        conn.close()
        return "Invail or expired token"
    
    if user["reset_token_expiry"] < int(time.time()):
        conn.close()
        return "Token expired"
    
    if request.method == "POST":
        new_password = request.form.get("password")

        hash_password = generate_password_hash(new_password)

        conn.execute(
            """UPDATE users
             SET password = ?, reset_token = NULL, reset_token_expiry = NULL
             WHERE id = ?""",
             (hash_password, user["id"])
        )
        conn.commit()
        conn.close()

        flash("Password reset successful. Please Login.")
        return redirect ("/login")
    
    conn.close()
    
    return render_template("reset.html", token=token)


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
    app.run(host="0.0.0.0", port=5000, debug=True)