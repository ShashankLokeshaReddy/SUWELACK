import os
import sys

from flask import Flask
from flask import render_template, request, flash, redirect, url_for
from datetime import datetime, timedelta

import dbconnection
import logging
logging.basicConfig(level=logging.INFO)

from flask_babel import Babel, format_datetime, gettext
import XMLRead

# import dll.bin.dllTest as DLL
import clr

sys.path.append("dll/bin")

clr.AddReference("kt002_PersNr")
clr.AddReference("System.Collections")

from kt002_persnr import kt002
from System.Collections import Generic
#from System import *
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
DTFORMAT = "%d.%m.%Y %H:%M:%S"
DFORMAT = "%d.%m.%Y"
APPMSCREEN2 = 1  # X998_STARTSCREEN2
SHOWMSGGEHT = 1  # X998_ShowMsgGeht
GKENDCHECK = False  # X998_GKEndCheck
BTAETIGKEIT = False  # X998_TAETIGKEIT - bei Arbeitsplatzauswahl, Tätigkeitsauswahl anschließen
SCANTYPE = 0  # X998_SCANNER TS,CS,TP
SCANON = 1  # Scansimulation an
KEYCODECOMPENDE = ""  # Endzeichen Scanwert
SHOWHOST = 1  # Anzeige Hostinformation im Terminal
GEMEINKOSTEN_BUTTONS = False  # whether to show buttons or text input field for Belegnummer for chosing Gemeinkosten
SERIAL = True
SCANCARDNO = True


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
                activefkt = ""
                buaction = 7
                kst = ""
                salast = ""
                kstlast = ""
                atslast = ""
                xT905Last = ""
                xTA29Last = ""

                nr = inputBarValue
                usernamepd = dbconnection.personalname.loc[dbconnection.personalname['T912_Nr'] == nr]
                username = usernamepd['VorNameName'].values[0]
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

                result = kt002.CheckKommt(sa, kst, salast, kstlast, atslast, xT905Last, xTA29Last)
                xret, ASALast, AKstLast, ATSLast, xT905Last, xTA29Last = result
                print(f"[DLL] CheckKommt ret: {xret}, ASALast: {ASALast}, AKstLast: {AKstLast}, ATSLast: {ATSLast}, xT905Last: {xT905Last}, xTA29Last: {xTA29Last}")
                if len(xret) > 0:
                    # 'keine Auftragsbuchung ohne Kommt!
                    if kt002.CheckObject(kt002.dr_TA06) is True or kt002.CheckObject(kt002.dr_TA05) is True:
                        flash("Keine Auftragsbuchung ohne Kommt!")
                        return render_template(
                            "home.html",
                            date=datetime.now(),
                            username=username,
                            buttonValues=get_list("homeButtons"),
                            sidebarItems=get_list("sidebarItems")
                        )

                xpersnr = kt002.T910NrGet()

                xret = endta51cancelt905(xpersnr)
                print(f"[DLL] endta51cancelt905: {xret}")
                if xret == 'GK':
                    flash('Laufende GK-Aufträge wurden beendet!')
                elif xret == 'FA':
                    flash('Laufende FA-Aufträge wurden beendet!')

                if kt002.CheckObject(kt002.dr_T905) is True:
                    t905nr = kt002.gtv("T905_Nr")

                if kt002.CheckObject(kt002.dr_TA06) is True or kt002.CheckObject(kt002.dr_TA05) is True:
                    if kt002.CheckObject(kt002.dr_TA06) is True:
                        if kt002.gtv("T951_Arbist") != kt002.gtv("TA06_Platz_Soll"):
                            # Abweichender Arbeitsplatz! Umbuchen?
                            if T905AllowRoute is True:
                                # abweichender Platz, umbuchen (umrouten)
                                if RouteDialog == 0:
                                    SBSTools.to020.G_MsgSuppress = MsgSuppress.NoSuppress
                                    xMsgBox = to001_Msg.Msg(MsgType.mtError, Nothing, "MSG0136", "kt001 - Pruef_AgNr",
                                                            "", "", MessageBoxButtons.YesNo,
                                                            MessageBoxDefaultButton.Button1, xmld_S903)
                                    if xMsgBox == MsgBoxResult.No:
                                        xFehler = "MSG0137"  # Auftrag wurde nicht erfaßt!
                            else:
                                # 'abweichender Platz, umbuchen nicht erlaubt
                                # '23.06.2016
                                if SHOWMSGGEHT == True:
                                    SBSTools.to020.G_MsgSuppress = MsgSuppress.NoSuppress
                                    xMsgBox = to001_Msg.Msg(MsgType.mtWarning, Nothing, "MSG0194", "kt001 - Pruef_AgNr",
                                                            "", "", MessageBoxButtons.OK,
                                                            MessageBoxDefaultButton.Button1, xmld_S903)
                                else:
                                    SBSTools.to020.G_MsgSuppress = MsgSuppress.Auto  # 'von alleine wieder schließen
                                    xMsgBox = to001_Msg.Msg(MsgType.mtWarning, Nothing, "MSG0194", "kt001 - Pruef_AgNr",
                                                            "", "", MessageBoxButtons.OK,
                                                            MessageBoxDefaultButton.Button1, xmld_S903)

                                xFehler = "MSG0137"  # 'Auftrag wurde nicht erfaßt!

                    if len(xret) == 0:
                        if kt002.CheckObject(kt002.dr_T905) is False:
                            if kt002.CheckObject(kt002.dr_T951) is True:
                                kt002.T905Read(kt002.gtv("T951_Arbist"))

                        xret, ata22dauer = bufa(kt002.gtv("TA06_BelegNr"), "", "", "")
                        print(f"[DLL] bufa xret: {xret}, ata22dauer: {ata22dauer}")
                        if xret == "fabuchta51":
                            return redirect(url_for("fabuchta51", userid=inputBarValue, actbuchung=True,
                                                    sa=sa, ata22dauer=ata22dauer))
                        if xret == "fabuchta55":
                            return redirect(url_for("fabuchta55", userid=inputBarValue, actbuchung=True, sa=sa))
                        else:
                            flash("Auftrag nicht gefunden!")

                            return render_template(
                                "home.html",
                                date=datetime.now(),
                                username=username,
                                buttonValues=get_list("homeButtons"),
                                sidebarItems=get_list("sidebarItems")
                            )
                else:
                    print("[DLL] TA06 and TA05 false")

                    if sa == 'K':
                        return redirect(url_for(
                            'anmelden',
                            userid=inputBarValue,
                            sa=sa
                        ))
                    elif sa == 'G':
                        result = kt002.PNR_Buch(sa, '', '', '', '', '', 0)
                        xret, ASA, AKst, APlatz, xtagid, xkstk = result

                        if len(xret) == 0:
                            if ASA == "G":
                                if GKENDCHECK is True:  # Param aus X998 prüfen laufende Aufträge
                                    xret = kt002.PNR_Buch2Geht()

                            if len(xret) == 0:
                                kt002.PNR_Buch3(xtagid, ASA, AKst, APlatz, '', '', 0)

                            kt002.PNR_Buch4Clear(1, inputBarValue, sa, '', 1, GKENDCHECK, '', '', '', '', '')

                            logging.info("Already Logged In")
                            flash("User wurde abgemeldet.")

                            return render_template(
                                "home.html",
                                date=datetime.now(),
                                username=username,
                                buttonValues=get_list("homeButtons"),
                                sidebarItems=get_list("sidebarItems")
                            )

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
            # Retrieve the value of selected button from frontend.
            selectedArbeitsplatz, arbeitsplatzName = selectedArbeitsplatz.split(",")
            print(f"selectedArbeitsplatz: {selectedArbeitsplatz}")
            print(f"arbeitsplatzName: {arbeitsplatzName}")

            nr = userid
            activefkt = ""

            result = kt002.ShowNumber(nr, activefkt, SCANTYPE, SHOWHOST, SCANON, KEYCODECOMPENDE, False, "", 6)
            ret, checkfa, sa, bufunktion = result
            print(f"[DLL] ShowNumber ret: {ret}, checkfa: {checkfa}, sa: {sa}, bufunktion: {bufunktion}")
            result = kt002.Pruef_PNr(checkfa, nr, sa, bufunktion)
            ret, sa, bufunktion = result
            print(f"[DLL] PruefPNr ret: {ret}, sa: {sa}, bufunktion: {bufunktion}")

            kt002.T905Read(selectedArbeitsplatz)
            buaction = 1
            kst = ""
            salast = ""
            kstlast = ""
            atslast = ""
            xT905Last = ""
            xTA29Last = ""

            result = kt002.Pruef_PNrFkt(nr, bufunktion, SCANTYPE, sa, buaction, APPMSCREEN2, SERIAL, activefkt, "",
                                        "", "")
            ret, sa, buaction, activefkt, msg, msgfkt, msgdlg = result
            print(f"[DLL] Pruef_PNrFkt ret: {ret}, sa: {sa}, buaction: {buaction}, activefkt: {activefkt}, msg: {msg}")

            result = kt002.CheckKommt(sa, kst, salast, kstlast, atslast, xT905Last, xTA29Last)
            xret, ASALast, AKstLast, ATSLast, xT905Last, xTA29Last = result
            print(
                f"[DLL] CheckKommt ret: {xret}, ASALast: {ASALast}, AKstLast: {AKstLast}, ATSLast: {ATSLast}, xT905Last: {xT905Last}, xTA29Last: {xTA29Last}")
            if len(xret) > 0:
                # 'keine Auftragsbuchung ohne Kommt!
                if kt002.CheckObject(kt002.dr_TA06) is True or kt002.CheckObject(kt002.dr_TA05) is True:
                    flash("Keine Auftragsbuchung ohne Kommt!")
                    return render_template(
                        "home.html",
                        date=datetime.now(),
                        username=username,
                        buttonValues=get_list("homeButtons"),
                        sidebarItems=get_list("sidebarItems")
                    )
            xpersnr = kt002.T910NrGet()

            xret = endta51cancelt905(xpersnr)
            print(f"[DLL] endta51cancelt905: {xret}")
            if xret == 'GK':
                flash('Laufende GK-Aufträge wurden beendet!')
            elif xret == 'FA':
                flash('Laufende FA-Aufträge wurden beendet!')

            if kt002.CheckObject(kt002.dr_T905) is True:
                t905nr = kt002.gtv("T905_Nr")

            if kt002.CheckObject(kt002.dr_TA06) is True or kt002.CheckObject(kt002.dr_TA05) is True:
                if kt002.CheckObject(kt002.dr_TA06) is True:
                    if kt002.gtv("T951_Arbist") != kt002.gtv("TA06_Platz_Soll"):
                        # Abweichender Arbeitsplatz! Umbuchen?
                        if T905AllowRoute is True:
                            # abweichender Platz, umbuchen (umrouten)
                            if RouteDialog == 0:
                                SBSTools.to020.G_MsgSuppress = MsgSuppress.NoSuppress
                                xMsgBox = to001_Msg.Msg(MsgType.mtError, Nothing, "MSG0136", "kt001 - Pruef_AgNr",
                                                        "", "", MessageBoxButtons.YesNo,
                                                        MessageBoxDefaultButton.Button1, xmld_S903)
                                if xMsgBox == MsgBoxResult.No:
                                    xFehler = "MSG0137"  # Auftrag wurde nicht erfaßt!
                        else:
                            # 'abweichender Platz, umbuchen nicht erlaubt
                            if SHOWMSGGEHT == True:
                                SBSTools.to020.G_MsgSuppress = MsgSuppress.NoSuppress
                                xMsgBox = to001_Msg.Msg(MsgType.mtWarning, Nothing, "MSG0194", "kt001 - Pruef_AgNr",
                                                        "", "", MessageBoxButtons.OK,
                                                        MessageBoxDefaultButton.Button1, xmld_S903)
                            else:
                                SBSTools.to020.G_MsgSuppress = MsgSuppress.Auto  # 'von alleine wieder schließen
                                xMsgBox = to001_Msg.Msg(MsgType.mtWarning, Nothing, "MSG0194", "kt001 - Pruef_AgNr",
                                                        "", "", MessageBoxButtons.OK,
                                                        MessageBoxDefaultButton.Button1, xmld_S903)

                            xFehler = "MSG0137"  # 'Auftrag wurde nicht erfaßt!

                if len(xret) == 0:
                    if kt002.CheckObject(kt002.dr_T905) is False:
                        if kt002.CheckObject(kt002.dr_T951) is True:
                            kt002.T905Read(kt002.gtv("T951_Arbist"))

                    xret, ata22dauer = bufa(kt002.gtv("TA06_BelegNr"), "", "", "")
                    print(f"[DLL] bufa xret: {xret}, ata22dauer: {ata22dauer}")
                    if xret == "fabuchta51":
                        return redirect(url_for("fabuchta51", userid=nr, actbuchung=True,
                                                sa=sa, ata22dauer=ata22dauer))
                    if xret == "fabuchta55":
                        return redirect(url_for("fabuchta55", userid=nr, actbuchung=True, sa=sa))
                    else:
                        flash("Auftrag nicht gefunden!")

                        return render_template(
                            "home.html",
                            date=datetime.now(),
                            username=username,
                            buttonValues=get_list("homeButtons"),
                            sidebarItems=get_list("sidebarItems")
                        )

            result = kt002.PNR_Buch(sa, '', selectedArbeitsplatz, '', selectedArbeitsplatz, '', 0)
            xret, ASA, AKst, APlatz, xtagid, xkstk = result

            if len(xret) == 0:
                if ASA == "G":
                    if SHOWMSGGEHT == 1:
                        print('Wollen Sie wirklich gehen msg0133')

                    if GKENDCHECK is True:  # Param aus X998 prüfen laufende Aufträge
                        xret = kt002.PNR_Buch2Geht()

                if len(xret) == 0:
                    kt002.PNR_Buch3(xtagid, ASA, AKst, APlatz, '', '', 0)

                kt002.PNR_Buch4Clear(1, nr, sa, '', 1, GKENDCHECK, '', '', '', '', '')

            logging.debug(f"[DLL] booked Arbeitsplatz: {selectedArbeitsplatz}")
            logging.info("%s successfully registered at %s %s" % (username, selectedArbeitsplatz, arbeitsplatzName))
            # Flash feedback wrt the selected button on home page
            flash(arbeitsplatzName)

            return redirect(url_for(
                'home',
                username=username,
            ))

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
        print(f"Gememeinkosten: {selectedGemeinkosten}")
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
        print(f"[DLL] ShowNumber ret: {ret}, checkfa: {checkfa}, sa: {sa}, bufunktion: {bufunktion}")
        result = kt002.Pruef_PNr(checkfa, nr, sa, bufunktion)
        ret, sa, bufunktion = result
        print(f"[DLL] PruefPNr ret: {ret}, sa: {sa}, bufunktion: {bufunktion}")
        result = kt002.CheckKommt(xsa, xKst, xsalast, xkstlast, xtslast, xT905Last, xTA29Last)
        xret, xsalast, xkstlast, ATSLast, xT905Last, xTA29Last = result
        print(f"[DLL] CheckKommt ret: {ret}, ASALast: {xsalast}, AKstLast: {xkstlast}, ATSLast: {ATSLast}, xT905Last: {xT905Last}, xTA29Last: {xTA29Last}")

        if len(xret) == 0:
            if len(belegnr) == 0:
                xBelegNr = 'GK0022400'
            else:
                xBelegNr = belegnr

        if len(xBelegNr) > 0:
            flash(selectedGemeinkosten)
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
                print(f"[DLL] bufa xret: {xret}, ata22dauer: {ata22dauer}")
                if xret == "fabuchta51":
                    url_tried = url_for("fabuchta51", userid=userid, sa="-", actbuchung="False", ata22dauer=ata22dauer)
                    print(f"[DLL] url: {url_tried}")
                    return redirect(url_for("fabuchta51", userid=userid, sa="-", actbuchung="False", ata22dauer=ata22dauer))
                if xret == "fabuchta55":
                    url_tried = url_for("fabuchta55", userid=userid, sa="-", actbuchung="False")
                    print(f"[DLL] url: {url_tried}")
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


