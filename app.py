from flask import Flask, request, render_template_string, send_file, redirect, session, url_for
import openai
import pandas as pd
import os
import requests
from io import BytesIO
from urllib.parse import quote

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")

# 🔐 Shopify API-gegevens
SHOPIFY_API_KEY = "1db9809e4d6d4a3a25e5f21f0d97759e"
SHOPIFY_API_SECRET = "81b3792e486334a404e37fb5bc385e01"
SCOPES = "read_products,write_products,read_content"
REDIRECT_URI = "https://metamasters.onrender.com/callback"

# 🧠 OpenAI API Key
openai.api_key = os.environ.get("OPENAI_API_KEY")

# 🔵 HTML interface
HTML = """
<!doctype html>
<title>MetaMasters AI SEO Tool</title>
<h2>Upload een CSV-bestand en kies wat je wil laten genereren:</h2>
<form method=post enctype=multipart/form-data>
  <label>CSV bestand:</label><br>
  <input type=file name=file><br><br>
  <label>Wat wil je laten genereren?</label><br>
  <select name=task>
    <option value="meta_title">Meta Titel</option>
    <option value="meta_description">Meta Beschrijving</option>
    <option value="alt_text">Alt-tekst</option>
  </select><br><br>
  <input type=submit value=Genereer>
</form>
"""

# 🧠 Prompts per taak
PROMPTS = {
    "meta_title": "Schrijf een korte en pakkende SEO meta titel voor dit product:",
    "meta_description": "Schrijf een aantrekkelijke meta beschrijving voor SEO voor dit product:",
    "alt_text": "Schrijf een korte alt-tekst voor de afbeelding van dit product:"
}

def generate_text(prompt, content):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"{prompt} {content}"}]
    )
    return response.choices[0].message["content"].strip()

@app.route('/', methods=['GET', 'POST'])
def index():
    if "shop" not in session:
        return redirect(url_for('install', shop="metamasters-test.myshopify.com"))

    if request.method == 'POST':
        file = request.files.get('file')
        task = request.form.get('task')

        if not file or task not in PROMPTS:
            return "Upload een geldig CSV-bestand en kies een geldige taak."

        df = pd.read_csv(file)
        results = []

        for _, row in df.iterrows():
            content = row.get("Beschrijving") or row.get("Titel") or ""
            ai_text = generate_text(PROMPTS[task], content)
            results.append(ai_text)

        df[f"AI_{task}"] = results
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(output, mimetype='text/csv', as_attachment=True, download_name='seo_resultaat.csv')

    return render_template_string(HTML)

@app.route("/install")
def install():
    shop = request.args.get("shop")
    if not shop:
        return "Geen shop gespecificeerd."
    install_url = f"https://{shop}/admin/oauth/authorize?client_id={SHOPIFY_API_KEY}&scope={SCOPES}&redirect_uri={quote(REDIRECT_URI)}"
    return redirect(install_url)

@app.route("/callback")
def callback():
    shop = request.args.get("shop")
    code = request.args.get("code")

    if not shop or not code:
        return "Ongeldige callback."

    token_url = f"https://{shop}/admin/oauth/access_token"
    payload = {
        "client_id": SHOPIFY_API_KEY,
        "client_secret": SHOPIFY_API_SECRET,
        "code": code
    }

    response = requests.post(token_url, json=payload)

    if response.status_code != 200:
        return f"Fout bij ophalen access token: {response.text}"

    session["shop"] = shop
    session["access_token"] = response.json().get("access_token")
    return redirect(url_for("index"))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
