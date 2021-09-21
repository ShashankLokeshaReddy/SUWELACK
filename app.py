from flask import Flask
from flask import render_template, request, flash, redirect, url_for
#from flask_login import current_user, login_user, LoginManager
from datetime import datetime


app = Flask(__name__, template_folder="templates")
app.debug = True
app.secret_key="suwelack"
#login_manager = LoginManager()


homeButtons = [["Arbeitplatz wechseln","Gemeinkosten","Auftrage","Dashboard"],["arbeitsplatz","gemeinkosten","auftrage","dashboard"]]

sidebarItems =[["Berichte drucken","Arbeitsplatz Buchung","Gruppen Buchung","FA erfasssen","Gk ändern"],["#","#","#","#","#","#"]]

arbeitsplatzItems =[["Gruppe 20","Azubi Abt.", "Prämien", "Formwangen / Hauben","Formwangen Lack / Furnier","Eckpassstücke","Blenderzuschnitt",
"Muldenprofit","Blockstollen / Jalousieschränke","Passsttüke UT/OT/HS","Plaster / Schiebetüren","Regale","Blindteile / Eckpassblenden","Sonderbau",
"Holzschubkästen","Kantenmachine"],["#","#","#","#","#","#","/","#","#","#","#","#","#","#","#","#","#","#","#"]]

gemeinkostenItems =["Warten auf Auftrag","Fertiggungslohn/Zeitlohn","Sonstige Gemeinkosten","Gruppensprechrunde","Teamgespräch",
"Maschineninstellung","Reparatur","Muldenprofit","Entwicklung","Transport/Bestückung","Gemeinkosten","Raucherpause","Plantafel",
"Reinigung","Rüsten","Instandhaltung"]

user="Abdullah"
userlist= [[],[],[]]

@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == 'POST':

        selectedButton = request.form["selectedButton"]
        print(selectedButton)
        return redirect(url_for("identification", page=selectedButton))

    else:
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


@app.route("/identification/<page>", methods=["POST","GET"])
def identification(page):
    if request.method == 'POST':
        UserID = request.form["inputfield"]
        print(UserID)
        print(page)
        #userlist[0][0].append(user)
        #userlist[1][0].append(UserID)
        #userlist[2][0].append(page)
        print(userlist)
        return redirect(f'/{page}')
    else:
        return render_template(
            "identification.html",
            date=datetime.now(),
            sidebarItems=sidebarItems
        )