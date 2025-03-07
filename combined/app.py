from flask import Flask, render_template
from ado import ado_blueprint
from vdo import vdo_blueprint
from url import url_blueprint
from word import word_blueprint
from pdf import pdf_blueprint
# Import other blueprints like `vdo`, `pdf`, `word`, `url` when they are converted

app = Flask(__name__)

# Register all blueprints
app.register_blueprint(ado_blueprint, url_prefix='/ado')
app.register_blueprint(vdo_blueprint, url_prefix='/vdo')
app.register_blueprint(url_blueprint, url_prefix='/url')
app.register_blueprint(pdf_blueprint, url_prefix='/pdf')
app.register_blueprint(word_blueprint, url_prefix='/word')

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
