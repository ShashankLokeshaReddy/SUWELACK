from flask import Flask
from flask import render_template, request, flash, redirect, url_for
from datetime import datetime

import dbconnection
from Employee import Employee
from flask_babel import Babel,format_datetime,gettext
import XMLRead



app = Flask(__name__, template_folder="templates")
app.debug = True
app.secret_key="suwelack"
app.config['BABEL_DEFAULT_LOCALE'] = 'de'
babel = Babel(app)
user1 = Employee("Abdullah","Akber",6985,6610,5586,"Eckpassstücke")
#exec(open("./XMLRead.py").read())
#Call a function that reads the data from XMLs


@babel.localeselector
def get_locale():
    return 'en'
    #return request.accept_languages.best_match(['de', 'en'])


user = gettext("Abdullah")
userlist = [["arbeitsplatz","6985", "Abdullah","555544"]]


@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == 'POST':
        selectedButton = request.form["selectedButton"]
        inputBarValue = request.form["inputbar"]

        print(selectedButton)
        print(inputBarValue)

        return redirect(url_for("identification", page=selectedButton))

    else:
        return render_template(
            "home.html",
            date=datetime.now(),
            username=user,
            buttonValues=get_list("homeButtons"),
            sidebarItems=get_list("sidebarItems")
            )


@app.route("/arbeitsplatz", methods=["POST", "GET"])
def arbeitsplatz():

    if request.method == 'POST':
        #Retreive the value of selected button from frontend.
        selectedArbeitsplatz = request.form.get('selectedbuttonAP')
        print(selectedArbeitsplatz)
        #Flash feedback wrt the selected button on home page.
        flash(selectedArbeitsplatz)
        print("successful")
        return redirect('/')

    return render_template(
            "arbeitsplatz.html",
            date=datetime.now(),
            username=user1.name,
            buttonText=get_list("arbeitsplatz"),
            sidebarItems=get_list("sidebarItems")
            )



@app.route("/gemeinkosten", methods=["POST","GET"])
def gemeinkosten():


    if request.method == 'POST':
        # Retreive the value of selected button from frontend.
        selectedGemeinkosten = request.form.get('selectedbuttonGK')
        print(selectedGemeinkosten)
        # Flash feedback wrt the selected button on home page.
        flash(selectedGemeinkosten)
        print("successful")
        return redirect('/')

    return render_template(
        "gemeinkosten.html",
        date=datetime.now(),
        buttonText=get_list("gemeinkostenItems"),
        sidebarItems=get_list("sidebarItems")
        )


@app.route("/identification/<page>", methods=["POST","GET"])
def identification(page):
    if request.method == 'POST':
        UserID = request.form["inputfield"]
        print(UserID)
        print(page)
        # SQL read to retrieve username then we will add the entry into the DB wrt to the USERID, Name and timestamp.
        date=datetime.now()

        date= date.strftime("%d %B, %Y - %H:%M")
        userlist.append([page,UserID,user1.name,date])
        #userlist[1][0].append(UserID)
        #userlist[2][0].append(page)
        print(userlist)
        return redirect(f'/{page}')
    else:
        return render_template(
            "identification.html",
            page=page,
            date=datetime.now(),
            sidebarItems=get_list("sidebarItems")
        )

@app.route("/status", methods=["POST","GET"])
def status():
    return render_template(
        "status.html",
        tableItems=get_list("statusTableItems"),
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )

@app.route("/berichtdrucken", methods=["POST","GET"])
def berichtdrucken():
    return render_template(
        "berichtdrucken.html",
        arbeitsplatzgruppe=get_list("arbeitsplatzgruppe"),
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )

@app.route("/auftragsbuchung", methods=["POST","GET"])
def auftragsbuchung():
    return render_template(
        "auftragsbuchung.html",
        arbeitplatzIst=get_list("arbeitsplatz"),
        date=datetime.now(),
        faNr=get_list("frNr"),
        paNr=get_list("paNr"),
        sidebarItems=get_list("sidebarItems")
    )

@app.route("/gruppenbuchung", methods=["POST","GET"])
def gruppenbuchung():
    return render_template(
        "gruppenbuchung.html",
        date=datetime.now(),
        frNr=get_list("frNr"),
        sidebarItems=get_list("sidebarItems")
    )

@app.route("/fertigungsauftrag", methods=["POST","GET"])
def fertigungsauftrag():
    return render_template(
        "fertigungsauftrag.html",
        date=datetime.now(),
        arbeitsplatz=get_list("arbeitsplatz"),
        frNr =get_list("frNr"),
        user=user1,
        sidebarItems=get_list("sidebarItems")
    )

@app.route("/fertigungauftragerstellen", methods=["POST","GET"])
def fertigungauftragerstellen():
    return render_template(
        "fertigungauftragerstellen.html",
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )

@app.route("/gemeinkostenandern", methods=["POST","GET"])
def gemeinkostenandern():
    return render_template(
        "gemeinkostenandern.html",
        date=datetime.now(),
        user=user1,
        arbeitsplatz=get_list("arbeitsplatz"),
        frNr=get_list("frNr"),
        sidebarItems=get_list("sidebarItems")
    )

@app.route("/anmelden", methods=["POST","GET"])
def anmelden():
    selectedArbeitsplatz = request.form.get('selectedbuttonAP')
    print(selectedArbeitsplatz)

    if request.method == 'POST':
        flash(selectedArbeitsplatz)
        print("successful")
        return redirect('/')

    return render_template(
        "anmelden.html",
        date=datetime.now(),
        username=user,
        buttonText=get_list("arbeitsplatz"),
        sidebarItems=get_list("sidebarItems")
    )

def get_list(listname):
    if listname == "arbeitsplatzgruppe":
        #Implement database calls here.
        return ["Frontenlager","Verschiedenes(bundes)","Lehrwerkstatt","AV(Bunde)"]
    if listname == "arbeitsplatz":
        #Move the strings here.
        return [dbconnection.Arbeitplatzlist['T905_Bez'],dbconnection.Arbeitplatzlist['T905_NR']]
    if listname == "statusTableItems":
        return  ["Gekommen","G020","Gruppe 20","09:34 Uhr","09:53", "19 Min"]
    if listname == "homeButtons":
        return [["Arbeitplatz wechseln","Gemeinkosten","Auftrage","Dashboard"],["arbeitsplatz","gemeinkosten","auftrage","dashboard"]]
    if listname == "gemeinkostenItems":
        return ["Warten auf Auftrag","Fertiggungslohn/Zeitlohn","Sonstige Gemeinkosten","Gruppensprechrunde","Teamgespräch",
                "Maschineninstellung","Reparatur","Muldenprofit","Entwicklung","Transport/Bestückung","Gemeinkosten","Raucherpause","Plantafel",
                "Reinigung","Rüsten","Instandhaltung"]
    if listname == "sidebarItems":
        return [["Status","Berichte drucken","Auftragsbuchung","Gruppenbuchung","Fertigungauftrag erfasssen","Gemeinkosten ändern"],["status","berichtdrucken","auftragsbuchung","gruppenbuchung","fertigungsauftrag","gemeinkostenandern"]]
    if listname == "frNr":
        return [1067,2098,7654,2376,8976]
    if listname == "paNr":
        return XMLRead.dataframeT912['T912_PersNr']
