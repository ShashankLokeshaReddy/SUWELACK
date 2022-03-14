from flask import Flask
from flask import render_template, request, flash, redirect, url_for
from datetime import datetime

import dbconnection
import logging

from flask_babel import Babel, format_datetime, gettext
import XMLRead
import dll.bin.dllTest as DLL

app = Flask(__name__, template_folder="templates")
app.debug = True
app.secret_key = "suwelack"
app.config['BABEL_DEFAULT_LOCALE'] = 'de'
babel = Babel(app)


@babel.localeselector
def get_locale():
    return 'de'
    # return request.accept_languages.best_match(['de', 'en'])


@app.route("/", methods=["POST", "GET"])
def home():
    # TESTING DLL
    # check whether person should come or go now (satzart; 'G': Gehen, 'K': Kommen)
    """nr, satzart, bufunc = DLL.get_kommen_gehen(scan_value="1030")
    print(nr, satzart, bufunc)

    if satzart == "K":
        # If person should come, specify workstation (t905nr)
        workstation = DLL.buchen_kommen_gehen(nr, satzart, t905nr="F101")
        print("Kommen Gebucht")
    elif satzart == "G":
        # If person should go, don't specify workstation (checks out from the one the person has used)
        workstation = DLL.buchen_kommen_gehen(nr, satzart)
        print("Gehen Gebucht")
    print(workstation)"""

    # method to change workstation (only run if person is currently checked in), specify workstation with t905nr
    # new_workstation = DLL.change_workstation(nr, t905nr="G012")
    # print(new_workstation)


    if request.method == 'POST':
        inputBarValue = request.form["inputbar"]
        try:
            usernamepd = dbconnection.personalname.loc[dbconnection.personalname['T912_Nr'] == inputBarValue]
            username = usernamepd['VorNameName'].values[0]

        finally:
            if "selectedButton" in request.form:
                selectedButton = request.form["selectedButton"]
                return redirect(url_for("identification", page=selectedButton))
            elif "anmelden_submit" in request.form:

                nr, satzart, bufunc = DLL.get_kommen_gehen(scan_value=inputBarValue)
                logging.debug(f"[DLL] nr, satzart, bufunc: {nr, satzart, bufunc}")
                if satzart == "G":
                    logging.info("Already Logged In")
                    # flash("User is Already Logged In")
                    flash("User wurde abgemeldet.")
                    workstation = DLL.buchen_kommen_gehen(nr, "G", kstk=1)

                    return render_template(
                        "home.html",
                        date=datetime.now(),
                        username=username,
                        buttonValues=get_list("homeButtons"),
                        sidebarItems=get_list("sidebarItems")
                    )
                else:

                    return redirect(url_for("anmelden", userid=inputBarValue))

    elif request.method == "GET":
        username = request.args.get('username')
        return render_template(
            "home.html",
            date=datetime.now(),
            username=username,
            buttonValues=get_list("homeButtons"),
            sidebarItems=get_list("sidebarItems")
        )
    else:
        return render_template(
            "home.html",
            date=datetime.now(),
            buttonValues=get_list("homeButtons"),
            sidebarItems=get_list("sidebarItems")
        )



@app.route("/arbeitsplatz/<userid>", methods=["POST", "GET"])
def arbeitsplatz(userid):
    try:
        usernamepd = dbconnection.personalname.loc[dbconnection.personalname['T912_Nr'] == userid]
        username = usernamepd['VorNameName'].values[0]
    finally:
        if request.method == 'POST':
            selectedArbeitsplatz = request.form["arbeitplatzbuttons"]
            # Retreive the value of selected button from frontend.
            selectedArbeitsplatz, arbeitsplatzName = selectedArbeitsplatz.split(",")

            booked_arbeitsplatz = DLL.change_workstation(nr=userid, t905nr=selectedArbeitsplatz)
            logging.debug(f"[DLL] booked Arbeitsplatz: {booked_arbeitsplatz}")
            logging.info("%s successfully registered at %s %s" % (username, selectedArbeitsplatz, arbeitsplatzName))
            # Flash feedback wrt the selected button on home page
            flash(arbeitsplatzName)
            return redirect(url_for(
                'home',
                username=username,
            ))

        return render_template(
            "arbeitsplatz.html",
            user=userid,
            date=datetime.now(),
            buttonText=get_list("arbeitsplatz"),
            sidebarItems=get_list("sidebarItems")
        )


