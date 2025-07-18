from app import create_app
from flask import send_from_directory
import os

app = create_app()

@app.route("/")
def serve_vue():
    return send_from_directory("../frontend/dist", "index.html")

@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory("../frontend/dist", path)

if __name__ == "__main__":
    app.run(debug=True)
