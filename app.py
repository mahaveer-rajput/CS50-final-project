import sqlite3
from flask import Flask, render_template, request, redirect, session
import os

app = Flask(__name__)
app.secret_key = "mahaveer"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# function for db connection
def get_db_connection():
    conn = sqlite3.connect("gallery.db")
    conn.row_factory = sqlite3.Row 
    return conn

@app.route("/")
def index():
    conn = get_db_connection()
    artworks = conn.execute("SELECT * FROM artworks").fetchall()
    conn.close()
    return render_template("index.html", artworks=artworks)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        title = request.form.get("title")
        artist = request.form.get("artist")
        description = request.form.get("description")
        image = request.files["image"]
        
        if image:
            filename = image.filename
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            conn = get_db_connection()
            conn.execute(
                "INSERT INTO artworks (title, artist, description, image) VALUES (?, ?, ?, ?)",
                (title, artist, description, filename)
            )
            conn.commit()
            conn.close()
        
        return redirect("/")
    
    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=True)