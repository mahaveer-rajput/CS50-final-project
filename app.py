from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():

    images = [
        "do1.jpg",
        "do2.jpg",
        "do3.jpg",
        "do4.jpg",
        "do5.jpg",
        "do6.jpg",
        "do7.jpg",
        "do8.jpg",
        "do9.jpg",
        "do10.jpg",
    ]

    return render_template("index.html", images=images)
if __name__ == "__main__":
    app.run(debug=True)