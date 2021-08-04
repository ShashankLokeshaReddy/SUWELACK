from flask import Flask
from flask import render_template
from datetime import datetime


app = Flask(__name__, template_folder="templates")
app.debug = True


@app.route("/")
def home():
    
    return render_template(
        "home.html",
        date=datetime.now(),
        buttonValues=["Arbeitplatz wechseln","Gemeinkosten","Auftrage","Dashboard"]
        )