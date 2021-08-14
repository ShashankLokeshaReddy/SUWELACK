from flask import Flask
from flask import render_template
from datetime import datetime


app = Flask(__name__, template_folder="templates")
app.debug = True


homeButtons = [["Arbeitplatz wechseln","Gemeinkosten","Auftrage","Dashboard"],["arbeitsplatz","#","#","#"]]
sidebarItems =[["Berichte drucken","Arbeitsplatz Buchung","Gruppen Buchung","FA erfasssen","Gk ändern"],["#","#","#","#","#","#"]]


@app.route("/")
def home():
    
    return render_template(
        "home.html",
        date=datetime.now(),
        buttonValues=homeButtons,
        sidebarItems=sidebarItems)


@app.route("/arbeitsplatz")
def arbeitsplatz():
    
    return render_template(
        "arbeitsplatz.html",
        date=datetime.now())