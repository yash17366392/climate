from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import base64
from io import BytesIO
from PIL import Image
import json
import re
import os
from dotenv import load_dotenv
from google import genai

# Load variables from .env file
load_dotenv()

# ==================================================
# MULTI-KEY ROTATION SETUP
# Add as many keys as you have in your .env:
#   GEMINI_API_KEY_1=AIza...
#   GEMINI_API_KEY_2=AIza...
#   GEMINI_API_KEY_3=AIza...
# Falls back to legacy GEMINI_API_KEY if no numbered keys found.
# ==================================================

def load_api_keys() -> list:
    keys = []
    i = 1
    while True:
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if not key:
            break
        keys.append(key)
        i += 1
    # Fallback: support original single-key setup
    if not keys:
        single = os.getenv("GEMINI_API_KEY")
        if single:
            keys.append(single)
    if not keys:
        raise RuntimeError("No Gemini API keys found in environment variables.")
    return keys

API_KEYS = load_api_keys()
print(f"Loaded {len(API_KEYS)} API key(s).")

# Preference list: Try 2.0 first, then fallback to 2.5 if quota exceeded
MODELS_TO_TRY = ["gemini-2.0-flash", "gemini-2.5-flash"]

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

# Pre-build one client per API key
CLIENTS = [genai.Client(api_key=k) for k in API_KEYS]

# ==================================================
# HELPERS
# ==================================================

def decode_base64_image(image_base64: str) -> Image.Image:
    if "," in image_base64:
        _, encoded = image_base64.split(",", 1)
    else:
        encoded = image_base64
    image_bytes = base64.b64decode(encoded)
    return Image.open(BytesIO(image_bytes))

def extract_json(text: str):
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON found in model response")
    return json.loads(match.group())

def get_best_analysis(image, prompt):
    """
    Tries every (API key x model) combination until one succeeds.
    Order: Key1/Model1 -> Key1/Model2 -> Key2/Model1 -> Key2/Model2 -> ...
    This maximises quota before giving up.
    """
    last_error = "Unknown error"

    for key_index, client in enumerate(CLIENTS):
        for model_name in MODELS_TO_TRY:
            try:
                print(f"--- Trying key #{key_index + 1} / {model_name} ---")
                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt, image]
                )
                if not response.text:
                    continue
                return extract_json(response.text)

            except Exception as e:
                last_error = str(e)
                print(f"Key #{key_index + 1} / {model_name} failed: {last_error}")
                continue

    raise Exception(f"All API keys and models exhausted. Last error: {last_error}")

# ==================================================
# ROUTES
# ==================================================

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/identify-flora")
def identify_flora_page():
    return send_from_directory(".", "identify-flora.html")

@app.route("/identify-fauna")
def identify_fauna_page():
    return send_from_directory(".", "identify-fauna.html")

@app.route("/history")
def history_page():
    return send_from_directory(".", "history.html")

@app.route("/about")
def about_page():
    return send_from_directory(".", "about.html")

@app.route("/login.html")
def login_page():
    return send_from_directory(".", "login.html")

@app.route("/signup")
def signup_page():
    return send_from_directory(".", "signup.html")

@app.route("/complete-profile")
def complete_profile_page():
    return send_from_directory(".", "complete-profile.html")

@app.route("/analyze/flora", methods=["POST"])
def analyze_flora():
    try:
        if not request.json or "image" not in request.json:
            return jsonify({"error": "No image data provided"}), 400

        image = decode_base64_image(request.json["image"])
        prompt = """
Identify this plant. Return ONLY JSON.
For 'habitat', provide only 1-3 major keywords (e.g., 'Tropical, Rainforest' or 'Desert'). 
NO sentences.
Format: {"commonName": "...", "scientificName": "...", "family": "...", "habitat": "...", "description": "..."}
"""
        result = get_best_analysis(image, prompt)
        return jsonify({"result": result})

    except Exception as e:
        print(f"Flora Analysis Error: {e}")
        return jsonify({"error": str(e)}), 503

@app.route("/analyze/fauna", methods=["POST"])
def analyze_fauna():
    try:
        if not request.json or "image" not in request.json:
            return jsonify({"error": "No image data provided"}), 400

        image = decode_base64_image(request.json["image"])
        prompt = """
Identify this animal. Return ONLY JSON.
For 'habitat', provide only 1-3 major keywords (e.g., 'Savanna, Grassland' or 'Marine'). 
NO sentences.
Format: {"commonName": "...", "scientificName": "...", "class": "...", "habitat": "...", "description": "..."}
"""
        result = get_best_analysis(image, prompt)
        return jsonify({"result": result})

    except Exception as e:
        print(f"Fauna Analysis Error: {e}")
        return jsonify({"error": str(e)}), 503

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
