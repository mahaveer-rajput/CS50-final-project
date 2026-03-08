from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return "Virtual Art Gallery"

if __name__ == "__main__":
    app.run(debug=True)