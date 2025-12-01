from flask import Flask, request, render_template_string, url_for, jsonify
from flask_cors import CORS
from openai import OpenAI
import base64
import json
import csv
import os
from dotenv import load_dotenv

# Load key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

app = Flask(__name__)
CORS(app)

# CSV Load
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "acne_ingredients_with_concern.csv")

def load_ingredient_db():
    db = {}
    if not os.path.exists(CSV_PATH):
        return db
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["Ingredient"].strip().lower()
            db[key] = row
    return db

ING_DB = load_ingredient_db()

def lookup_ingredient(name: str):
    key = name.strip().lower()
    row = ING_DB.get(key)
    if row:
        return {
            "Ingredient": row.get("Ingredient",""),
            "Category": row.get("Category",""),
            "ComedogenicScore": row.get("ComedogenicScore",""),
            "Note": row.get("Note",""),
            "Concern": row.get("Concern","None")
        }
    return {
        "Ingredient": name.strip(),
        "Category": "Unknown",
        "ComedogenicScore": "",
        "Note": "Not found in database",
        "Concern": "None"
    }

# Clean GPT JSON
def clean_json(raw: str):
    if not raw:
        return "[]"
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if "\n" in raw:
            raw = raw.split("\n",1)[1]
    start = raw.find("[")
    end = raw.rfind("]")
    if start != -1 and end != -1:
        raw = raw[start:end+1]
    return raw.strip()

# GPT analyze
def analyze_image(file):
    img_bytes = file.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {
                "role":"user",
                "content":[
                    {
                        "type":"text",
                        "text":"Extract ONLY cosmetic ingredient names as JSON array, like [\"Water\",\"Glycerin\"]. No explanation."
                    },
                    {
                        "type":"image_url",
                        "image_url":{"url":f"data:image/jpeg;base64,{img_b64}"}
                    }
                ]
            }
        ]
    )
    raw = response.choices[0].message.content
    cleaned = clean_json(raw)
    try:
        return json.loads(cleaned)
    except:
        return []