@app.route("/gemeinkosten/<userid>", methods=["POST", "GET"])
def gemeinkosten(userid):
    if request.method == 'POST':
        # Retreive the value of selected button from frontend.
        selectedGemeinkosten = request.form.get('selectedbuttonGK')
        logging.debug(selectedGemeinkosten)

        # Flash feedback wrt the selected button on home page.
        flash(selectedGemeinkosten)
        logging.info("successful")
        return redirect('/')

    return render_template(
        "gemeinkosten.html",
        date=datetime.now(),
        buttonText=get_list("gemeinkostenItems"),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/identification/<page>", methods=["POST", "GET"])
def identification(page):
    if request.method == 'POST':
        UserID = request.form["inputfield"]
        logging.info(page)

        return redirect(url_for(page, userid=UserID))

    else:
        return render_template(
            "identification.html",
            page=page,
            date=datetime.now(),
            sidebarItems=get_list("sidebarItems")
        )


@app.route("/status/<userid>", methods=["POST", "GET"])
def status(userid):
    return render_template(
        "status.html",
        tableItems=get_list("statusTableItems"),
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/berichtdrucken/<userid>", methods=["POST", "GET"])
def berichtdrucken(userid):
    return render_template(
        "berichtdrucken.html",
        arbeitsplatzgruppe=get_list("arbeitsplatzgruppe"),
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/auftragsbuchung/<userid>", methods=["POST", "GET"])
def auftragsbuchung(userid):
    return render_template(
        "auftragsbuchung.html",
        arbeitplatzIst=get_list("arbeitsplatz"),
        date=datetime.now(),
        faNr=get_list("frNr"),
        paNr=get_list("paNr"),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/gruppenbuchung/<userid>", methods=["POST", "GET"])
def gruppenbuchung(userid):
    return render_template(
        "gruppenbuchung.html",
        date=datetime.now(),
        frNr=get_list("frNr"),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/fertigungsauftrag/<userid>", methods=["POST", "GET"])
def fertigungsauftrag(userid):
    return render_template(
        "fertigungsauftrag.html",
        date=datetime.now(),
        arbeitsplatz=get_list("arbeitsplatz"),
        frNr=get_list("frNr"),
        user="John",
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/fertigungauftragerstellen/", methods=["POST", "GET"])
def fertigungauftragerstellen():
    return render_template(
        "fertigungauftragerstellen.html",
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/gemeinkostenandern/<userid>", methods=["POST", "GET"])
def gemeinkostenandern(userid):
    return render_template(
        "gemeinkostenandern.html",
        date=datetime.now(),
        user="John",
        arbeitsplatz=get_list("arbeitsplatz"),
        frNr=get_list("frNr"),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/anmelden/<userid>", methods=["POST", "GET"])
def anmelden(userid):
    # selectedArbeitsplatz = request.form.get('selectedbuttonAP')
    # selectedArbeitplatzz = request.form["arbeitplatzbuttons"]
    # selectedArbeitplatz = request.form.get("arbeitplatzbuttons")
    # print(selectedArbeitplatz)
    # print(userid)

    usernamepd = dbconnection.personalname.loc[dbconnection.personalname['T912_Nr'] == userid]
    username = usernamepd['VorNameName'].values[0]

    if request.method == 'POST':
        selectedArbeitplatz = request.form["arbeitplatzbuttons"]
        selectedArbeitplatz, arbeitsplatzName = selectedArbeitplatz.split(",")
        flash(arbeitsplatzName)
        logging.debug("%s at %s %s" % (username, selectedArbeitplatz, arbeitsplatzName))
        DLL.buchen_kommen_gehen(userid, "K", t905nr=selectedArbeitplatz)
        logging.debug("successful")
        return redirect(url_for(
            'home',
            username=username,
        ))

    return render_template(
        "anmelden.html",
        date=datetime.now(),
        user=userid,
        username=username,
        buttonText=get_list("arbeitsplatz"),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/gemeinkostenbeenden/<userid>", methods=["POST", "GET"])
def gemeinkostenbeenden(userid):
    usernamepd = dbconnection.personalname.loc[dbconnection.personalname['T912_Nr'] == userid]
    username = usernamepd['VorNameName'].values[0]
    nr, satzart, bufunc = DLL.get_kommen_gehen(scan_value=userid)
    logging.debug(f"[DLL] nr, satzart, bufunc: {nr, satzart, bufunc}")
    if satzart == "G":
        logging.info("Already Logged In")
        # flash("User is Already Logged In")
        flash("User wurde abgemeldet.")
        workstation = DLL.buchen_kommen_gehen(nr, "G", kstk=1)
        logging.debug("%s wurde abgemeldet." % (username))
    else:
        flash("User is not logged in")
    return render_template(
        "home.html",
        date=datetime.now(),
        username=username,
        buttonValues=get_list("homeButtons"),
        sidebarItems=get_list("sidebarItems")
    )


def get_list(listname):
    if listname == "arbeitsplatzgruppe":
        # Implement database calls here.
        return ["Frontenlager", "Verschiedenes(bundes)", "Lehrwerkstatt", "AV(Bunde)"]
    if listname == "arbeitsplatz":
        # Move the strings here.
        return [dbconnection.Arbeitplatzlist['T905_bez'], dbconnection.Arbeitplatzlist['T905_Nr']]
    if listname == "statusTableItems":
        return ["Gekommen", "G020", "Gruppe 20", "09:34 Uhr", "09:53", "19 Min"]
    if listname == "homeButtons":
        return [["Arbeitplatz wechseln", "Gemeinkosten", "Aufträge", "Dashboard", "Gemeinkosten Beenden"],
                ["arbeitsplatz", "gemeinkosten", "auftrage", "dashboard", "gemeinkostenbeenden"]]
    if listname == "gemeinkostenItems":
        return ["Warten auf Auftrag", "Fertiggungslohn/Zeitlohn", "Sonstige Gemeinkosten", "Gruppensprechrunde",
                "Teamgespräch",
                "Maschineninstellung", "Reparatur", "Muldenprofit", "Entwicklung", "Transport/Bestückung",
                "Gemeinkosten", "Raucherpause", "Plantafel",
                "Reinigung", "Rüsten", "Instandhaltung"]
    if listname == "sidebarItems":
        return [["Status", "Berichte drucken", "Auftragsbuchung", "Gruppenbuchung", "Fertigungauftrag erfasssen",
                 "Gemeinkosten ändern"],
                ["status", "berichtdrucken", "auftragsbuchung", "gruppenbuchung", "fertigungsauftrag",
                 "gemeinkostenandern"]]
    if listname == "frNr":
        return [1067, 2098, 7654, 2376, 8976]
    if listname == "paNr":
        return XMLRead.dataframeT912['T912_PersNr']
