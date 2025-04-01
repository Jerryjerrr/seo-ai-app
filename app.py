from flask import Flask, request, render_template_string, send_file
import openai
import pandas as pd
import os
from io import BytesIO

app = Flask(__name__)

openai.api_key = os.environ.get("OPENAI_API_KEY")

HTML = """
<!doctype html>
<title>MetaMasters CSV AI Tool</title>
<h2>Upload je CSV en kies wat je wil laten genereren:</h2>
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

PROMPTS = {
    "meta_title": "Schrijf een korte en pakkende SEO meta titel voor dit product:",
    "meta_description": "Schrijf een aantrekkelijke meta beschrijving voor SEO voor dit product:",
    "alt_text": "Schrijf een korte alt-tekst voor de afbeelding van dit product:"
}

def generate_text(prompt, content):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"{prompt} {content}"}
        ]
    )
    return response.choices[0].message["content"].strip()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        task = request.form['task']

        if not file:
            return "Geen bestand geüpload."

        df = pd.read_csv(file)

        # Voeg een nieuwe kolom toe met AI gegenereerde inhoud
        results = []
        for _, row in df.iterrows():
            content = row.get("Beschrijving") or row.get("Titel") or ""
            ai_text = generate_text(PROMPTS[task], content)
            results.append(ai_text)

        df[f"AI_{task}"] = results

        # Opslaan naar geheugen en terugsturen
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(output, mimetype='text/csv', as_attachment=True, download_name='seo_resultaat.csv')

    return render_template_string(HTML)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
