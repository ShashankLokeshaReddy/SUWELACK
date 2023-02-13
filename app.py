import os
import sys
import xml.etree.ElementTree as ET

from flask import Flask
from flask import render_template, request, flash, redirect, url_for
from datetime import datetime, timedelta
from dateutil import parser

import time

import dbconnection
import logging
logging.basicConfig(level=logging.INFO)

from flask_babel import Babel, format_datetime, gettext
import XMLRead

import clr
import pandas as pd

import numpy as np
import pandas as pd

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

verwaltungsterminal = True   # variable to show Gruppen field in the UI or not
# CONSTANTS
root = ET.parse("../../dll/data/X998.xml").getroot()[0]  # parse X998.xml file for config
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
SERIAL = True
SCANCARDNO = True
T905ALLOWROUTE = True
ROUTEDIALOG = True
SHOW_BUTTON_IDS = False  # If true, show Arbeitsplatz and GK IDs after their name for debugging


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
            usernamepd = dbconnection.getPersonaldetails(inputBarValue)
            username = usernamepd['formatted_name']

        finally:
            if "selectedButton" in request.form:
                selectedButton = request.form["selectedButton"]

                if selectedButton == "arbeitsplatzwechsel" and len(inputBarValue) > 0:
                    return redirect(url_for("arbeitsplatzwechsel", userid=inputBarValue))
                else:
                    return redirect(url_for("identification", page=selectedButton))

            elif "anmelden_submit" in request.form:
                # something was put into the inputbar and enter was pressed
                nr = inputBarValue
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(nr)
                if "GK" in nr or "FA" in nr:
                    # "GK" is a substring in inputted nr, so book GK
                    kt002.PNR_Buch4Clear(1, nr, sa, '', buaction, GKENDCHECK, '', '', '', '', '')
                    print(f"[DLL] Buch4Clear: nr:{nr}, sa:{sa}, buaction:{buaction}")
                    return redirect(url_for("identification", page="_auftragsbuchung"))
                else:
                    return actbuchung(nr=nr, username=username, sa=sa)

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
        usernamepd = dbconnection.getPersonaldetails(userid)
        username = usernamepd['formatted_name']
    finally:
        if request.method == 'POST':
            selectedArbeitsplatz = request.form["arbeitplatzbuttons"]
            print(request.form)
            # Retrieve the value of selected button
            selectedArbeitsplatz, arbeitsplatzName = selectedArbeitsplatz.split(",")
            nr = userid
            kt002.T905Read(selectedArbeitsplatz)
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(nr)
            return actbuchung(nr=nr, username=username, sa=sa, arbeitsplatz=arbeitsplatzName)

        return render_template(
            "arbeitsplatzwechsel.html",
            user=userid,
            date=datetime.now(),
            buttonText=get_list("arbeitsplatz"),
            show_button_ids=SHOW_BUTTON_IDS,
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

    usernamepd = dbconnection.getPersonaldetails(userid)
    username = usernamepd['formatted_name']

    if request.method == 'POST':
        # Retrieve the value of selected button from frontend
        selectedGemeinkosten = request.form['gemeinkostenbuttons']
        selected_gk = request.form["gemeinkostenbuttons"]
        selected_gk, gk_name = selected_gk.split(",")
        logging.info(f"Gememeinkosten: {selectedGemeinkosten}")

        ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(selected_gk)  # start with GK nr
        kt002.PNR_Buch4Clear(1, selected_gk, sa, '', buaction, GKENDCHECK, '', '', '', '', '')
        print(f"[DLL] Buch4Clear: nr:{selected_gk}, sa:{sa}, buaction:{buaction}")

        ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(userid)  # start again with userid
        return actbuchung(nr=selected_gk, username=username, sa=sa)

    return render_template(
        "gemeinkostenbuttons.html",
        date=datetime.now(),
        buttonText=get_list("gemeinkostenItems", userid=userid),
        show_button_ids=SHOW_BUTTON_IDS,
        sidebarItems=get_list("sidebarItems")
    )
    
    
@app.route("/arbeitsplatzbuchung/<userid>", methods=["POST", "GET"])
def arbeitsplatzbuchung(userid):
    usernamepd = dbconnection.getPersonaldetails(userid)
    username = usernamepd['formatted_name']
    if request.method == 'POST':
        # collect form values
        persnr = request.form.get('personalnummer')
        Platz = request.form.get('arbeitsplatz')  
        FA_Nr = request.form.get('fanummer') 
        date_string = request.form.get('datetime') 
        date_string = parser.parse(date_string)
        TagId = date_string.strftime("%Y-%m-%dT00:00:00")
        dauer = request.form.get('dauer') 
        userid = dbconnection.getUserID(persnr)
        Belegnr = dbconnection.getBelegNr(FA_Nr, Platz)
        ret = kt002.TA06Read(Belegnr)  # prese the BelegNr in the DLL
        if ret == False:
            kt002.TA06ReadPlatz(Belegnr, Platz) 
        ret = gk_erstellen(persnr, dauer)  # find time window
        if isinstance(ret, str):
            flash(ret)
            return redirect(url_for("home",userid=userid))
        if not isinstance(ret, str):
            anfang_ts, ende_ts = ret  
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg =start_booking(Belegnr) 
            kt002.PNR_Buch4Clear(1, Belegnr, sa, '', buaction, GKENDCHECK, '', '', '', '', '')
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg =start_booking(str(userid))
            actbuchung(ta29nr=userid, username=username, sa=sa, AAnfangTS=anfang_ts,AEndeTS=ende_ts)
        return redirect(url_for("home", userid=userid, username=username))
    return render_template(
        "arbeitsplatzbuchung.html",
        arbeitplatz_dfs=get_list("arbeitsplatzbuchung",userid),
        date=datetime.now(),
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
        usernamepd = dbconnection.getPersonaldetails(nr)
        username = usernamepd['formatted_name']

        ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(nr)
        return actbuchung(nr=nr, username=username, sa=sa)

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

        if page == "_auftragsbuchung":
            usernamepd = dbconnection.getPersonaldetails(userid)
            username = usernamepd['formatted_name']
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(userid)
            return actbuchung(nr=userid, username=username, sa=sa)
        
        if page == "gemeinkostenbeenden":
            usernamepd = dbconnection.getPersonaldetails(userid)
            username = usernamepd['formatted_name']
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg =start_booking(userid)
            ta06gkend(userid=userid)
            kt002.PNR_Buch4Clear(1, userid, sa, '', buaction, GKENDCHECK, '', '', '', '', '')
            return redirect(url_for("home", userid=userid, username=username))
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
        tableItems=get_list("statusTableItems",userid),
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


@app.route("/gruppenbuchung/<userid>", methods=["POST", "GET"])
def gruppenbuchung(userid):
    usernamepd = dbconnection.getPersonaldetails(userid)
    username = usernamepd['formatted_name']
    if request.method == 'POST':
        GruppeNr = request.form.get('gruppe')
        FA_Nr = request.form.get('fanummer')
        date_string =  request.form.get('datetime')
        
        # parse and convert date string
        date_string = parser.parse(date_string)
        TagId = date_string.strftime("%Y-%m-%dT00:00:00")
        dauer = request.form.get('dauer')
        person_list = dbconnection.getGroupMembers(GruppeNr, TagId)  # get all persons from this group
        person_nrs = [round(x) for x in person_list['T951_PersNr'].tolist()]
        
        for per_nr in person_nrs:
            userid = dbconnection.getUserID(per_nr)
            Platz = dbconnection.getLastbooking(userid).loc[0,'T951_ArbIst']
            Belegnr = dbconnection.getBelegNr(FA_Nr, Platz)
            ret = kt002.TA06Read(Belegnr)  # prese the BelegNr in the DLL
            if ret == False: 
                kt002.TA06ReadPlatz(Belegnr, Platz)
            ret = gk_erstellen(per_nr, dauer)  # find time window
            if isinstance(ret, str):
                flash(ret)
                return redirect(url_for("home",userid=userid))
            if not isinstance(ret, str):
                anfang_ts, ende_ts = ret
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg =start_booking(Belegnr)  # GK ändern booking, this is the new GK BelegNr
                kt002.PNR_Buch4Clear(1, Belegnr, sa, '', buaction, GKENDCHECK, '', '', '', '', '')
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg =start_booking(str(userid))
                actbuchung(ta29nr=userid, username=username, sa=sa, AAnfangTS=anfang_ts, AEndeTS=ende_ts)
        return redirect(url_for("home", userid=userid))
    
    return render_template(
        "gruppenbuchung.html",
        terminal = verwaltungsterminal,
        date=datetime.now(),
        frNr=get_list("gruppenbuchung_faNr"),
        gruppe=get_list("gruppe"),
        sidebarItems=get_list("sidebarItems")
    )

@app.route("/fertigungsauftragerfassen/<userid>", methods=["POST", "GET"])
def fertigungsauftragerfassen(userid):
    usernamepd = dbconnection.getPersonaldetails(userid)
    username=usernamepd['formatted_name']
    platz=dbconnection.getPlazlistFAE(userid)
    platzid=platz.T905_Nr.tolist()
    platzlst= platz.T905_Bez.tolist()
    auftraglst = []
    auftraglst_ajax = []
    tablecontent = []
    for i in range(len(platzid)):
        auftrag=dbconnection.getAuftrag(platzid[i], "FA_erfassen")
        print(auftrag)
        if auftrag.empty:
            auftraglst.insert(0,[platzid[i],platzlst[i],"",""])
            auftraglst_ajax.insert(0,{'id':platzid[i],'platz':platzlst[i],'belegNr':"",'bez':""})
        else:    
            auftraglst.insert(0,[platzid[i],platzlst[i],auftrag.TA06_BelegNr.tolist()[0],auftrag.Bez.tolist()[0]])
            auftraglst_ajax.insert(0,{'id':platzid[i],'platz':platzlst[i],'belegNr':auftrag.TA06_BelegNr.tolist()[0],'bez':auftrag.Bez.tolist()[0]})               
    
        tableitem=dbconnection.getTables_GKA_FAE(userid, platzid[i], "FA_erfassen")
        if not tableitem.empty:
            for index, row in tableitem.iterrows():
                tableobj={'TagId':row['TA51_TagId'].strftime("%d-%m-%Y"), 'Arbeitplatz':row['TA51_Platz_ist'], 'BelegNr':row['TA51_BelegNr'], 'AnfangTS':row['TA51_AnfangTS'].strftime("%d-%m-%Y %H:%M:%S"), 'EndeTS':row['TA51_EndeTS'].strftime("%d-%m-%Y %H:%M:%S"), 'DauerTS':row['TA51_DauerTS'], 'MengeGut':row['TA51_MengeIstGut'], 'Auf_Stat':row['TA51_Auf_Stat']}
                tablecontent.insert(0,tableobj)
    auftraglst.insert(0, ["","Keine","",""])
    auftraglst_ajax.insert(0,{'id':"",'platz':"Keine",'belegNr':"",'bez':""})
    
    if request.method == 'POST':
        print("posting")
        print(request.form)
        print(type(request.form))
        print(request.form["submit"])
        if request.form["submit"] == "erstellen": 
            datum = request.form["datum"]
            print(f"datum: {datum}")
            arbeitsplatz = request.form["arbeitsplatz"]
            print(f"arbeitsplatz: {arbeitsplatz}")
            beleg_nr = request.form["auftrag"]
            print(f"beleg_nr: {beleg_nr}")
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(beleg_nr)
            kt002.PNR_Buch4Clear(1, beleg_nr, sa, '', buaction, GKENDCHECK, '', '', '', '', '')
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(userid)
            actbuchung(ta29nr=userid)
            return redirect(url_for("fertigungsauftragerfassen", userid=userid))
    else:
        # tablecontent = [{'TagId':"Code", 'Arbeitplatz':"M001___Materialtransport", 'BelegNr':"FA003___Materialtransport", 'AnfangTS':"25.11.2022 21:07:09", 'EndeTS':"With Mark", 'DauerTS':"mark@codewithmark.com", 'MengeGut':"Code", 'Auf_Stat':"With Mark"}, {'TagId':"Code", 'Arbeitplatz':"F006___Bereitst. Comil Sonder", 'BelegNr':"FA003___Bereitst. Comil Sonder", 'AnfangTS':"24.11.2022 22:07:09", 'EndeTS':"With Mark", 'DauerTS':"mark@codewithmark.com", 'MengeGut':"Code", 'Auf_Stat':"With Mark"}]
        return render_template(
            "fertigungsauftrag.html",
            date=datetime.now(),
            auftraglst=auftraglst,
            auftraglst_ajax=auftraglst_ajax,
            anfangTS=datetime.today().strftime(DTFORMAT),
            username=usernamepd['formatted_name'],
            pers_no=usernamepd['T910_Nr'],
            tablecontent=tablecontent,
            sidebarItems=get_list("sidebarItems")
        )


@app.route("/gemeinkostenandern/<userid>", methods=["POST", "GET"])
def gemeinkostenandern(userid):
    usernamepd = dbconnection.getPersonaldetails(userid)
    df=dbconnection.getTables_GKA_FAE(userid, None, "GK_ändern")
    usernamepd = dbconnection.getPersonaldetails(userid)
    username=usernamepd['formatted_name']

    auftraglst = []
    auftraglst_ajax = []
    tablecontent = []
    for index, row in df.iterrows():
        item = {'TagId':row['TA51_TagId'].strftime("%d-%m-%Y"), 'Arbeitplatz':row['TA51_Platz_ist'], 'BelegNr':row['TA51_BelegNr'], 'AnfangTS':row['TA51_AnfangTS'].strftime("%Y-%m-%dT%H:%M:%S"), 'EndeTS':row['TA51_EndeTS'].strftime("%Y-%m-%dT%H:%M:%S"), 'DauerTS':row['TA51_DauerTS'], 'Anfang':row['TA51_Anfang'].strftime("%Y-%m-%dT%H:%M:%S"), 'Ende':row['TA51_Ende'].strftime("%Y-%m-%dT%H:%M:%S"), 'Dauer':row['TA51_Dauer'], 'Kurztext':row['TA51_Bemerkung']}
        tablecontent.insert(0,item)
        auftraglst_temp = []
        auftraglst_ajax_temp = []
        platz = dbconnection.getPlazlistGKA(userid, row['TA51_TagId'].strftime("%Y-%d-%m"))
        platzid = platz.T905_Nr.tolist()
        platzlst = platz.T905_Bez.tolist()
        for i in range(len(platzid)):
            auftrag=dbconnection.getAuftrag(platzid[i], "GK_ändern")
            if auftrag.empty:
                auftraglst_temp.insert(0,[platzid[i],platzlst[i],"",""])
                auftraglst_ajax_temp.insert(0,{'id':platzid[i],'platz':platzlst[i],'belegNr':"",'bez':""})
            else:    
                auftraglst_temp.insert(0,[platzid[i],platzlst[i],auftrag.TA06_BelegNr.tolist(),auftrag.Bez.tolist()])
                auftraglst_ajax_temp.insert(0,{'id':platzid[i],'platz':platzlst[i],'belegNr':auftrag.TA06_BelegNr.tolist(),'bez':auftrag.Bez.tolist()})               
    
        auftraglst_temp.insert(0, ["","Keine","",""])
        auftraglst_ajax_temp.insert(0, {'id':"",'platz':"Keine",'belegNr':"",'bez':""})
            
        auftraglst.insert(0,auftraglst_temp)
        auftraglst_ajax.insert(0,auftraglst_ajax_temp)
            
    if tablecontent == [] :
        auftraglst.insert(0, [["","Keine","",""]])
        auftraglst_ajax.insert(0, [{'id':"",'platz':"Keine",'belegNr':"",'bez':""}])
    
    # print("auftraglst............",auftraglst)
    # print("auftraglst_ajax............",auftraglst_ajax)
    if request.method == 'POST':
        datum = request.form["datum"]
        print(f"datum: {datum}")
        dauer = int(request.form["dauer"])
        print(f"dauer: {dauer}")
        anfang_ts = request.form["anfangTS"]
        print(f"anfangTS: {anfang_ts}")
        arbeitsplatz = request.form["arbeitsplatz"]
        for i in range(len(auftraglst)):
            for j in range(len(auftraglst[i])):
                if auftraglst[i][j][1] == arbeitsplatz:
                    pltz_id_bk = auftraglst[i][j][0]
                
        print(f"arbeitsplatz: {arbeitsplatz}")
        print(f"pltz_id_bk: {pltz_id_bk}")
        beleg_nr_old = request.form["old_beleg_nr"]
        print(f"beleg_nr_old: {beleg_nr_old}")
        beleg_nr = request.form["gemeinkosten"]
        print(f"beleg_nr: {beleg_nr}")
        kurztext = request.form["kurztext"]
        print(f"kurztext: {kurztext}")
        print("posting")
        if request.form["submit"] == "ändern":  # change selected Auftrag
            ret = gk_ändern(fa_old=beleg_nr_old, userid=userid, anfang_ts=anfang_ts, dauer=dauer)
            if isinstance(ret, str):
                # ende_ts = anfang_ts # initial assignment, gets overrided
                # display error string and cancel booking
                flash(ret)
                return redirect(url_for('home',username=username,))
            else:
                anfang_ts, ende_ts = ret
                print(f"[DLL] anfang_ts: {anfang_ts}, ende_ts: {ende_ts}")
                
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(beleg_nr)
                kt002.PNR_Buch4Clear(1, beleg_nr, sa, '', buaction, GKENDCHECK, '', '', '', '', '')
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(userid)
                actbuchung(ta29nr=userid, sa=sa, AAnfangTS=anfang_ts, AEndeTS=ende_ts, arbeitsplatz=pltz_id_bk, aBem=kurztext)
                return redirect(url_for("gemeinkostenandern", userid=userid))
        
        elif request.form["submit"] == "erstellen":  # create auftrag
            ret = gk_erstellen(userid=userid, dauer=dauer)
            if isinstance(ret, str):
                # display error string and cancel booking
                flash(ret)
                return redirect(url_for('home',username=username,))
            else:
                anfang_ts, ende_ts = ret
                print(f"[DLL] anfang_ts: {anfang_ts}, ende_ts: {ende_ts}")
                
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(beleg_nr)
                kt002.PNR_Buch4Clear(1, beleg_nr, sa, '', buaction, GKENDCHECK, '', '', '', '', '')
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(userid)
                actbuchung(ta29nr=userid, sa=sa, AAnfangTS=anfang_ts, AEndeTS=ende_ts, arbeitsplatz=pltz_id_bk, aBem=kurztext) 
                return redirect(url_for("gemeinkostenandern", userid=userid))

    else:
        dauer=np.linspace(0, 600, num=121).tolist()

        return render_template(
            "gemeinkostenandern.html",
            date=datetime.now(),
            anfangTS=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            auftraglst=auftraglst,
            auftraglst_ajax=auftraglst_ajax,
            sidebarItems=get_list("sidebarItems"),
            username=usernamepd['formatted_name'],
            pers_no=usernamepd['T910_Nr'],
            userid=userid,
            dauer=[int(i) for i in dauer],
            tableItems=get_list("statusTableItems",userid),
            tablecontent=tablecontent
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

    usernamepd = dbconnection.getPersonaldetails(userid)
    username = usernamepd['formatted_name']

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
        show_button_ids=SHOW_BUTTON_IDS,
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/fabuchta55_dialog/<userid>/<menge_soll>/<xFAStatus>/<xFATS>/<xFAEndeTS>/<xScanFA>", methods=["POST", "GET"])
def fabuchta55_dialog(userid, menge_soll, xFAStatus, xFATS, xFAEndeTS, xScanFA):
    """
    Route for Mengendialog for GK/FA where fabuchta55 is appropriate.
    Uses 'mengendialog.html'.

    Args:
        userid: Kartennummer that was input into the inputbar on the identification screen.

    Routes to:
        "home": After user has has submitted Mengen and booking is complete.
        "anmelden": When this route is part of a K/G/A booking process.
    """

    usernamepd = dbconnection.getPersonaldetails(userid)
    username = usernamepd['formatted_name']

    if request.method == 'POST':
        if request.form["submit"] == "submit_end":
            xFAStatus = '30'  # Endrückmeldung
        elif request.form["submit"] == "submit_teil":
            xFAStatus = '20'  # Teilrückmeldung

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
        if ruestzeit == "":
            ruestzeit = 0.0

        xbuchen = True
        tl51use = False
        xScanFA = int(xScanFA)  # make sure dtype is correct
        xVal1, xVal2, xVal3, xVal4, xVal5 = 0.0, 0.0, 0.0, 0.0, 0.0

        if xbuchen:
            # Auftrag in DB schreiben
            xPersNr = kt002.gtv("T910_Nr")
            xTE = kt002.gtv("TA06_TE")
            print(f"[DLL] BuchTa55_3: {xFAStatus, xFATS, xFAEndeTS, kt002.T905_NrSelected, xPersNr, float(menge_gut), float(menge_aus), xTE, float(ruestzeit), lagerplatz, charge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA}")
            kt002.BuchTA55_3(xFAStatus, xFATS, xFAEndeTS, kt002.T905_NrSelected, xPersNr, float(menge_gut), float(menge_aus), xTE,
                             float(ruestzeit), lagerplatz, charge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA)

            # Störung setzen
            if tl51use:
                kt002.BuchTA55_3_TL(xFAEndeTS, kt002.T905_NrSelected)

            # directly add mengendialog for an Auftrag that is now starting, currently not implemented
            # if xInputMengeNew == 1:
                # add another Mengendialog, maybe just reroute with skip?
                # raise NotImplementedError

            kt002.PNR_Buch4Clear(1, userid, '', '', 1, GKENDCHECK, '', '', '', '', '')

        flash("FA oder GK erfolgreich gebucht.")
        logging.info("successful")

        return redirect(url_for('home', username=username))

    return render_template(
        "mengendialog.html",
        date=datetime.now(),
        menge_soll=menge_soll,
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

        xStatusMenge = "20"
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
    xbcancel=0

    xmsg = kt002.EndTA51GKCheck()
    logging.info('result EndTA51GKCheck: ' + xmsg)

    if len(xmsg) > 0:
        xret = "MSG0133" #Vorgang wurde abgebrochen
        if SHOWMSGGEHT == 1:
            print('Info mit Eingabeaufforderung S903_ID=MSG0178 "GK müssen erst beendet werden!"')
            #ok oder no Eingabe
            msgr='ok'
        else:
            print('Info OHNE Eingabeaufforderung S903_ID=MSG0178 "GK müssen erst beendet werden!"')
            #geht mit ok weiter
            msgr='ok'        

    if msgr == 'ok':
        if GKENDCHECK == 1:
            print('dialog GK-Kosten ändern (Platz/Belegnummer/Anfangszeitpunkt/Endezeitpunkt')
            #'Dialog GK-Buchung Editierbar und mit update schließen PNR_TA51GKEndSave noch zu realisieren
                #'anschließend ks001.TA06SetStatusBelegNrN
        else:
            #SQL absetzen
            #Private GK-Aufträge beenden
            #xSql = "exec ksmaster.dbo.kspr_TA51GKEnd2FB1 '" + FirmaNr + "'"
            #xSql = xSql + " ," + PersNr
            #exec sql
            xret = ""
            logging.info('sql')
        
    else:
        xbcancel=1 #nix zu beenden

    # Prüfen ob Fertigungsaufträge und GK-Aufträge laufen
    result = kt002.EndTA51FACheck(xfa, xgk)
    xret, xfa, xgk = result

    if xret is None:
        xret = ''
    logging.info(f'[DLL] endta51cancelt905 xret: {xret}, xfa: {xfa}, xgk: {xgk}')

    # FA sind zu beenden
    if len(xfa) > 0:
        print('Info mit Eingabeaufforderung S903_ID=MSG0132 "Sollen alle laufenden Aufträge ohne Mengeneingabe beendet werden? ok/no"')
        msgr= "ok"
        if msgr == "ok":
            result=kt002.EndTA51Save()
        else:
            xret='false'

    # GK sind zu beenden
    if len(xgk) > 0:
        result = kt002.EndTA51GKSave()
        # xret = "GK"

    return xret


def bufa(ANr="", ATA29Nr="", AFARueckend="", ata22dauer="", aAnfangTS=None, aEndeTS=None, platz=None, aBem=None):
    """Checks whether current GK/FA active in DLL is ok to be booked and decides which fabuchta is appropriate."""
    xFehler=''  
    xbBuchZiel=1
    xScanFA = 0
    xfanr = ''
    xt905nr=''
    
    #Prüfen, ob WB gemacht werden muß
    #nur dann, wenn Arbeitsplatz gelesen worden ist!
    if kt002.CheckObject(kt002.dr_T905) == True:
            print("bufa: drT905 vorhanden")
    #Vor Buchung, prüfen, ob Kst der Person mit der Kst des zu buchenden Arbeitsplatz stimmt! Wenn nicht Wechsebuchung erzeugen!
    #Wechselbuchung triggert auf T955!!
            kt002.BuFAWB(ATA29Nr)

    if kt002.CheckObject(kt002.dr_T905) is True:
        kt002.BuFAWB(ATA29Nr)

    # Auftrag finden
    if kt002.CheckObject(kt002.dr_TA06) is True:
        print('[DLL] bufa CO drta06 exist')
    else:
        # FANr wird gescannt und über T905ArbGRNr oder T909 und Platz Soll wird Beleg gefunden
        # Buchung auf FA_Nr
        if kt002.CheckObject(kt002.dr_TA05) is True:
            xt905nr = kt002.gtv("T905_Nr")
            xfanr = kt002.gtv("TA05_FA_Nr")
            result = kt002.TA06ReadArbGrNr(xfanr, xt905nr)
            print('[DLL] TA06Read' + result)
            if result == 1:
                xScanFA = 1
            else:
                xFehler = xfanr

    if len(xFehler) == 0:
        # Prüfen, ob FA bebucht werden darf
        result = kt002.BuFANr0Status(xbBuchZiel)
        xret, xbBuchZiel = result
        print('[DLL] Bufanrstatus ' + xret + ', Buchzeile ' + str(xbBuchZiel))

        if len(xFehler) == 0:
            if xbBuchZiel == 1:
                xFehler = fabuchta55()
            else:
                xFehler = fabuchta51(ata22dauer=ata22dauer, aAnfangTS=aAnfangTS, aEndeTS=aEndeTS, platz=platz, aBem=aBem)
    else:
        xFehler = ("Kein Auftrag!", ata22dauer)
        if kt002.CheckObject(kt002.dr_TA06) is True and kt002.CheckObject(kt002.dr_TA05) is False:
            xFehler = ("Keine Kopfdaten vorhanden!", ata22dauer)

    return xFehler


def start_booking(nr):
    """Starts the booking process for given card nr."""

    activefkt = ""
    buaction = 7
    bufunktion = 0
    # print('parameters',type(nr), type(activefkt), type(SCANTYPE), type(SHOWHOST), type(SCANON), type(KEYCODECOMPENDE))
    result = kt002.ShowNumber(nr, activefkt, SCANTYPE, SHOWHOST, SCANON, KEYCODECOMPENDE, False, "")
    ret, checkfa, sa = result
    print(f"[DLL] ShowNumber ret: {ret}, checkfa: {checkfa}, sa: {sa}")
    result = kt002.Pruef_PNr(checkfa, nr, sa, bufunktion)
    ret, sa, bufunktion = result
    print(f"[DLL] PruefPNr ret: {ret}, sa: {sa}, bufunktion: {bufunktion}")
        
    result = kt002.Pruef_PNrFkt(nr, bufunktion, SCANTYPE, sa, buaction, APPMSCREEN2, SERIAL, activefkt, "",
                                "", "")
    ret, sa, buaction, activefkt, msg, msgfkt, msgdlg = result
    print(f"[DLL] Pruef_PNrFkt ret: {ret}, sa: {sa}, buaction: {buaction}, activefkt: {activefkt}, msg: {msg}")

    return ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg


def fabuchta55():
	xInputMenge=0 #Flag, 1=Menge eingeben
	xInputMengeNew=0
	xFARueckEnd=False
	xScanFA=0
	xFAStatus=''
	xFATS=''
	xFAEndeTS=''
	xFAMeGut=0.0
	xFAMeGes=0.0
	xFANewScanFA=0
	xFANewStatus=''
	xFANewMeGes=0.0
	xFANewMe=0.0
	xPersNr=0
	xTE =0.0
	xMengeAus=0.0
	xtrman=0.0
	xta11nr=''
	xcharge=''
	xVal1=0.0
	xVal2=0.0
	xVal3=0.0
	xVal4=0.0
	xVal5=0.0
	xbuchen=True
	tl51use=False

	result = kt002.BuchTA55_0(xInputMenge, xInputMengeNew, xFARueckEnd, xScanFA, xFAStatus, xFATS, xFAEndeTS, xFAMeGut, xFAMeGes, xFANewScanFA, xFANewStatus, xFANewMeGes, xFANewMe)
	xret,xInputMenge, xInputMengeNew,xScanFA, xFAStatus, xFATS, xFAEndeTS, xFAMeGut, xFAMeGes, xFANewScanFA, xFANewStatus, xFANewMeGes, xFANewMe=result
	#print("kt002.BuchTA55_0:" + xret + "," + str(xInputMenge) + "," +  str(xInputMengeNew)  + "," + str(xScanFA) + "," +  xFAStatus+ "," +  xFATS + "," +  xFAEndeTS + "," +  str(xFAMeGut+ "," +  str(xFAMeGes) + "," + str(xFANewScanFA) + "," +  xFANewStatus + "," +  str(xFANewMeGes) + "," +  str(xFANewMe))
	print(f"BuchTA55_0: {result}")
	if len(xret) > 0:
		xbuchen=False

	if xInputMenge == 1:
        # return fabuchta55 dialogue here
        # return fabuchta55 dialogue here
		print ("Dialog TA55")
		
		
	if xbuchen == True:
		#Auftrag in DB schreiben
		#xClDetails noch zu lösen
		xPersNr = kt002.gtv("T910_Nr")
		xTE = kt002.gtv("TA06_TE")
		print(f"BuchTA55_3 input: {xFAStatus, xFATS, xFAEndeTS, kt002.T905_NrSelected, xPersNr, xFAMeGut, xMengeAus, xTE, xtrman, xta11nr, xcharge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA}")
		kt002.BuchTA55_3(xFAStatus, xFATS, xFAEndeTS, kt002.T905_NrSelected, xPersNr, xFAMeGut, xMengeAus, xTE, xtrman, xta11nr, xcharge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA)

		#Störung setzen
		#MDEGK_Ruest FA-Nr für Rüsten muß in Global Param definiert sein
		if tl51use == True:
			kt002.BuchTA55_3_TL(xFAEndeTS, kt002.T905_NrSelected)
		
		# Below does not happen for now
		# if xInputMengeNew == 1:
		# 	xMengeAus = 0
		# 	xFATS = Now
		# 	xFAEndeTS = xFATS
		# 	#HIER MENGENDIALOG
		# 	#xbuchen = kt001_InputMenge_Modus(Nothing, ActModus, kt002.dr_TA06BuchNew("TA06_RueckArt"),
		# 	#kt002.dr_TA06BuchNew("TA06_BelegNr"), kt002.dr_TA06BuchNew("TA06_AgBez"), T905_NrSelected, kt002.dr_TA06BuchNew("TA06_Soll_Me"), kt002.dr_TA06BuchNew("TA06_Ist_Me_gut"), kt002.dr_TA06BuchNew("TA06_Ist_Me_Aus") _
		# 	#, xFANewMe, xMengeAus, xtrman, xta11nr, xFANewStatus, xcharge, xVal1, xVal2, xVal3, xVal4, xVal5, xFARueckEnd, xClDetails)

		# 	if xbuchen == True:
		# 		#Auftrag in DB schreiben
		# 		kt002.dr_TA06Buch = kt002.dr_TA06BuchNew
		# 		#xClDetails, 
		# 		xTE = kt002.gtv("TA06_TE")
		# 		kt002.BuchTA55_3(xFANewStatus, xFATS, xFAEndeTS, T905_NrSelected, 0, xFANewMe, xMengeAus, xTE, xtrman, xta11nr, xcharge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA)
	return  xret #fabuchta55


def fabuchta51(nr="", username="", ata22dauer="", aAnfangTS=None, aEndeTS=None, aBem=None, platz=None):
    xStatusMenge = ""
    # if given, set begin and end according to parameter, else assume begin = end = now
    if aAnfangTS is None and aEndeTS is None:
        xEndeTS = datetime.now()
        xAnfangTS = xEndeTS
    else:
        xAnfangTS = datetime.strptime(aAnfangTS, DTFORMAT)
        xEndeTS = datetime.strptime(aEndeTS, DTFORMAT)
    xTS=xAnfangTS.strftime(DTFORMAT)  #Stringtransporter Datum    
    xTSEnd=xEndeTS.strftime(DTFORMAT)

    xTRMan = 0.0
    xTA11Nr = ""
    xCharge = ""
    xDauer = 0
    xVal1 = 0.0
    xVal2 = 0.0
    xVal3 = 0.0
    xVal4 = 0.0
    xVal5 = 0.0
    xbCancel = False

    xTA22Dauer = kt002.gtv("TA22_Dauer")  # aus TA06 gelesen
    if not isinstance(ata22dauer, int):
        if ata22dauer.isnumeric():
            xTA22Dauer = int(ata22dauer)  # if given, take assume this
    else:
        xTA22Dauer = ata22dauer
    print(f"[DLL] PRE BuchTA51_0 xTA22Dauer: {xTA22Dauer}, xTS: {xTS}, xStatusMenge: {xStatusMenge}")
    result = kt002.BuchTA51_0(xTA22Dauer, xTS, xStatusMenge)
    xret, xTS, xStatusMenge = result
    xAnfangTS = datetime.strptime(xTS, DTFORMAT)
    print(f"[DLL] BuchTA51_0 xret: {xret}, xTS: {xTS}, xStatusMenge: {xStatusMenge}")
    if not aAnfangTS is None and not aEndeTS is None and not xTS=="01.01.1900 00:00:00":  # when booking with given Dauer
        xStatusMenge = "20"  # TODO: bug in DLL, temporarily overwrite, 20 means just book, don't validate further

    print("xTS:" + xTS + " Datum:" + xAnfangTS.strftime(DTFORMAT))
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
            xAnfangTS = xAnfangTS.AddSeconds(-1) #1 sekunde wird wieder draufgerechnet!
        else:
            xbCancel = True
            xret = "MSG0133"
 
    if xbCancel is False:
        xta22typ = kt002.gtv("TA22_Typ")
        print("xta22typ:" + xta22typ)
        if kt002.gtv("TA22_Typ") == "7":
            xDialog=True
            if xDialog == True:
                xTSEnd = xEndeTS.strftime("%d.%m.%Y %H:%M:%S")
                xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S") 
                if platz == None:
                    platz = kt002.gtv("T905_Nr")
                kt002.BuchTA51_3( xTSEnd, kt002.gtv("T910_Nr"), kt002.gtv("TA06_FA_Nr"), kt002.gtv("TA06_BelegNr"), xStatusMenge, kt002.gtv("T910_Entlohnung")
                ,platz, kt002.gtv("TA06_TE"), kt002.gtv("TA06_TR"), 0, xMengeGut, xMengeAus, xTRMan, xTA11Nr, xCharge, xVal1, xVal2, xVal3, xVal4, xVal5, kt002.gtv("TA06_FA_Art"), xTS)
                
                #msg0166=Auftrag "_Msg1" wurde gebucht!
                xret = "FA Buchen;MSG0166" + ";" + kt002.gtv("TA06_BelegNr") + ";" + kt002.gtv("TA06_AgBez")
            else:
                # 'EvtMsgDisplay("FA Buchen", "MSG0133", "", "")
                #MSG0133=Vorgang wurde abgebrochen
                xret = "FA Buchen;MSG0133;;"
                         
            # dialogue is needed so reroute to route for Mengendialog
            return redirect(url_for("fabuchta51_dialog", userid=nr))
        else:
            # vorangegangenen Auftrag unterbrechen
            xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")
            t901_nr_print = kt002.gtv("T910_Nr")
            print(f"[DLL] PRE BuchTa51_4_Cancel xTS: {xTS}, T910_Nr: {t901_nr_print}")
            kt002.BuchTA51_4_Cancel(xTS, kt002.gtv("T910_Nr"))

            if kt002.gtv("TA22_Dauer") != 1:
                if aAnfangTS is None and aEndeTS is None:
                    # if not booking with Dauer, add a second for safety (?)
                    xAnfangTS = xAnfangTS + timedelta(seconds = 1) #xAnfangTS.AddSeconds(1)
                xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")
                
                xcl = Generic.Dictionary[String,Object]() #leere liste
                xdmegut = kt002.gtv("TA06_Soll_Me")
                xsmegut = str(xdmegut)
                xmegut=float(xsmegut.replace(",","."))
                if platz == None:
                    platz = kt002.gtv("T905_Nr")
                xret = kt002.BuchTA51_3(xTSEnd, int(kt002.gtv("T910_Nr")), kt002.gtv("TA06_FA_Nr"),
                                        kt002.gtv("TA06_BelegNr"), xStatusMenge, kt002.gtv("T910_Entlohnung"),
                                        platz, kt002.gtv("TA06_TE"), kt002.gtv("TA06_TR"), 0.0,
                                        xmegut, float(0.0), xTRMan, xTA11Nr, xCharge,
                                        xVal1, xVal2, xVal3, xVal4, xVal5, kt002.gtv("TA06_FA_Art"), xTS)

            xret = "FA Buchen;MSG0166" + ";" + kt002.dr_TA06.get_Item("TA06_BelegNr") + ";" + kt002.dr_TA06.get_Item(
                "TA06_AgBez")
    kt002.PNR_Buch4Clear(1, nr, '', '', 1, GKENDCHECK, '', '', '', '', '')
    print(f"Buch4Clear: nr:{nr}, sa:{''}, buaction:{1}")
    flash("FA oder GK erfolgreich gebucht.")
    logging.info("successful")



def actbuchung(ta29nr="", kst="", t905nr="", salast="", kstlast="", tslast="", APlatz="", nr="", username="", sa="", arbeitsplatz=None, ata22dauer="", AAnfangTS=None, AEndeTS=None, aBem=None):
    """K/G/A booking according to sa for user with given card nr and username."""
    xT905Last = ""
    xTA29Last = ""
    xtagid=''
    xkstk=0
    xfaruecknr=''
    xmenge=0
    result = kt002.CheckKommt(sa, kst, salast, kstlast, tslast, xT905Last, xTA29Last)
    xret, ASALast, AKstLast, ATSLast, xT905Last, xTA29Last = result
    print(
        f"[DLL] CheckKommt ret: {xret}, ASALast: {ASALast}, AKstLast: {AKstLast}, ATSLast: {ATSLast}, xT905Last: {xT905Last}, xTA29Last: {xTA29Last}")
    if len(xret) > 0:
        if kt002.CheckObject(kt002.dr_TA06) is True or kt002.CheckObject(kt002.dr_TA05) is True:
            flash("Fehler: Keine Auftragsbuchung ohne Kommt!")
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
                    if SHOWMSGGEHT == True:
                        SBSTools.to020.G_MsgSuppress = MsgSuppress.NoSuppress
                        xMsgBox = to001_Msg.Msg(MsgType.mtWarning, Nothing, "MSG0194", "kt001 - Pruef_AgNr", "", "", MessageBoxButtons.OK, MessageBoxDefaultButton.Button1, xmld_S903)
                    else:
                        SBSTools.to020.G_MsgSuppress = MsgSuppress.Auto #'von alleine wieder schließen
                        xMsgBox = to001_Msg.Msg(MsgType.mtWarning, Nothing, "MSG0194", "kt001 - Pruef_AgNr", "", "", MessageBoxButtons.OK, MessageBoxDefaultButton.Button1, xmld_S903)
                    if SHOWMSGGEHT == True:
                        SBSTools.to020.G_MsgSuppress = MsgSuppress.NoSuppress
                        xMsgBox = to001_Msg.Msg(MsgType.mtWarning, Nothing, "MSG0194", "kt001 - Pruef_AgNr", "", "", MessageBoxButtons.OK, MessageBoxDefaultButton.Button1, xmld_S903)
                    else:
                        SBSTools.to020.G_MsgSuppress = MsgSuppress.Auto #'von alleine wieder schließen
                        xMsgBox = to001_Msg.Msg(MsgType.mtWarning, Nothing, "MSG0194", "kt001 - Pruef_AgNr", "", "", MessageBoxButtons.OK, MessageBoxDefaultButton.Button1, xmld_S903)

                    xFehler = "MSG0137" #'Auftrag wurde nicht erfaßt!                    
                    xFehler = "MSG0137" #'Auftrag wurde nicht erfaßt!                    
                    print("[DLL] abweichender Platz, umbuchen nicht erlaubt")
                    flash("Abweichender Platz, Umbuchen nicht erlaubt!")
                    return redirect(url_for("home", username=username))

        if len(xret) == 0:
            if kt002.CheckObject(kt002.dr_T905) is False:
                if kt002.CheckObject(kt002.dr_T951) is True:
                    kt002.T905Read(kt002.gtv("T951_Arbist"))

            kt002.T905_NrSelected = kt002.gtv("T905_Nr")
            xret = bufa(ANr=kt002.gtv("TA06_BelegNr"), ata22dauer=ata22dauer, aAnfangTS=AAnfangTS, aEndeTS=AEndeTS, platz=arbeitsplatz, aBem=aBem)
            return redirect(url_for("home", username=username))

    if len(xret) == 0:
        result = kt002.PNR_Buch(sa, kst, t905nr, ta29nr, APlatz, xtagid, xkstk)
        xret, ASA, AKst, APlatz, xtagid, xkstk = result
        
        if len(xret) == 0:
            if ASA == "K":
                if xkstk == 2:
                    #'xplatz = PYTHON Auswahl Platz
                    print ('Auswahl Platz')
                    xplatz='0006'
                return redirect(url_for(
                    'anmelden',
                    userid=nr,
                    sa=sa
                ))               
            elif ASA == "G":
                if SHOWMSGGEHT == 1:
                    if GKENDCHECK is True:  # Param aus X998 prüfen laufende Aufträge
                        xret = kt002.PNR_Buch2Geht()
                    logging.info("Already Logged In")
                    flash("User wurde abgemeldet.")
            elif ASA == 'A':
                # result = kt002.PNR_Buch(sa, '', t905nr, '', '', '', 0)
                # xret, ASA, AKst, APlatz, xtagid, xkstk = result
                flash(arbeitsplatz)
                logging.debug(f"[DLL] booked Arbeitsplatz: {arbeitsplatz}")

            if len(xret) == 0:
                kt002.PNR_Buch3(xtagid, ASA, AKst, APlatz, ta29nr, xfaruecknr, xmenge)
            kt002.PNR_Buch4Clear(1, nr, sa, '', 1, GKENDCHECK, '', '', '', '', '')

        return redirect(url_for("home", username=username))


def ta06gkend(userid,AScreen2=None):
	
	xMsg = kt002.EndTA51GKCheck()
	if len(xMsg) == 0:
		flash("Keine GK zu Beenden") # Es gibt keine Gemeinkostenaufträge zu beenden!  || nothing to terminate
	else:
		ret = dbconnection.doGKBeenden(userid)
		if ret==True:
			flash("Laufende Aufträge beendet")
		else:
			flash("GK konnten nicht beendet werden!")
            
        
def gk_ändern(fa_old, userid, anfang_ts, dauer):
	# Change existing Auftragsbuchung, TODO: somehow return error when no GK to delete is found
	ret = dbconnection.doGKLoeschen(fa_old, userid, anfang_ts)  # delete old booking with BelegNr=scanvalue and Anfang=Anfangts
	persnr = dbconnection.getPersonaldetails(userid)["T910_Nr"]
	if dauer > 0:
		# add back booking with correct dauer
		anfang_ts, ende_ts = dbconnection.doFindTS(persnr, dauer)  # find suitable begin and end for new Auftrag
		if anfang_ts is None and ende_ts is None:
			ret = dbconnection.doUndoDelete(fa_old, userid)
			if not ret is None:
				return "Keine neue Zeitperiode gefunden und Auftrag konnte nicht wiederhergestellt werden!"
			return "Keine neue Zeitperiode gefunden!"
		return anfang_ts, ende_ts
	else:
		# dauer == 0 meaning no new booking, just delete old
		# result = kt002.PNR_Buch4Clear(1, scanvalue, sa, platz, buaction, gkendcheck, activefkt, msgfkt, msgbuch, msgzeit, msgpers)
		return "Nur gelöscht"


def gk_erstellen(userid, dauer):
	# create Auftragsbuchung with Dauer
	persnr = dbconnection.getPersonaldetails(userid)["T910_Nr"]
	anfang_ts, ende_ts = dbconnection.doFindTS(persnr, dauer)
	if anfang_ts is None and ende_ts is None:
		return "Keine neue Zeitperiode gefunden!"
	else:
		return anfang_ts, ende_ts


def get_list(listname, userid=None):
    """Getter function for various lists needed for display in the app."""

    if listname == "arbeitsplatzgruppe":
        # Implement database calls here.
        return ["Frontenlager", "Verschiedenes(bundes)", "Lehrwerkstatt", "AV(Bunde)"]

    if listname == "arbeitsplatz":
        arbeitsplatz_info = dbconnection.getArbeitplazlist()
        return [arbeitsplatz_info['T905_bez'], arbeitsplatz_info['T905_Nr']]

    if listname == "arbeitsplatzbuchung":
        persnr, arbeitsplatz, fanr = dbconnection.getArbeitplatzBuchung()
        return [persnr, arbeitsplatz, fanr]
    
    if listname == "gruppenbuchung_faNr":
        fanr = dbconnection.getGruppenbuchungFaNr()
        return fanr

    if listname == "gruppe":
        gruppe = dbconnection.getGruppenbuchungGruppe()
        return gruppe


    if listname == "fertigungsauftrag_frNr":
        return [1067, 2098, 7654, 2376, 8976]

    if listname == "gemeinkostenandern_frNr":
        return [1067, 2098, 7654, 2376, 8976]

    if listname == "statusTableItems":
        upper_items_df, lower_items_df = dbconnection.getStatustableitems(userid)
        # create html tags out of the above data frames
        upper_items_html = upper_items_df.to_html(classes="table table-striped", index=False, justify="left").replace('border="1"','border="0"')
        lower_items_html = lower_items_df.to_html(classes="table table-striped", index=False, justify="left").replace('border="1"','border="0"')
        return [upper_items_html, lower_items_html]

    if listname == "homeButtons":
        return [["Wechselbuchung", "Gemeinkosten", "Status", "Gemeinkosten Beenden", "Bericht drucken",
                 "Gemeinkosten ändern", "Arbeitsplatzbuchung", "Gruppenbuchung", "FA erfassen"],
                ["arbeitsplatzwechsel", "gemeinkosten_buttons", "status", "gemeinkostenbeenden", "berichtdrucken",
                 "gemeinkostenandern", "arbeitsplatzbuchung", "gruppenbuchung", "fertigungsauftragerfassen"]]

    if listname == "gemeinkostenItems":
        gk_info = dbconnection.getGemeinkosten(userid)
        return [gk_info["TA05_ArtikelBez"], gk_info["TA06_BelegNr"]]

    if listname == "sidebarItems":
        return [["Wechselbuchung", "Gemeinkosten", "Status", "Gemeinkosten Beenden", "Bericht drucken",
                 "Gemeinkosten ändern", "Arbeitsplatzbuchung", "Gruppenbuchung", "FA erfassen"],
                ["arbeitsplatzwechsel", "gemeinkosten_buttons", "status", "gemeinkostenbeenden", "berichtdrucken",
                 "gemeinkostenandern", "arbeitsplatzbuchung", "gruppenbuchung", "fertigungsauftragerfassen"]]