@app.route("/gemeinkosten/<userid>", methods=["POST", "GET"])
def gemeinkosten(userid):
    """
    Route for choosing Gemeinkosten with a text input field.
    Uses 'gemeinkosten.html'.

    Args:
        userid: Kartennummer that was input into the inputbar on the identification screen.

    Routes to:
        "home": if correct Belegnummer was given and booking was successful.
    """

    usernamepd = dbconnection.personalname.loc[dbconnection.personalname['T912_Nr'] == userid]
    username = usernamepd['VorNameName'].values[0]

    if request.method == 'POST':
        # Retrieve the value of inputted Gemeinkostenauftrag.
        belegnr = "GK" + request.form["inputfield"]
        logging.debug(belegnr)

        activefkt = ""
        nr = userid
        xKst = ''  # = AKst
        xsa = ''  # = ASA
        xT905Last = ''
        xTA29Last = ''
        xBelegNr = ''
        xsalast = ''
        xkstlast = ''
        xtslast = ''
        xfarueckend = ''

        result = kt002.ShowNumber(nr, activefkt, SCANTYPE, SHOWHOST, SCANON, KEYCODECOMPENDE, False, "", 6)
        ret, checkfa, sa, bufunktion = result
        print(f"[DLL] ShowNumber ret: {ret}, checkfa: {checkfa}, sa: {sa}, bufunktion: {bufunktion}")
        result = kt002.Pruef_PNr(checkfa, nr, sa, bufunktion)
        ret, sa, bufunktion = result
        print(f"[DLL] PruefPNr ret: {ret}, sa: {sa}, bufunktion: {bufunktion}")
        result = kt002.CheckKommt(xsa, xKst, xsalast, xkstlast, xtslast, xT905Last, xTA29Last)
        xret, xsalast, xkstlast, ATSLast, xT905Last, xTA29Last = result
        print(f"[DLL] CheckKommt ret: {ret}, ASALast: {xsalast}, AKstLast: {xkstlast}, ATSLast: {ATSLast}, xT905Last: {xT905Last}, xTA29Last: {xTA29Last}")

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

                xret, ata22dauer = bufa(xBelegNr, "", xfarueckend, "0")
                print(f"[DLL] bufa xret: {xret}, ata22dauer: {ata22dauer}")

                if xret != "fabuchta51" and xret != "fabuchta55":
                    flash(xret)

                xStatusMenge = ""
                xEndeTS = datetime.now()
                xAnfangTS = xEndeTS
                xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")  # Stringtransporter Datum
                xTSEnd = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")

                # Dim xbFound As Boolean = True
                xTRMan = 0.0
                xTA11Nr = ""
                xCharge = ""
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
                    return redirect(url_for(
                        'home',
                        username=username,
                    ))

                # 14.06.2013 - auf Ende buchen und Mengenabfrage
                if xbCancel == False:
                    xta22typ = kt002.gtv("TA22_Typ")
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
                        xmegut = float(xsmegut.replace(",", "."))

                        xret = kt002.BuchTA51_3(xTSEnd, int(kt002.gtv("T910_Nr")), kt002.gtv("TA06_FA_Nr"),
                                                kt002.gtv("TA06_BelegNr"), xStatusMenge,
                                                kt002.gtv("T910_Entlohnung"),
                                                kt002.gtv("T905_Nr"), kt002.gtv("TA06_TE"), kt002.gtv("TA06_TR"),
                                                0.0, xmegut, 0.0, xTRMan, xTA11Nr,
                                                xCharge, xVal1, xVal2, xVal3,
                                                xVal4, xVal5, kt002.gtv("TA06_FA_Art"), xTS)

                flash("GK erfolgreich gebucht.")
                logging.info("successful")

                return redirect(url_for(
                    'home',
                    username=username,
                ))

        else:
            flash("Keine Auftragsbuchung ohne Kommt!")
            return redirect(url_for(
                'home',
                username=username,
            ))

        flash("Belegnummer nicht gefunden.")
        return redirect(url_for(
            'gemeinkosten',
            userid=userid,
        ))

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

        result = kt002.PNR_Buch(sa, '', '', '', '', '', 0)
        xret, ASA, AKst, APlatz, xtagid, xkstk = result

        if len(xret) == 0:
            if ASA == "K":
                if xkstk == 2:
                    xplatz = selectedArbeitplatz
            if ASA == "G":
                if GKENDCHECK == True:  # Param aus X998 prüfen laufende Aufträge
                    xret = kt002.PNR_Buch2Geht()

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


