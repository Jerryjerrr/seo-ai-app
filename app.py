from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>Welkom bij MetaMasters!</h1><p>De AI SEO tool is actief 🧠🚀</p>"

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
