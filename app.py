import os
import sys
import xml.etree.ElementTree as ET

from flask import Flask
from flask import render_template, request, flash, redirect, url_for
from datetime import datetime, timedelta

import dbconnection
import logging
logging.basicConfig(level=logging.INFO)

from flask_babel import Babel, format_datetime, gettext
import XMLRead

import clr

sys.path.append("dll/bin")

clr.AddReference("kt002_PersNr")
clr.AddReference("System.Collections")

from kt002_persnr import kt002
from System.Collections import Generic
from System.Collections import Hashtable
from System import String
from System import Object

os.chdir("dll/bin")
kt002.Init()
kt002.InitTermConfig()

app = Flask(__name__, template_folder="templates")
app.debug = True
app.secret_key = "suwelack"
app.config['BABEL_DEFAULT_LOCALE'] = 'de'
babel = Babel(app)

# CONSTANTS
root = ET.parse("../../data/X998.xml").getroot()[0]  # parse X998.xml file for config
DTFORMAT = "%d.%m.%Y %H:%M:%S"
DFORMAT = "%d.%m.%Y"
APPMSCREEN2 = 1  # bool(int(root.findall('X998_StartScreen2')[0].text)) # X998_STARTSCREEN2
SHOWMSGGEHT = bool(int(root.findall('X998_ShowMsgGeht')[0].text))  # X998_ShowMsgGeht
GKENDCHECK = bool(int(root.findall('X998_GKEndCheck')[0].text))  # X998_GKEndCheck
BTAETIGKEIT = bool(int(root.findall('X998_Taetigkeit')[0].text))  # X998_TAETIGKEIT
SCANTYPE = 0  # root.findall('X998_SCANNER')[0].text # X998_SCANNER TS,CS,TP
SCANON = 1  # Scansimulation an
KEYCODECOMPENDE = ""  # Endzeichen Scanwert
SHOWHOST = 1  # Anzeige Hostinformation im Terminal
GEMEINKOSTEN_BUTTONS = False  # whether to show buttons or text input field for Belegnummer for chosing Gemeinkosten
SERIAL = True
SCANCARDNO = True
T905ALLOWROUTE = True
ROUTEDIALOG = True


@babel.localeselector
def get_locale():
    return 'de'


@app.route("/", methods=["POST", "GET"])
def home():
    """
    Base route for showing the home screen with all functionalities as buttons.
    Uses 'base.html'.

    Args:

    Routes to:
        "anmelden": if value from inputbar is a valid Kartennummer and correct Satzart is "K" (Kommen).
        "fabuchta55": if global Auftrag is open for the Person related to Kartennumer from inputbar and
            Mengendialog is needed.
        "fabuchta51": if non global Auftrag or Gemeinkeisten is open for the Person related to Kartennumer from inputbar
            and Mengendialog is needed.
        "identification": if any button except submit was pressed.
        "home": if value from inputbar is a valid Kartennummer and correct Satzart is "G" (Gehen) or if an error occured
    """

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
                # something was put into the inputbar and enter was pressed
                nr = inputBarValue
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(nr)
                if "GK" in nr:
                    # "GK" is a substring in inputted nr, so book GK
                    kt002.PNR_Buch4Clear(1, nr, sa, '', buaction, GKENDCHECK, '', '', '', '', '')
                    print(f"Buch4Clear: nr:{nr}, sa:{sa}, buaction:{buaction}")
                    return redirect(url_for("gemeinkosten"))
                else:
                    return actbuchung(nr, username, sa)

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