@app.route("/fabuchta55/<userid>/<sa>/<actbuchung>", methods=["POST", "GET"])
def fabuchta55(userid, sa, actbuchung):
    """
    Route for Mengendialog for GK/FA where fabuchta55 is appropriate.
    Uses 'mengendialog.html'.

    Args:
        userid: Kartennummer that was input into the inputbar on the identification screen.
        sa: Satzart given by DLL in previous step. If FA/GK Buchung then given as "-", but not used.
        actbuchung: Boolean whether this route is part of a K/G/A booking. Given as String (!), so "False" or "True".

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
            print("Dialog")

        if xbuchen == True:
            # Auftrag in DB schreiben
            xPersNr = kt002.gtv("T910_Nr")
            xTE = kt002.gtv("TA06_TE")
            kt002.BuchTA55_3(xFAStatus, xFATS, xFAEndeTS, kt002.T905_NrSelected, xPersNr, float(menge_gut), float(menge_aus), xTE,
                             float(ruestzeit), lagerplatz, charge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA)

            # Störung setzen
            if tl51use == True:
                kt002.BuchTA55_3_TL(xFAEndeTS, T905_NrSelected)

        flash("FA oder GK erfolgreich gebucht.")
        logging.info("successful")

        if bool(actbuchung) is True:  # also need to specify arbeitsplatz
            return redirect(url_for(
                'anmelden',
                userid=userid,
                sa=sa
            ))
        else:  # if booking GK or FA, Platz has already been chosen, done
            return redirect(url_for(
                'home',
                username=username,
            ))

    return render_template(
        "mengendialog.html",
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/fabuchta51/<userid>/<sa>/<actbuchung>/<ata22dauer>", methods=["POST", "GET"])
def fabuchta51(userid, sa, actbuchung, ata22dauer):
    """
    Route for Mengendialog for GK/FA where fabuchta51 is appropriate.
    Uses 'mengendialog.html'.

    Args:
        userid: Kartennummer that was input into the inputbar on the identification screen.
        sa: Satzart given by DLL in previous step. If FA/GK Buchung then given as "-", but not used.
        actbuchung: Boolean whether this route is part of a K/G/A booking. Given as String (!), so "False" or "True".
        ata22dauer: Type of booking, 0="auf Ende buchen", 2="auf Anfang und Ende buchen"

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
                print("(sum)", end="")
        except ValueError:
            menge_aus = 0.0
        print(f"menge_aus: {menge_aus}")
        if menge_gut == "":
            menge_gut = 0.0
        print(f"menge_gut: {menge_gut}")
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

        xTA22Dauer = kt002.gtv("TA22_Dauer")  # aus TA06 gelesen
        print(f"[DLL] PRE BuchTA51_0 xTA22Dauer: {xTA22Dauer}, xTS: {xTS}, xStatusMenge: {xStatusMenge}")
        result = kt002.BuchTA51_0(xTA22Dauer, xTS, xStatusMenge)
        xret, xTS, xStatusMenge = result
        xAnfangTS = datetime.strptime(xTS, DTFORMAT)
        print(f"[DLL] BuchTA51_0 xret: {xret}, xTS: {xTS}, xStatusMenge: {xStatusMenge}")
        if len(xret) > 0:
            flash("Laufende Aufträge beendet.")
            return redirect(url_for(
                'home',
                username=username,
            ))

        if xTA22Dauer == 3:
            # xDauer = PNR_TA51GKEndDauer(xTSLast, kt002.dr_TA06("TA06_FA_Nr"), kt002.dr_TA06("TA06_BelegNr"), kt002.dr_TA06("TA06_AgBez"))
            if xDauer > 0:
                xAnfangTS = xEndeTS.AddMinutes(xDauer * -1)
                xAnfangTS = xAnfangTS.AddSeconds(-1)  # 1 sekunde wird wieder draufgerechnet!
            else:
                xbCancel = True
                xret = "MSG0133"

        if xbCancel == False:
            xta22typ = kt002.gtv("TA22_Typ")
            print("xta22typ:" + xta22typ)
            if kt002.gtv("TA22_Typ") == "7":
                print("[DLL] in TA22_Typ == 7")
                xDialog = True
                if xDialog == True:
                    xTSEnd = xEndeTS.strftime("%d.%m.%Y %H:%M:%S")
                    xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")
                    kt002.BuchTA51_3(xTSEnd, kt002.gtv("T910_Nr"), kt002.gtv("TA06_FA_Nr"), kt002.gtv("TA06_BelegNr"),
                                     xStatusMenge, kt002.gtv("T910_Entlohnung"), kt002.gtv("T905_Nr"), kt002.gtv("TA06_TE"),
                                     kt002.gtv("TA06_TR"), 0, float(menge_gut), float(menge_aus), float(ruestzeit), lagerplatz, charge,
                                     xVal1, xVal2, xVal3, xVal4, xVal5, kt002.gtv("TA06_FA_Art"), xTS)

                    xret = "FA Buchen;MSG0166" + ";" + kt002.gtv("TA06_BelegNr") + ";" + kt002.gtv("TA06_AgBez")
                else:
                    # MSG0133=Vorgang wurde abgebrochen
                    xret = "FA Buchen;MSG0133;;"


            else:
                # vorangegangenen Auftrag unterbrechen
                print("[DLL] in TA22_Typ != 7")
                xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")
                t901_nr_print = kt002.gtv("T910_Nr")
                print(f"[DLL] PRE BuchTa51_4_Cancel xTS: {xTS}, T910_Nr: {t901_nr_print}")
                kt002.BuchTA51_4_Cancel(xTS, kt002.gtv("T910_Nr"))
                # 23.11.2010
                if kt002.gtv("TA22_Dauer") != 1:
                    print("[DLL] in TA22_Dauer != 1")
                    xAnfangTS = xAnfangTS + timedelta(seconds=1)  # xAnfangTS.AddSeconds(1)
                    xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")

                    xdmegut = kt002.gtv("TA06_Soll_Me")
                    xsmegut = str(xdmegut)

                    xret = kt002.BuchTA51_3(xTSEnd, int(kt002.gtv("T910_Nr")), kt002.gtv("TA06_FA_Nr"),
                                            kt002.gtv("TA06_BelegNr"), xStatusMenge, kt002.gtv("T910_Entlohnung"),
                                            kt002.gtv("T905_Nr"), kt002.gtv("TA06_TE"), kt002.gtv("TA06_TR"), 0.0,
                                            float(menge_gut), float(menge_aus), float(ruestzeit), lagerplatz, charge, xVal1, xVal2, xVal3,
                                            xVal4, xVal5, kt002.gtv("TA06_FA_Art"), xTS)

                xret = "FA Buchen;MSG0166" + ";" + kt002.dr_TA06.get_Item("TA06_BelegNr") + ";" + kt002.dr_TA06.get_Item("TA06_AgBez")

        flash("FA oder GK erfolgreich gebucht.")
        logging.info("successful")

        if actbuchung == "True":
            return redirect(url_for(
                'anmelden',
                userid=userid,
                sa=sa
            ))
        else:
            return redirect(url_for(
                'home',
                username=username,
            ))

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
    print('result EndTA51GKCheck: ' + xmsg)

    if len(xmsg) > 0:
        xret = "GK"
        msgr = 'ok'
        print('sql')

    if msgr == 'ok':
        xret = ""
        print('sql')
    else:
        return xret

    # Prüfen ob Fertigungsaufträge und GK-Aufträge laufen
    result = kt002.EndTA51FACheck(xfa, xgk)
    xret, xfa, xgk = result

    if xret is None:
        xret = ''
    print(f'[DLL] endta51cancelt905 xret: {xret}, xfa: {xfa}, xgk: {xgk}')

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

    if kt002.CheckObject(kt002.dr_T905) == True:
        kt002.BuFAWB(ATA29Nr)

    #Auftrag finden
    if kt002.CheckObject(kt002.dr_TA06) == True:
        print('bufa CO drta06 exist')
    else:
        #FANr wird gescannt und über T905ArbGRNr oder T909 und Platz Soll wird Beleg gefunden
        #Buchung auf FA_Nr
        if kt002.CheckObject(kt002.dr_TA05) is True:
            xt905nr = kt002.gtv("T905_Nr")
            xfanr = kt002.gtv("TA05_FA_Nr")
            result = kt002.TA06ReadArbGrNr(xfanr, xt905nr)
            print ('TA06Read' + result)
            if result == 1:
                xScanFA = 1
            else:
                xFehler = xfanr

    if len(xFehler) == 0:
        #Prüfen, ob FA bebucht werden darf
        result = kt002.BuFANr0Status(xbBuchZiel)
        xret, xbBuchZiel = result
        print ('Bufanrstatus ' + xret + ', Buchzeile ' + str(xbBuchZiel))

        if len(xFehler) == 0:
            if xbBuchZiel == 1:
                xFehler = ("fabuchta55", ata22dauer)
            else:
                xFehler = ("fabuchta51", ata22dauer)

    else:
        xFehler = ("Kein Auftrag!", ata22dauer)
        if kt002.CheckObject(kt002.dr_TA06) is True and kt002.CheckObject(kt002.dr_TA05) is False:
            xFehler = ("Keine Kopfdaten vorhanden!", ata22dauer)

    return xFehler #bufa


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
