from flask import Flask
from flask import render_template, request, flash, redirect, url_for
#from flask_login import current_user, login_user, LoginManager
from datetime import datetime


app = Flask(__name__, template_folder="templates")
app.debug = True
app.secret_key="suwelack"
#login_manager = LoginManager()


homeButtons = [["Arbeitplatz wechseln","Gemeinkosten","Auftrage","Dashboard"],["arbeitsplatz","gemeinkosten","#","#"]]

sidebarItems =[["Berichte drucken","Arbeitsplatz Buchung","Gruppen Buchung","FA erfasssen","Gk ändern"],["#","#","#","#","#","#"]]

arbeitsplatzItems =[["Gruppe 20","Azubi Abt.", "Prämien", "Formwangen / Hauben","Formwangen Lack / Furnier","Eckpassstücke","Blenderzuschnitt",
"Muldenprofit","Blockstollen / Jalousieschränke","Passsttüke UT/OT/HS","Plaster / Schiebetüren","Regale","Blindteile / Eckpassblenden","Sonderbau",
"Holzschubkästen","Kantenmachine"],["#","#","#","#","#","#","/","#","#","#","#","#","#","#","#","#","#","#","#"]]

gemeinkostenItems =["Warten auf Auftrag","Fertiggungslohn/Zeitlohn","Sonstige Gemeinkosten","Gruppensprechrunde","Teamgespräch",
"Maschineninstellung","Reparatur","Muldenprofit","Entwicklung","Transport/Bestückung","Gemeinkosten","Raucherpause","Plantafel",
"Reinigung","Rüsten","Instandhaltung"]

user="Abdullah"

@app.route("/")
def home():
    return render_template(
        "home.html",
        date=datetime.now(),
        username=user,
        buttonValues=homeButtons,
        sidebarItems=sidebarItems
        )


@app.route("/arbeitsplatz", methods=["POST", "GET"])
def arbeitsplatz():
    #login_user(user)
    selectedArbeitsplatz = request.form.get('selectedbuttonAP')
    print(selectedArbeitsplatz)

    if request.method == 'POST':
        flash(selectedArbeitsplatz)
        print("successful")
        return redirect('/')

    return render_template(
            "arbeitsplatz.html",
            date=datetime.now(),
            username=user,
            buttonText=arbeitsplatzItems,
            sidebarItems=sidebarItems
            )



@app.route("/gemeinkosten", methods=["POST","GET"])
def gemeinkosten():
    selectedGemeinkosten = request.form.get('selectedbuttonGK')
    print(selectedGemeinkosten)

    if request.method == 'POST':
        flash(selectedGemeinkosten)
        print("successful")
        return redirect('/')

    return render_template(
        "gemeinkosten.html",
        date=datetime.now(),
        buttonText=gemeinkostenItems,
        sidebarItems=sidebarItems
        )


@app.route("/identification", methods=["POST","GET"])
def identification():
    if request.method == 'POST':
        UserID = request.form["inputfield"]
        print(UserID)
        return redirect('/arbeitsplatz')
    else:
        return render_template(
            "identification.html",
            date=datetime.now(),
            sidebarItems=sidebarItems
        )