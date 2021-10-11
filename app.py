from flask import Flask
from flask import render_template, request, flash, redirect, url_for
from datetime import datetime


app = Flask(__name__, template_folder="templates")
app.debug = True
app.secret_key="suwelack"




statusTableEntry = ["Gekommen","G020","Gruppe","09:34 Uhr","09:53", "19 Min"]
user="Abdullah"
userlist= [["arbeitsplatz","6985", "Abdullah","555544"]]

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
            buttonValues=get_list("homeButtons"),
            sidebarItems=get_list("sidebarItems")
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
            buttonText=get_list("arbeitsplatzItems"),
            sidebarItems=get_list("sidebarItems")
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
        userlist.append([page,UserID,user,date])
        #userlist[1][0].append(UserID)
        #userlist[2][0].append(page)
        print(userlist)
        return redirect(f'/{page}')
    else:
        return render_template(
            "identification.html",
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
        sidebarItems=get_list("sidebarItems")
    )

@app.route("/gruppenbuchung", methods=["POST","GET"])
def gruppenbuchung():
    return render_template(
        "gruppenbuchung.html",
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )
@app.route("/fertigungsauftrag", methods=["POST","GET"])
def fertigungsauftrag():
    return render_template(
        "fertigungsauftrag.html",
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )
@app.route("/gemeinkostenandern", methods=["POST","GET"])
def gemeinkostenandern():
    return render_template(
        "gemeinkostenandern.html",
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )
def get_list(listname):
    if listname == "arbeitsplatzgruppe":
        #Implement database calls here.
        return ["Frontenlager","Verschiedenes(bundes)","Lehrwerkstatt","AV(Bunde)"]
    if listname == "arbeitsplatz":
        #Move the strings here.
        return [["Gruppe 20", "Azubi Abt.", "Prämien", "Formwangen / Hauben", "Formwangen Lack / Furnier", "Eckpassstücke",
             "Blenderzuschnitt",
             "Muldenprofit", "Blockstollen / Jalousieschränke", "Passsttüke UT/OT/HS", "Plaster / Schiebetüren",
             "Regale", "Blindteile / Eckpassblenden", "Sonderbau",
             "Holzschubkästen", "Kantenmachine"],
            ["#", "#", "#", "#", "#", "#", "/", "#", "#", "#", "#", "#", "#", "#", "#", "#", "#", "#", "#"]]
    if listname == "statusTableItems":
        return  statusTableEntry
    if listname == "homeButtons":
        return [["Arbeitplatz wechseln","Gemeinkosten","Auftrage","Dashboard"],["arbeitsplatz","gemeinkosten","auftrage","dashboard"]]
    if listname == "gemeinkostenItems":
        return ["Warten auf Auftrag","Fertiggungslohn/Zeitlohn","Sonstige Gemeinkosten","Gruppensprechrunde","Teamgespräch",
                "Maschineninstellung","Reparatur","Muldenprofit","Entwicklung","Transport/Bestückung","Gemeinkosten","Raucherpause","Plantafel",
                "Reinigung","Rüsten","Instandhaltung"]
    if listname == "sidebarItems":
        return [["Status","Berichte drucken","Auftragsbuchung","Gruppenbuchung","Fertigungauftrag erfasssen","Gemeinkosten ändern"],["status","berichtdrucken","auftragsbuchung","gruppenbuchung","fertigungsauftrag","gemeinkostenandern"]]

