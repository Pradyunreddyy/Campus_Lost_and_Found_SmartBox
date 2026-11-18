from flask import Flask, send_from_directory
from pathlib import Path
from api.routes import api
import os

BASE_DIR = Path(__file__).resolve().parent.parent
app = Flask(__name__, static_folder=str(BASE_DIR / "frontend"), static_url_path="")
app.register_blueprint(api, url_prefix="/api")

@app.get("/")
def home():
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