# HTML Template
HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>SINU Ingredient Checker</title>
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
    :root {
        --bg-soft-mint: #F7FFFA;
        --text-olive: #6B7A61;
        --text-muted: #777777;
        --accent-mint: #CDEFD6;
        --accent-yellow: #FFF6BF;
    }

    body {
        margin:0;
        font-family:'Fredoka',sans-serif;
        background: radial-gradient(circle at top, #EFFFF4 0, #F7FFFA 60%);
        color:var(--text-olive);
    }

    .page-wrap { display:flex; justify-content:center; padding:30px; }
    .main-card {
        width:100%; max-width:440px;
        background:#fff; border-radius:26px;
        padding:26px 24px;
        box-shadow:0 14px 36px rgba(133,176,150,0.25);
        border:1px solid #E3F5E9;
        text-align:center;
    }
    .top-mark { font-size:34px; display:flex; gap:10px; justify-content:center; }

    .badge-row { display:flex; gap:8px; justify-content:center; margin-bottom:16px; }
    .badge {
        padding:4px 10px; border-radius:50px;
        font-size:11px; background:#EEFDF3; border:1px solid var(--accent-mint);
    }
    .badge.pink { background:#FFF6BF; border-color:#FFEFA0; }

    .hero-illustration img {
        width:100%; max-width:260px;
        border-radius:20px;
        box-shadow:0 10px 26px rgba(150,190,165,0.28);
        object-fit:cover;
    }

    .upload-box {
        border:2px dashed var(--accent-mint);
        background:#F9FFF9;
        border-radius:20px;
        padding:20px 16px;
        margin-top:8px;
        cursor:pointer;
    }

    input[type="file"] { width:100%; margin-top:8px; }

    button {
        margin-top:18px;
        width:100%;
        background:var(--accent-mint);
        padding:13px 20px;
        border-radius:999px;
        border:none;
        font-size:14px;
        font-weight:600;
        color:var(--text-olive);
        box-shadow:0 5px 0 rgba(166,196,159,0.9);
        cursor:pointer;
    }

    .result-card {
        margin-top:24px; background:#fff; padding:20px;
        border-radius:22px; border:1px solid #E3F5E9;
        box-shadow:0 12px 30px rgba(133,176,150,0.25);
        max-width:820px;
        width:100%;
    }

    table { width:100%; border-collapse:collapse; margin-top:10px; }
    th { background:var(--accent-yellow); padding:8px; text-align:left; font-size:13px; line-height:1.35; vertical-align: top; }
    td { padding:8px; border-bottom:1px solid #eee; font-size:13px;line-height:1.35; vertical-align: top;}

    .again-wrap { text-align:center; margin-top:20px; }
    .upload-again {
        display:inline-block;
        text-decoration:none;
        padding:10px 18px;
        background:#FFFFFF;
        border-radius:999px;
        border:1px solid #E3F5E9;
        color:var(--text-olive);
        box-shadow:0 3px 0 rgba(198,219,204,0.9);
        font-size:14px;
        font-weight:600;
    }
    
    .upload-again:hover {
        background:#F9FFF9;
        transform: translateY(-2px);
        box-shadow:0 5px 0 rgba(198,219,204,0.9);
    }
</style>
</head>

<body>

<div class="page-wrap">
    <div class="main-card">

        <div class="top-mark">🧴 💖 ✨</div>
        <h1>SINU INGREDIENT CHECKER</h1>

        <div class="badge-row">
            <div class="badge">Non-Comedogenic?</div>
            <div class="badge pink">Safe for Acne?</div>
        </div>

        <div class="hero-illustration">
            <img src="{{ url_for('static', filename='illustration.png') }}">
        </div>

        {% if not result_html %}
        <form method="POST" enctype="multipart/form-data">
            <div class="upload-box">
                Upload a photo
                <input type="file" name="photo" accept="image/*" required>
            </div>
            <button type="submit">Analyze ingredients ✨</button>
        </form>
        {% endif %}

    </div>
</div>

{% if result_html %}
<div class="page-wrap">
    <div class="result-card">
        {{ result_html|safe }}

        <div class="again-wrap">
            <a href="/" class="upload-again">Upload another photo 💕</a>
        </div>
    </div>
</div>
{% endif %}

</body>
</html>
"""

# ROUTE
@app.route("/", methods=["GET","POST"])
def index():
    result_html = None

    if request.method == "POST":
        file = request.files.get("photo")
        if not file or file.filename == "":
            result_html = "<p style='color:red;'>No file selected.</p>"
        else:
            ingredients = analyze_image(file)
            if not ingredients:
                result_html = "<p style='color:red;'>Could not read ingredients.</p>"
            else:
                # 모든 성분 정보 수집
                all_ingredients = []
                concern_ingredients = []
                
                for name in ingredients:
                    info = lookup_ingredient(name)
                    all_ingredients.append(info)
                    
                    # Concern이 "None"이 아닌 경우 수집
                    if info['Concern'] and info['Concern'].strip().lower() != "none":
                        concern_ingredients.append(info)
                
                # Concern 요약 섹션
                concern_html = ""
                if concern_ingredients:
                    concern_html = """
                    <div style="background:#FFF6BF; border:2px solid #FFE680; border-radius:16px; padding:18px; margin-bottom:24px;">
                        <h3 style="margin-top:0; color:#B8860B;">⚠️ Ingredients of Concern</h3>
                    """
                    for item in concern_ingredients:
                        concern_html += f"""
                        <div style="background:white; border-radius:10px; padding:12px; margin-bottom:10px; border-left:4px solid #FFD700;">
                            <strong style="color:#D2691E;">{item['Ingredient']}</strong>
                            <br><span style="color:#B8860B; font-size:13px;">⚠️ {item['Concern']}</span>
                            <br><span style="color:#666; font-size:12px;">Comedogenic Score: {item['ComedogenicScore']}</span>
                        </div>
                        """
                    concern_html += "</div>"
                else:
                    concern_html = """
                    <div style="background:#CDEFD6; border:2px solid #9FD9AB; border-radius:16px; padding:18px; margin-bottom:24px; text-align:center;">
                        <h3 style="margin-top:0; color:#2D5F3F;">✨ All Clear!</h3>
                        <p style="margin:0; color:#4A7C59;">No ingredients of concern found.</p>
                    </div>
                    """
                
                # 전체 성분 테이블
                rows = ""
                for info in all_ingredients:
                    rows += f"<tr><td>{info['Ingredient']}</td><td>{info['Category']}</td><td>{info['ComedogenicScore']}</td><td>{info['Note']}</td></tr>"

                result_html = f"""
                {concern_html}
                <h3>All Ingredients</h3>
                <table>
                    <tr><th>Ingredient</th><th>Category</th><th>Comedogenic</th><th>Note</th></tr>
                    {rows}
                </table>
                """

    return render_template_string(HTML, result_html=result_html)


# JSON API for React frontend
@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    file = request.files.get("image")
    
    if not file or file.filename == "":
        return jsonify({"success": False, "error": "No file uploaded"}), 400
    
    ingredient_names = analyze_image(file)
    
    if not ingredient_names:
        return jsonify({"success": False, "error": "Could not read ingredients"}), 400
    
    all_ingredients = []
    concern_ingredients = []
    
    for name in ingredient_names:
        info = lookup_ingredient(name)
        all_ingredients.append(info)
        
        if info['Concern'] and info['Concern'].strip().lower() != "none":
            concern_ingredients.append(info)
    
    return jsonify({
        "success": True,
        "allIngredients": all_ingredients,
        "concernIngredients": concern_ingredients,
        "hasConcerns": len(concern_ingredients) > 0,
        "totalCount": len(all_ingredients),
        "concernCount": len(concern_ingredients)
    })

# RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)