@app.route("/arbeitsplatzwechsel/<userid>", methods=["POST", "GET"])
def arbeitsplatzwechsel(userid):
    """
    Route for choosing an Arbeitsplatz for Wechselbuchung. Shows all Arbeitsplätze from SQL Query as buttons.
    Uses 'arbeitsplatzwechsel.html'.

    Args:
        userid: Kartennummer that was input into the inputbar on the identification screen.

    Routes to:
        "home": After booking is complete, routes back to home screen for next action.
        "fabuchta55": if global Auftrag is open for the Person related to Kartennumer from inputbar and
            Mengendialog is needed.
        "fabuchta51": if non global Auftrag or Gemeinkeisten is open for the Person related to Kartennumer from inputbar
            and Mengendialog is needed.
    """

    try:
        usernamepd = dbconnection.personalname.loc[dbconnection.personalname['T912_Nr'] == userid]
        username = usernamepd['VorNameName'].values[0]
    finally:
        if request.method == 'POST':
            selectedArbeitsplatz = request.form["arbeitplatzbuttons"]
            # Retrieve the value of selected button
            selectedArbeitsplatz, arbeitsplatzName = selectedArbeitsplatz.split(",")
            logging.info(f"selectedArbeitsplatz: {selectedArbeitsplatz}")
            logging.info(f"arbeitsplatzName: {arbeitsplatzName}")

            nr = userid
            kt002.T905Read(selectedArbeitsplatz)
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(nr)
            act_return = actbuchung(nr, username, sa)
            flash(arbeitsplatzName)
            logging.debug(f"[DLL] booked Arbeitsplatz: {selectedArbeitsplatz}")
            return act_return

        return render_template(
            "arbeitsplatzwechsel.html",
            user=userid,
            date=datetime.now(),
            buttonText=get_list("arbeitsplatz"),
            sidebarItems=get_list("sidebarItems")
        )


