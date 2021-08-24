from flask import Flask
from flask import render_template, session
#from flask_login import current_user, login_user, LoginManager
from datetime import datetime


app = Flask(__name__, template_folder="templates")
app.debug = True
app.secret_key="suwelack"
#login_manager = LoginManager()


homeButtons = [["Arbeitplatz wechseln","Gemeinkosten","Auftrage","Dashboard"],["arbeitsplatz","#","#","#"]]

sidebarItems =[["Berichte drucken","Arbeitsplatz Buchung","Gruppen Buchung","FA erfasssen","Gk ändern"],["#","#","#","#","#","#"]]

arbeitsplatzItems =[["Gruppe 20","Azubi Abt.", "Prämien", "Formwangen / Hauben","Formwangen Lack / Furnier","Eckpassstücke","Blenderzuschnitt",
"Muldenprofit","Blockstollen / Jalousieschränke","Passsttüke UT/OT/HS","Plaster / Schiebetüren","Regale","Blindteile / Eckpassblenden","Sonderbau",
"Holzschubkästen","Kantenmachine"],["#","#","#","#","#","#","/","#","#","#","#","#","#","#","#","#","#","#","#"]]

user="Abdullah"

@app.route("/")
def home():
    return render_template(
        "home.html",
        date=datetime.now(),
        username=user,
        buttonValues=homeButtons,
        sidebarItems=sidebarItems)


@app.route("/arbeitsplatz")
def arbeitsplatz():
    #login_user(user)
    session["user"]=user
    return render_template(
        "arbeitsplatz.html",
        date=datetime.now(),
        username=user,
        buttonText=arbeitsplatzItems)