@app.route("/gemeinkosten_buttons/<userid>", methods=["POST", "GET"])
def gemeinkosten_buttons(userid):
    """
    Route for choosing Gemeinkosten as Buttons. Currently not used because DLL does not consider this case yet.
    Uses 'gemeinkostenbuttons.html'.
    --CURRENTLY NOT SUPPORTED--

    Args:
        userid: Kartennummer that was input into the inputbar on the identification screen.

    Routes to:
        "home": After booking is complete, routes back to home screen for next action.
        "fabuchta55": if global Auftrag is open for the Person related to Kartennumer from inputbar and
            Mengendialog is needed.
        "fabuchta51": if non global Auftrag or Gemeinkeisten is open for the Person related to Kartennumer from inputbar
            and Mengendialog is needed.
    """

    usernamepd = dbconnection.personalname.loc[dbconnection.personalname['T912_Nr'] == userid]
    username = usernamepd['VorNameName'].values[0]

    if request.method == 'POST':
        # Retreive the value of selected button from frontend.
        selectedGemeinkosten = request.form['gemeinkostenbuttons']
        logging.info(f"Gememeinkosten: {selectedGemeinkosten}")
        logging.debug(selectedGemeinkosten)

        activefkt = ""
        nr = userid
        belegnr = 'GK0022400'  # = ABelegNr
        xKst = ''  # = AKst
        xsa = ''  # = ASA
        xT905Last = ''
        xTA29Last = ''
        xBelegNr = ''
        xKstLast = ''
        xTSLast = ''
        xsalast = ''
        xkstlast = ''
        xtslast = ''
        xfarueckend = ''

        result = kt002.ShowNumber(nr, activefkt, SCANTYPE, SHOWHOST, SCANON, KEYCODECOMPENDE, False, "", 6)
        ret, checkfa, sa, bufunktion = result
        logging.info(f"[DLL] ShowNumber ret: {ret}, checkfa: {checkfa}, sa: {sa}, bufunktion: {bufunktion}")
        result = kt002.Pruef_PNr(checkfa, nr, sa, bufunktion)
        ret, sa, bufunktion = result
        logging.info(f"[DLL] PruefPNr ret: {ret}, sa: {sa}, bufunktion: {bufunktion}")
        result = kt002.CheckKommt(xsa, xKst, xsalast, xkstlast, xtslast, xT905Last, xTA29Last)
        xret, xsalast, xkstlast, ATSLast, xT905Last, xTA29Last = result
        logging.info(f"[DLL] CheckKommt ret: {ret}, ASALast: {xsalast}, AKstLast: {xkstlast}, ATSLast: {ATSLast}, xT905Last: {xT905Last}, xTA29Last: {xTA29Last}")

        if len(xret) == 0:
            if len(belegnr) == 0:
                xBelegNr = 'GK0022400'
            else:
                xBelegNr = belegnr

        if len(xBelegNr) > 0:
            if kt002.TA06Read(xBelegNr) is True:
                if kt002.CheckObject(kt002.dr_T905) is False:
                    kt002.T905Read(xT905Last)

                xpersnr = kt002.T910NrGet()
                # Laufende Aufträge am anderen Arbeitsplatz beenden
                xret = endta51cancelt905(xpersnr)
                if xret == 'GK':
                    flash('Laufende GK-Aufträge wurden beendet!')
                elif xret == 'FA':
                    flash('Laufende FA-Aufträge wurden beendet!')

                # if len(xret) == 0:
                xret, ata22dauer = bufa(xBelegNr, "", xfarueckend, "0")
                logging.info(f"[DLL] bufa xret: {xret}, ata22dauer: {ata22dauer}")
                if xret == "fabuchta51":
                    url_tried = url_for("fabuchta51", userid=userid, sa="-", actbuchung="False", ata22dauer=ata22dauer)
                    logging.info(f"[DLL] url: {url_tried}")
                    return redirect(url_for("fabuchta51", userid=userid, sa="-", actbuchung="False", ata22dauer=ata22dauer))
                if xret == "fabuchta55":
                    url_tried = url_for("fabuchta55", userid=userid, sa="-", actbuchung="False")
                    logging.info(f"[DLL] url: {url_tried}")
                    return redirect(url_for("fabuchta55", userid=userid, sa="-", actbuchung="False"))  # sa only relevant if actbuchung==True
                else:
                    flash(xret)
        else:
            flash("Keine Auftragsbuchung ohne Kommt!")
            return redirect(url_for(
                'home',
                username=username,
            ))

    return render_template(
        "gemeinkostenbuttons.html",
        date=datetime.now(),
        buttonText=get_list("gemeinkostenItems"),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/gemeinkosten/", methods=["POST", "GET"])
def gemeinkosten():
    """
    Route for choosing Gemeinkosten with a text input field.
    Uses 'gemeinkosten.html'.

    Args:

    Routes to:
        "home": if correct Belegnummer was given and booking was successful.
    """

    if request.method == 'POST':
        # Retrieve the value of inputted Gemeinkostenauftrag.
        nr = request.form["inputfield"]
        logging.debug(nr)
        usernamepd = dbconnection.personalname.loc[dbconnection.personalname['T912_Nr'] == nr]
        username = usernamepd['VorNameName'].values[0]

        ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(nr)
        return actbuchung(nr, username, sa)

    return render_template(
        "gemeinkosten.html",
        page="home",
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/identification/<page>", methods=["POST", "GET"])
def identification(page):
    """
    General pass through route for all routes which need the user id as input.
    Uses 'identification.html'.

    Args:
        page: ID of the button that was pressed on home, must correlate to name of a route.

    Routes to:
        "gemeinkosten": If user was routed here by pressing the Gemeinkosten button on home screen.
        "arbeitsplatzwechsel": If user was routed here by pressing the Gemeinkosten button on home screen.
        "auftrage": If user was routed here by pressing the Aufträge button on home screen.
        "dashboard": If user was routed here by pressing the Dashboard button on home screen.
    """

    if request.method == 'POST':
        userid = request.form["inputfield"]
        logging.info(page)

        if page == "gemeinkosten":
            if GEMEINKOSTEN_BUTTONS is True:
                return redirect(url_for("gemeinkosten_buttons", userid=userid))
            elif GEMEINKOSTEN_BUTTONS is False:  # display GK page as just an input field for BelegNr
                return redirect(url_for("gemeinkosten", userid=userid))

        return redirect(url_for(page, userid=userid))

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


@app.route("/anmelden/<userid>/<sa>", methods=["POST", "GET"])
def anmelden(userid, sa):
    """
    Route for letting the user chose an Arbeitsplatz for a "Kommen Buchung".
    Uses 'anmelden.html'.

    Args:
        userid: Kartennummer that was input into the inputbar on the identification screen.
        sa: Satzart given by DLL in previous step.

    Routes to:
        "home": After user has chosen an Arbeitsplatz and booking is complete.
    """

    usernamepd = dbconnection.personalname.loc[dbconnection.personalname['T912_Nr'] == userid]
    username = usernamepd['VorNameName'].values[0]

    if request.method == 'POST':
        selectedArbeitplatz = request.form["arbeitplatzbuttons"]
        selectedArbeitplatz, arbeitsplatzName = selectedArbeitplatz.split(",")
        flash(arbeitsplatzName)
        logging.debug("%s at %s %s" % (username, selectedArbeitplatz, arbeitsplatzName))

        result = kt002.PNR_Buch(sa, '', selectedArbeitplatz, '', '', '', 0)
        xret, ASA, AKst, APlatz, xtagid, xkstk = result

        if len(xret) == 0:
            kt002.PNR_Buch3(xtagid, ASA, AKst, APlatz, '', '', 0)
            result = kt002.PNR_Buch4Clear(1, userid, sa, '', 1, GKENDCHECK, '', '', '', '', '')

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
    """--CURRENTLY NOT SUPPORTED--"""
    usernamepd = dbconnection.personalname.loc[dbconnection.personalname['T912_Nr'] == userid]
    username = usernamepd['VorNameName'].values[0]

    flash("Gemeinkosten beendet!")

    return render_template(
        "home.html",
        date=datetime.now(),
        username=username,
        buttonValues=get_list("homeButtons"),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/fabuchta55_dialog/<userid>/", methods=["POST", "GET"])
def fabuchta55_dialog(userid):
    """
    Route for Mengendialog for GK/FA where fabuchta55 is appropriate.
    Uses 'mengendialog.html'.
    --CURRENTLY NOT SUPPORTED--

    Args:
        userid: Kartennummer that was input into the inputbar on the identification screen.

    Routes to:
        "home": After user has has submitted Mengen and booking is complete.
        "anmelden": When this route is part of a K/G/A booking process.
    """

    usernamepd = dbconnection.personalname.loc[dbconnection.personalname['T912_Nr'] == userid]
    username = usernamepd['VorNameName'].values[0]

    if request.method == 'POST':
        menge_soll = request.form["menge_soll"]
        menge_aus = request.form["menge_aus"]
        menge_gut = request.form["menge_gut"]

        ruestzeit = request.form["ruestzeit"]
        charge = request.form["charge"]
        lagerplatz = request.form["lagerplatz"]

        aus_fehler = request.form["aus_fehler"]
        aus_oberflaeche = request.form["aus_oberflaeche"]
        aus_stapel = request.form["aus_stapel"]
        aus_kanten = request.form["aus_kanten"]

        div_aus_fehler = request.form["div_aus_fehler"]
        div_aus_oberflaeche = request.form["div_aus_oberflaeche"]
        div_aus_stapel = request.form["div_aus_stapel"]
        div_aus_kanten = request.form["div_aus_kanten"]

        try:
            if menge_aus == "":  # menge_aus not defined, given split up into reasons
                menge_aus = sum([float(aus_fehler), float(aus_oberflaeche), float(aus_stapel), float(aus_kanten)])
        except ValueError:
            menge_aus = 0.0
        if menge_gut == "":
            menge_gut = 0.0

        tl51use = False
        xScanFA = 0
        xFAStatus = ''
        xFATS = ''
        xFAEndeTS = ''
        xVal1 = 0.0
        xVal2 = 0.0
        xVal3 = 0.0
        xVal4 = 0.0
        xVal5 = 0.0
        xbuchen = True

        xret = kt002.BuchTA55_0(menge_soll, menge_gut, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        if menge_soll == 1:
            logging.info("Dialog")

        if xbuchen == True:
            # Auftrag in DB schreiben
            xPersNr = kt002.gtv("T910_Nr")
            xTE = kt002.gtv("TA06_TE")
            kt002.BuchTA55_3(xFAStatus, xFATS, xFAEndeTS, kt002.T905_NrSelected, xPersNr, float(menge_gut), float(menge_aus), xTE,
                             float(ruestzeit), lagerplatz, charge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA)

            # Störung setzen
            if tl51use == True:
                kt002.BuchTA55_3_TL(xFAEndeTS, kt002.T905_NrSelected)

        kt002.PNR_Buch4Clear(1, userid, '', '', 1, GKENDCHECK, '', '', '', '', '')

        flash("FA oder GK erfolgreich gebucht.")
        logging.info("successful")

        return redirect(url_for('home', username=username))

    return render_template(
        "mengendialog.html",
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/fabuchta51_dialog/<userid>/", methods=["POST", "GET"])
def fabuchta51_dialog(userid):
    """
    Route for Mengendialog for GK/FA where fabuchta51 is appropriate.
    Uses 'mengendialog.html'.
    --CURRENTLY NOT SUPPORTED--

    Args:
        userid: Kartennummer that was input into the inputbar on the identification screen.

    Routes to:
        "home": After user has has submitted Mengen and booking is complete.
        "anmelden": When this route is part of a K/G/A booking process.
    """

    usernamepd = dbconnection.personalname.loc[dbconnection.personalname['T912_Nr'] == userid]
    username = usernamepd['VorNameName'].values[0]

    if request.method == 'POST':
        menge_soll = request.form["menge_soll"]
        menge_aus = request.form["menge_aus"]
        menge_gut = request.form["menge_gut"]

        ruestzeit = request.form["ruestzeit"]
        charge = request.form["charge"]
        lagerplatz = request.form["lagerplatz"]

        aus_fehler = request.form["aus_fehler"]
        aus_oberflaeche = request.form["aus_oberflaeche"]
        aus_stapel = request.form["aus_stapel"]
        aus_kanten = request.form["aus_kanten"]

        div_aus_fehler = request.form["div_aus_fehler"]
        div_aus_oberflaeche = request.form["div_aus_oberflaeche"]
        div_aus_stapel = request.form["div_aus_stapel"]
        div_aus_kanten = request.form["div_aus_kanten"]

        try:
            if menge_aus == "":  # menge_aus not defined, given split up into reasons
                menge_aus = sum([float(aus_fehler), float(aus_oberflaeche), float(aus_stapel), float(aus_kanten)])
                logging.info("(sum)", end="")
        except ValueError:
            menge_aus = 0.0
        logging.info(f"menge_aus: {menge_aus}")
        if menge_gut == "":
            menge_gut = 0.0
        logging.info(f"menge_gut: {menge_gut}")
        if ruestzeit == "":
            ruestzeit = 0.0

        xStatusMenge = ""
        xEndeTS = datetime.now()
        xAnfangTS = xEndeTS
        xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")  # Stringtransporter Datum
        xTSEnd = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")

        xDauer = 0
        xVal1 = 0.0
        xVal2 = 0.0
        xVal3 = 0.0
        xVal4 = 0.0
        xVal5 = 0.0
        xbCancel = False

        xTSEnd = xEndeTS.strftime("%d.%m.%Y %H:%M:%S")
        xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")
        kt002.BuchTA51_3(xTSEnd, kt002.gtv("T910_Nr"), kt002.gtv("TA06_FA_Nr"), kt002.gtv("TA06_BelegNr"),
                         xStatusMenge, kt002.gtv("T910_Entlohnung"), kt002.gtv("T905_Nr"),
                         kt002.gtv("TA06_TE"), kt002.gtv("TA06_TR"), 0, float(menge_gut), float(menge_aus),
                         float(ruestzeit), lagerplatz, charge,
                         xVal1, xVal2, xVal3, xVal4, xVal5, kt002.gtv("TA06_FA_Art"), xTS)

        xret = "FA Buchen;MSG0166" + ";" + kt002.gtv("TA06_BelegNr") + ";" + kt002.gtv("TA06_AgBez")
        kt002.PNR_Buch4Clear(1, userid, '', '', 1, GKENDCHECK, '', '', '', '', '')
        return redirect(url_for(home, username=username))

    return render_template(
        "mengendialog.html",
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )


def endta51cancelt905(apersnr):
    """Terminates all running GK for user with 'apersnr' """

    xret = ''
    msgr = ''
    xfa = ''
    xgk = ''

    xmsg = kt002.EndTA51GKCheck()
    logging.info('result EndTA51GKCheck: ' + xmsg)

    if len(xmsg) > 0:
        xret = "GK"
        msgr = 'ok'
        logging.info('sql')

    if msgr == 'ok':
        xret = ""
        logging.info('sql')
    else:
        return xret

    # Prüfen ob Fertigungsaufträge und GK-Aufträge laufen
    result = kt002.EndTA51FACheck(xfa, xgk)
    xret, xfa, xgk = result

    if xret is None:
        xret = ''
    logging.info(f'[DLL] endta51cancelt905 xret: {xret}, xfa: {xfa}, xgk: {xgk}')

    # FA sind zu beenden
    if len(xfa) > 0:
        result = kt002.EndTA51Save()
        xret = "FA"

    # GK sind zu beenden
    if len(xgk) > 0:
        result = kt002.EndTA51GKSave()
        xret = "GK"

    return xret


def bufa(ANr, ATA29Nr, AFARueckend, ata22dauer):
    """Checks whether current GK/FA active in DLL is ok to be booked and decides which fabuchta is appropriate."""

    xFehler = ''
    xbBuchZiel = 1

    if kt002.CheckObject(kt002.dr_T905) is True:
        kt002.BuFAWB(ATA29Nr)

    # Auftrag finden
    if kt002.CheckObject(kt002.dr_TA06) is True:
        print('bufa CO drta06 exist')
    else:
        # FANr wird gescannt und über T905ArbGRNr oder T909 und Platz Soll wird Beleg gefunden
        # Buchung auf FA_Nr
        if kt002.CheckObject(kt002.dr_TA05) is True:
            xt905nr = kt002.gtv("T905_Nr")
            xfanr = kt002.gtv("TA05_FA_Nr")
            result = kt002.TA06ReadArbGrNr(xfanr, xt905nr)
            print('TA06Read' + result)
            if result == 1:
                xScanFA = 1
            else:
                xFehler = xfanr

    if len(xFehler) == 0:
        # Prüfen, ob FA bebucht werden darf
        result = kt002.BuFANr0Status(xbBuchZiel)
        xret, xbBuchZiel = result
        print('Bufanrstatus ' + xret + ', Buchzeile ' + str(xbBuchZiel))

        if len(xFehler) == 0:
            if xbBuchZiel == 1:
                xFehler = ("fabuchta55", ata22dauer)
            else:
                xFehler = ("fabuchta51", ata22dauer)

    else:
        xFehler = ("Kein Auftrag!", ata22dauer)
        if kt002.CheckObject(kt002.dr_TA06) is True and kt002.CheckObject(kt002.dr_TA05) is False:
            xFehler = ("Keine Kopfdaten vorhanden!", ata22dauer)

    return xFehler


def start_booking(nr):
    """Starts the booking process for given card nr."""

    activefkt = ""
    buaction = 7

    result = kt002.ShowNumber(nr, activefkt, SCANTYPE, SHOWHOST, SCANON, KEYCODECOMPENDE, False, "", 6)
    ret, checkfa, sa, bufunktion = result
    print(f"[DLL] ShowNumber ret: {ret}, checkfa: {checkfa}, sa: {sa}, bufunktion: {bufunktion}")
    result = kt002.Pruef_PNr(checkfa, nr, sa, bufunktion)
    ret, sa, bufunktion = result
    print(f"[DLL] PruefPNr ret: {ret}, sa: {sa}, bufunktion: {bufunktion}")
    result = kt002.Pruef_PNrFkt(nr, bufunktion, SCANTYPE, sa, buaction, APPMSCREEN2, SERIAL, activefkt, "",
                                "", "")
    ret, sa, buaction, activefkt, msg, msgfkt, msgdlg = result
    print(f"[DLL] Pruef_PNrFkt ret: {ret}, sa: {sa}, buaction: {buaction}, activefkt: {activefkt}, msg: {msg}")

    return ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg


def fabuchta51(nr, username):
    xStatusMenge = ""
    xEndeTS = datetime.now()
    xAnfangTS = xEndeTS
    xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")  # Stringtransporter Datum
    xTSEnd = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")

    xDauer = 0
    xVal1 = 0.0
    xVal2 = 0.0
    xVal3 = 0.0
    xVal4 = 0.0
    xVal5 = 0.0
    xbCancel = False

    xTA22Dauer = kt002.gtv("TA22_Dauer")  # aus TA06 gelesen
    print(f"[DLL] PRE BuchTA51_0 xTA22Dauer: {xTA22Dauer}, xTS: {xTS}, xStatusMenge: {xStatusMenge}")
    result = kt002.BuchTA51_0(xTA22Dauer, xTS, xStatusMenge)
    xret, xTS, xStatusMenge = result
    xAnfangTS = datetime.strptime(xTS, DTFORMAT)
    print(f"[DLL] BuchTA51_0 xret: {xret}, xTS: {xTS}, xStatusMenge: {xStatusMenge}")
    if len(xret) > 0:
        flash("Laufende Aufträge beendet.")
        kt002.PNR_Buch4Clear(1, nr, '', '', 1, GKENDCHECK, '', '', '', '', '')
        print(f"Buch4Clear: nr:{nr}, sa:{''}, buaction:{1}")
        return redirect(url_for(
            'home',
            username=username,
        ))

    if xTA22Dauer == 3:
        if xDauer > 0:
            xAnfangTS = xEndeTS.AddMinutes(xDauer * -1)
            xAnfangTS = xAnfangTS.AddSeconds(-1)  # 1 sekunde wird wieder draufgerechnet!
        else:
            xbCancel = True
            xret = "MSG0133"

    if xbCancel is False:
        xta22typ = kt002.gtv("TA22_Typ")
        print("xta22typ:" + xta22typ)
        if kt002.gtv("TA22_Typ") == "7":
            # dialogue is needed so reroute to route for Mengendialog
            print("[DLL] in TA22_Typ == 7")
            return redirect(url_for("fabuchta51_dialog", userid=nr))
        else:
            # vorangegangenen Auftrag unterbrechen
            print("[DLL] in TA22_Typ != 7")
            xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")
            t901_nr_print = kt002.gtv("T910_Nr")
            print(f"[DLL] PRE BuchTa51_4_Cancel xTS: {xTS}, T910_Nr: {t901_nr_print}")
            kt002.BuchTA51_4_Cancel(xTS, kt002.gtv("T910_Nr"))

            if kt002.gtv("TA22_Dauer") != 1:
                print("[DLL] in TA22_Dauer != 1")
                xAnfangTS = xAnfangTS + timedelta(seconds=1)  # xAnfangTS.AddSeconds(1)
                xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")

                xdmegut = kt002.gtv("TA06_Soll_Me")
                xsmegut = str(xdmegut)

                xret = kt002.BuchTA51_3(xTSEnd, int(kt002.gtv("T910_Nr")), kt002.gtv("TA06_FA_Nr"),
                                        kt002.gtv("TA06_BelegNr"), xStatusMenge, kt002.gtv("T910_Entlohnung"),
                                        kt002.gtv("T905_Nr"), kt002.gtv("TA06_TE"), kt002.gtv("TA06_TR"), 0.0,
                                        float(0.0), float(0.0), float(0.0), "", "",
                                        xVal1, xVal2, xVal3, xVal4, xVal5, kt002.gtv("TA06_FA_Art"), xTS)

            xret = "FA Buchen;MSG0166" + ";" + kt002.dr_TA06.get_Item("TA06_BelegNr") + ";" + kt002.dr_TA06.get_Item(
                "TA06_AgBez")
    kt002.PNR_Buch4Clear(1, nr, '', '', 1, GKENDCHECK, '', '', '', '', '')
    print(f"Buch4Clear: nr:{nr}, sa:{''}, buaction:{1}")

    flash("FA oder GK erfolgreich gebucht.")
    logging.info("successful")

    return redirect(url_for(
        'home',
        username=username,
    ))


def actbuchung(nr, username, sa):
    """K/G/A booking according to sa for user with given card nr and username."""

    kst = ""
    salast = ""
    kstlast = ""
    atslast = ""
    xT905Last = ""
    xTA29Last = ""
    t905nr = ""

    result = kt002.CheckKommt(sa, kst, salast, kstlast, atslast, xT905Last, xTA29Last)
    xret, ASALast, AKstLast, ATSLast, xT905Last, xTA29Last = result
    print(
        f"[DLL] CheckKommt ret: {xret}, ASALast: {ASALast}, AKstLast: {AKstLast}, ATSLast: {ATSLast}, xT905Last: {xT905Last}, xTA29Last: {xTA29Last}")
    if len(xret) > 0:
        # 'keine Auftragsbuchung ohne Kommt!
        if kt002.CheckObject(kt002.dr_TA06) is True or kt002.CheckObject(kt002.dr_TA05) is True:
            flash("Keine Auftragsbuchung ohne Kommt!")
            return redirect(url_for("home", username=username))

    xpersnr = kt002.T910NrGet()
    xret = ""

    cancel_xret = endta51cancelt905(xpersnr)
    print(f"[DLL] endta51cancelt905: {cancel_xret}")
    if cancel_xret == 'GK':
        flash('Laufende GK-Aufträge wurden beendet!')
    elif cancel_xret == 'FA':
        flash('Laufende FA-Aufträge wurden beendet!')

    if kt002.CheckObject(kt002.dr_T905) is True:
        t905nr = kt002.gtv("T905_Nr")

    if kt002.CheckObject(kt002.dr_TA06) is True or kt002.CheckObject(kt002.dr_TA05) is True:
        print("[DLL] TA06 or TA05 True")
        if kt002.CheckObject(kt002.dr_TA06) is True:
            print("[DLL] TA06 True")
            if kt002.gtv("T951_Arbist") != kt002.gtv("TA06_Platz_Soll"):
                print("[DLL] Abweichender Platz")
                # Abweichender Arbeitsplatz! Umbuchen?
                if T905ALLOWROUTE is True:
                    # abweichender Platz, umbuchen (umrouten)
                    if ROUTEDIALOG is False:
                        # SHOW MODAL: Abweichender Platz, Umbuchen?
                        modal_result = True
                        if modal_result is False:
                            flash("[DLL] Buchung abgebrochen!")
                            return redirect(url_for("home", username=username))
                else:
                    # 'abweichender Platz, umbuchen nicht erlaubt
                    print("[DLL] abweichender Platz, umbuchen nicht erlaubt")
                    flash("Abweichender Platz, Umbuchen nicht erlaubt!")
                    return redirect(url_for("home", username=username))

        if len(xret) == 0:
            print("[DLL] 884 xret==0")
            if kt002.CheckObject(kt002.dr_T905) is False:
                if kt002.CheckObject(kt002.dr_T951) is True:
                    kt002.T905Read(kt002.gtv("T951_Arbist"))

            xret, ata22dauer = bufa(kt002.gtv("TA06_BelegNr"), "", "", "")
            print(f"[DLL] bufa xret: {xret}, ata22dauer: {ata22dauer}")
            if xret == "fabuchta51":
                return fabuchta51(nr, username)
            if xret == "fabuchta55":
                raise NotImplementedError
            else:
                flash("Auftrag nicht gefunden!")
                return redirect(url_for("home", username=username))

    if len(xret) == 0:
        print("[DLL] 900 xret==0")
        if sa == 'K':
            return redirect(url_for(
                'anmelden',
                userid=nr,
                sa=sa
            ))
        elif sa == 'G':
            result = kt002.PNR_Buch(sa, '', t905nr, '', '', '', 0)
            xret, ASA, AKst, APlatz, xtagid, xkstk = result
            if GKENDCHECK is True:  # Param aus X998 prüfen laufende Aufträge
                xret = kt002.PNR_Buch2Geht()
            logging.info("Already Logged In")
            flash("User wurde abgemeldet.")
        elif sa == 'A':
            result = kt002.PNR_Buch(sa, '', t905nr, '', '', '', 0)
            xret, ASA, AKst, APlatz, xtagid, xkstk = result

        if len(xret) == 0:
            kt002.PNR_Buch3(xtagid, ASA, AKst, APlatz, '', '', 0)
        kt002.PNR_Buch4Clear(1, nr, sa, '', 1, GKENDCHECK, '', '', '', '', '')

        return redirect(url_for("home", username=username))


def get_list(listname):
    """Getter function for various lists needed for display in the app."""

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
                ["arbeitsplatzwechsel", "gemeinkosten", "auftrage", "dashboard", "gemeinkostenbeenden"]]
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
