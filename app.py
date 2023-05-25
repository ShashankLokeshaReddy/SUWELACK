import os
import sys
import xml.etree.ElementTree as ET

from flask import Flask
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import PickleType
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length
from flask_wtf import FlaskForm

from datetime import datetime, timedelta
from dateutil import parser
import time

import dbconnection
import logging
logging.basicConfig(level=logging.INFO)

from flask_babel import Babel, format_datetime, gettext

import clr
import System
import pandas as pd
import ctypes
from ctypes import *
import numpy as np
import pandas as pd

# CONSTANTS
verwaltungsterminal = True   # variable to show Gruppen field in the UI or not
root  = {}
DTFORMAT = "%d.%m.%Y %H:%M:%S"
DFORMAT = "%d.%m.%Y"
ROOT_DIR = "C:\\Users\\MSSQL\\PycharmProjects\\suwelack\\"  # directory which directly contains app.py
APPMSCREEN2 = True  # bool(int(root.findall('X998_StartScreen2')[0].text)) # X998_STARTSCREEN2
SHOWMSGGEHT = {} # X998_ShowMsgGeht
GKENDCHECK = {} # X998_GKEndCheck
BTAETIGKEIT = {} # X998_TAETIGKEIT
FirmaNr = {}
X998_GrpPlatz = {}
SCANTYPE = True  # root.findall('X998_SCANNER')[0].text # X998_SCANNER TS,CS,TP
SCANON = True  # Scansimulation an
KEYCODECOMPENDE = ""  # Endzeichen Scanwert
SHOWHOST = False  # Anzeige Hostinformation im Terminal
SERIAL = True
SCANCARDNO = True
T905ALLOWROUTE = True
ROUTEDIALOG = True
SHOW_BUTTON_IDS = False  # If true, show Arbeitsplatz and GK IDs after their name for debugging

sys.path.append("dll/bin")

clr.AddReference("kt002_PersNr")
clr.AddReference("System.Collections")

dll_ref1 = System.Reflection.Assembly.LoadFile(ROOT_DIR+"dll\\bin\\kt002_PersNr.dll")
type1 = dll_ref1.GetType('kt002_persnr.kt002')
instance1 = System.Activator.CreateInstance(type1)

from System.Collections import Generic
from System.Collections import Hashtable
from System import String
from System import Object
from System import Type
import shutil

os.chdir("dll/bin")
instance1.Init()
instance1.InitTermConfig()

app = Flask(__name__, template_folder="templates")
app.debug = True
app.secret_key = "suwelack"
app.config['BABEL_DEFAULT_LOCALE'] = 'de'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
babel = Babel(app)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    dll_path = db.Column(db.String(100))  # define the dll_path attribute
    dll_path_data = db.Column(db.String(100))

with app.app_context():
    db.create_all()

# create a dictionary to store the dll instances for each logged in user
dll_instances = {}

# Function to create a copy of the DLL for a given user
def create_dll_copy(username):
    src_path_data = ROOT_DIR+"dll\\data\\X998.xml"
    dest_path_data = ROOT_DIR+f"dll\\data\\X998{username}.xml"
    shutil.copyfile(src_path_data, dest_path_data)
    src_path = ROOT_DIR+"dll\\bin\\kt002_PersNr.dll"
    dest_path = ROOT_DIR+f"dll\\bin\\kt002_PersNr{username}.dll"
    shutil.copyfile(src_path, dest_path)
    return dest_path_data, dest_path

# Function to delete the DLL copy for a given user
def delete_dll_copy(user):
    if os.path.exists(user.dll_path):
        os.remove(user.dll_path)
    else:
        print(user.dll_path ,"DLL-Datei wurde nicht gelöscht")
    if os.path.exists(user.dll_path_data):
        os.remove(user.dll_path_data)
    else:
        print(user.dll_path_data ,"DLL-Datei wurde nicht gelöscht")
        
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

    def validate(self, extra_validators=None):
        rv = super(LoginForm, self).validate()
        if not rv:
            return False

        user = User.query.filter_by(username=self.username.data).first()
        if user and check_password_hash(user.password, self.password.data):
            dll_path = user.dll_path
            dll_path_data = user.dll_path_data
            if dll_path and os.path.exists(dll_path) and dll_path_data and os.path.exists(dll_path_data):
                dll_ref = System.Reflection.Assembly.LoadFile(dll_path)
                type = dll_ref.GetType('kt002_persnr.kt002')
                instance = System.Activator.CreateInstance(type)
                dll_instances[user.username] = instance
                instance.Init()
                instance.InitTermConfig()
                root[user.username] = ET.parse(f"../../dll/data/X998{user.username}.xml").getroot()[0]  # parse X998.xml file for config
                SHOWMSGGEHT[user.username]  = bool(int(root[user.username].findall('X998_ShowMsgGeht')[0].text))  # X998_ShowMsgGeht
                GKENDCHECK[user.username]  = bool(int(root[user.username].findall('X998_GKEndCheck')[0].text))  # X998_GKEndCheck
                BTAETIGKEIT[user.username]  = bool(int(root[user.username].findall('X998_Taetigkeit')[0].text))  # X998_TAETIGKEIT
                FirmaNr[user.username]  = root[user.username].findall('X998_FirmaNr')[0].text  # X998_GKEndCheck
                X998_GrpPlatz[user.username]  = root[user.username].findall('X998_GrpPlatz')[0].text  # X998_TAETIGKEIT
                print(FirmaNr, X998_GrpPlatz)
                return True

        return False

@app.route('/index')
def index():
    return render_template('index.html', buttonValues=get_list("homeButtons"), sidebarItems=get_list("sidebarItems"))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if db.session.query(User).filter_by(username=form.username.data).count() < 1:
            hashed_password = generate_password_hash(form.password.data, method='sha256')
            new_user = User(username=form.username.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            dll_path_data, dll_path = create_dll_copy(new_user.username)
            new_user.dll_path = dll_path
            new_user.dll_path_data = dll_path_data
            db.session.commit()
            flash('Sie haben sich erfolgreich registriert!')
        else:
            flash('Benutzer existiert bereits!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form, buttonValues=get_list("homeButtons"), sidebarItems=get_list("sidebarItems"))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
        flash('ungültiger Benutzername oder Passwort')
    return render_template('login.html', form=form, buttonValues=get_list("homeButtons"), sidebarItems=get_list("sidebarItems"))

@app.route('/dashboard')
@login_required
def dashboard():
    users = User.query.all()
    return render_template('dashboard.html', users=users, buttonValues=get_list("homeButtons"), sidebarItems=get_list("sidebarItems"))

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    form = RegistrationForm()
    user = User.query.get(user_id)
    if user:
        if form.validate_on_submit():
            user.username = form.username.data
            user.password = generate_password_hash(form.password.data, method='sha256')
            db.session.commit()
            flash('Benutzer erfolgreich aktualisiert!')
            return redirect(url_for('dashboard'))
        else:
            form.username.data = user.username
            return render_template('register.html', form=form, buttonValues=get_list("homeButtons"), sidebarItems=get_list("sidebarItems"))
    else:
        flash('Benutzer nicht gefunden')
        return redirect(url_for('dashboard'))

@app.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        delete_dll_copy(user)
        flash('Benutzer erfolgreich gelöscht!')
    else:
        flash('Benutzer nicht gefunden')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    # Delete the dll_instance for the logged out user
    del dll_instances[current_user.username]
    logout_user()
    return redirect(url_for('index'))

# @babel.localeselector
# def get_locale():
#     return 'de'

@app.route("/", methods=["POST", "GET"])
@login_required
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
        username = None
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
                    dll_instances[current_user.username].PNR_Buch4Clear(1, nr, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
                    print(f"[DLL] Buch4Clear: nr:{nr}, sa:{sa}, buaction:{buaction}")
                    return redirect(url_for("identification", page="_auftragsbuchung"))
                if username is None:
                    # handle the case where username is not valid
                    flash("Ungültiger Benutzername")
                    return redirect(url_for("home"))
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
@login_required
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
            dll_instances[current_user.username].T905Read(selectedArbeitsplatz)
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
@login_required
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
        dll_instances[current_user.username].PNR_Buch4Clear(1, selected_gk, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
        print(f"[DLL] Buch4Clear: nr:{selected_gk}, sa:{sa}, buaction:{buaction}")

        ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(userid)  # start again with userid
        return actbuchung(nr=userid, username=username, sa=sa)

    return render_template(
        "gemeinkostenbuttons.html",
        title="Gemeinkosten",
        date=datetime.now(),
        buttonText=get_list("gemeinkostenItems", userid=userid),
        show_button_ids=SHOW_BUTTON_IDS,
        sidebarItems=get_list("sidebarItems")
    )
    

@app.route("/zaehlerstand_buttons/<userid>", methods=["POST", "GET"])
@login_required
def zaehlerstand_buttons(userid):
    """
    Route for choosing Zähler as Buttons.
    Uses 'gemeinkostenbuttons.html'.

    Args:
        userid: Kartennummer that was input into the inputbar on the identification screen.

    Routes to:
        TODO
    """

    usernamepd = dbconnection.getPersonaldetails(userid)
    username = usernamepd['formatted_name']

    if request.method == 'POST':
        # Retrieve the value of selected button from frontend
        selected_zs = request.form["gemeinkostenbuttons"]
        selected_zs, zs_name = selected_zs.split(",")
        logging.info(f"Zählerstand: {selected_zs, zs_name}")

        ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(selected_zs)  # start with GK nr
        dll_instances[current_user.username].PNR_Buch4Clear(1, selected_zs, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
        print(f"[DLL] Buch4Clear: nr:{selected_zs}, sa:{sa}, buaction:{buaction}")

        ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(userid)  # start again with userid
        return actbuchung(nr=userid, username=username, sa=sa)

    return render_template(
        "gemeinkostenbuttons.html",
        title="Zählerstände",
        date=datetime.now(),
        buttonText=get_list("zaehlerItems", userid=userid),
        show_button_ids=SHOW_BUTTON_IDS,
        sidebarItems=get_list("sidebarItems")
    )
    
    
@app.route("/arbeitsplatzbuchung/<userid>", methods=["POST", "GET"])
@login_required
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
        Belegnr = dbconnection.getBelegNr(FA_Nr, Platz, FirmaNr[current_user.username])
        if Belegnr == "error":
            flash("GK Auftrag für diesen Platz nicht definiert!")
            dll_instances[current_user.username].PNR_Buch4Clear(1, userid, '', '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
            return redirect(url_for("arbeitsplatzbuchung", userid=userid))
        ret = dll_instances[current_user.username].TA06Read(Belegnr)  # prese the BelegNr in the DLL
        if ret == False:
            dll_instances[current_user.username].TA06ReadPlatz(Belegnr, Platz) 
        ret = gk_erstellen(userid, dauer, TagId)  # find time window
        if isinstance(ret, str):
            flash(ret)
            dll_instances[current_user.username].PNR_Buch4Clear(1, userid, '', '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
            return redirect(url_for("arbeitsplatzbuchung", userid=userid))
        if not isinstance(ret, str):
            anfang_ts, ende_ts = ret  
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(Belegnr) 
            dll_instances[current_user.username].PNR_Buch4Clear(1, Belegnr, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(str(userid))
            return actbuchung(nr=userid, username=username, sa=sa, AAnfangTS=anfang_ts,AEndeTS=ende_ts)
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
            return actbuchung(nr=userid, username=username, sa=sa, endroute="home")
        
        if page == "gemeinkostenbeenden":
            usernamepd = dbconnection.getPersonaldetails(userid)
            username = usernamepd['formatted_name']
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg =start_booking(userid)
            ta06gkend(userid=userid)
            dll_instances[current_user.username].PNR_Buch4Clear(1, userid, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
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
@login_required
def status(userid):
    return render_template(
        "status.html",
        tableItems=get_list("statusTableItems",userid),
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/berichtdrucken/<userid>", methods=["POST", "GET"])
@login_required
def berichtdrucken(userid):
    return render_template(
        "berichtdrucken.html",
        arbeitsplatzgruppe=get_list("arbeitsplatzgruppe"),
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/gruppenbuchung/<userid>", methods=["POST", "GET"])
@login_required
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
        person_list = dbconnection.getGroupMembers(GruppeNr, TagId, FirmaNr[current_user.username])  # get all persons from this group
        person_nrs = [round(x) for x in person_list['T951_PersNr'].tolist()]
        
        for per_nr in person_nrs:
            userid = dbconnection.getUserID(per_nr)
            Platz = dbconnection.getLastbooking(userid).loc[0,'T951_ArbIst']
            Belegnr = dbconnection.getBelegNr(FA_Nr, Platz, FirmaNr[current_user.username])
            if Belegnr == "error":
                flash("GK Auftrag für diesen Platz nicht definiert!")
                continue
            ret = dll_instances[current_user.username].TA06Read(Belegnr)  # prese the BelegNr in the DLL
            if ret == False: 
                dll_instances[current_user.username].TA06ReadPlatz(Belegnr, Platz)
            ret = gk_erstellen(userid, dauer, TagId) # find time window
            if isinstance(ret, str):
                flash(ret)
                dll_instances[current_user.username].PNR_Buch4Clear(1, userid, sa, '', 1, GKENDCHECK, '', '', '', '', '')
                return redirect(url_for("home",userid=userid))
            if not isinstance(ret, str):
                anfang_ts, ende_ts = ret
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(Belegnr)  # GK ändern booking, this is the new GK BelegNr
                dll_instances[current_user.username].PNR_Buch4Clear(1, Belegnr, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(str(userid))
                actbuchung(nr=userid, username=username, sa=sa, AAnfangTS=anfang_ts, AEndeTS=ende_ts)
                time.sleep(1)  # make sure database has time to catch up
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
@login_required
def fertigungsauftragerfassen(userid):
    usernamepd = dbconnection.getPersonaldetails(userid)
    username=usernamepd['formatted_name']
    platz=dbconnection.getPlazlistFAE(userid, FirmaNr[current_user.username], datetime.now().strftime("%Y-%m-%dT00:00:00"))
    platzid=platz.T905_Nr.tolist()
    platzlst= platz.T905_Bez.tolist()
    auftraglst = []
    auftraglst_ajax = []
    tablecontent = []
    for i in range(len(platzid)):
        auftrag=dbconnection.getAuftrag(platzid[i], "FA_erfassen", FirmaNr[current_user.username])
        if auftrag.empty:
            auftraglst.insert(0,[platzid[i],platzlst[i],"",""])
            auftraglst_ajax.insert(0,{'id':platzid[i],'platz':platzlst[i],'belegNr':"",'bez':""})
        else:    
            auftraglst.insert(0,[platzid[i],platzlst[i],auftrag.TA06_BelegNr.tolist()[0],auftrag.Bez.tolist()[0]])
            auftraglst_ajax.insert(0,{'id':platzid[i],'platz':platzlst[i],'belegNr':auftrag.TA06_BelegNr.tolist()[0],'bez':auftrag.Bez.tolist()[0]})               
    
        tableitem=dbconnection.getTables_GKA_FAE(userid, platzid[i], "FA_erfassen", FirmaNr[current_user.username])
        if not tableitem.empty:
            for index, row in tableitem.iterrows():
                tableobj={'TagId':row['TA51_TagId'].strftime("%d-%m-%Y"), 'Arbeitplatz':row['TA51_Platz_ist'], 'BelegNr':row['TA51_BelegNr'], 'AnfangTS':row['TA51_AnfangTS'].strftime("%d-%m-%Y %H:%M:%S"), 'EndeTS':row['TA51_EndeTS'].strftime("%d-%m-%Y %H:%M:%S"), 'DauerTS':row['TA51_DauerTS'], 'MengeGut':row['TA51_MengeIstGut'], 'Auf_Stat':row['TA51_Auf_Stat']}
                tablecontent.insert(0,tableobj)
    auftraglst.insert(0, ["","Keine","",""])
    auftraglst_ajax.insert(0,{'id':"",'platz':"Keine",'belegNr':"",'bez':""})
    
    if request.method == 'POST':
        print("posting")
        if request.form["submit"] == "erstellen": 
            datum = request.form["datum"]
            arbeitsplatz = request.form["arbeitsplatz"]
            beleg_nr = request.form["auftrag"]
            # beleg_nr = "FA00300150" # TODO: bug here -> works only for this value
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(beleg_nr)
            dll_instances[current_user.username].PNR_Buch4Clear(1, beleg_nr, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
            if bufunktion == 3:
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(userid)
                return actbuchung(nr=userid, sa=sa, endroute="fertigungsauftragerfassen")
            else:
                flash("Buchung fehlgeschlagen")
                dll_instances[current_user.username].PNR_Buch4Clear(1, userid, sa, '', 1, GKENDCHECK, '', '', '', '', '')
                return redirect(url_for('home',username=username,))
    else:
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
@login_required
def gemeinkostenandern(userid):
    usernamepd = dbconnection.getPersonaldetails(userid)
    df=dbconnection.getTables_GKA_FAE(userid, None, "GK_ändern", FirmaNr[current_user.username])
    usernamepd = dbconnection.getPersonaldetails(userid)
    username=usernamepd['formatted_name']

    auftraglst = []
    auftraglst_ajax = []
    tablecontent = []
    for index, row in df.iterrows():
        item = {'TagId':row['TA51_TagId'].strftime("%Y-%m-%d"), 'Arbeitplatz':row['TA51_Platz_ist'], 'BelegNr':row['TA51_BelegNr'], 'AnfangTS':row['TA51_AnfangTS'].strftime("%Y-%m-%dT%H:%M:%S"), 'EndeTS':row['TA51_EndeTS'].strftime("%Y-%m-%dT%H:%M:%S"), 'DauerTS':row['TA51_DauerTS'], 'Anfang':row['TA51_Anfang'].strftime("%Y-%m-%dT%H:%M:%S"), 'Ende':row['TA51_Ende'].strftime("%Y-%m-%dT%H:%M:%S"), 'Dauer':row['TA51_Dauer'], 'Kurztext':row['TA51_Bemerkung']}
        tablecontent.insert(0,item)
        auftraglst_temp = []
        auftraglst_ajax_temp = []
        platz = dbconnection.getPlazlistGKA(userid, row['TA51_TagId'].strftime("%Y-%m-%dT00:00:00"), FirmaNr[current_user.username])
        platzid = platz.T905_Nr.tolist()
        platzlst = platz.T905_Bez.tolist()
        for i in range(len(platzid)):
            auftrag=dbconnection.getAuftrag(platzid[i], "GK_ändern", FirmaNr[current_user.username])
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
    
    if request.method == 'POST':
        datum = request.form["datum"]
        print(f"datum: {datum}")
        dauer = int(request.form["dauer"])
        print(f"dauer: {dauer}")
        anfang_ts = request.form["anfangTS"]
        print(f"anfangTS: {anfang_ts}")
        if datum == "":
            datum = anfang_ts
        date_string = parser.parse(datum)
        TagId = date_string.strftime("%Y-%m-%dT00:00:00")
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
            ret = gk_ändern(fa_old=beleg_nr_old, userid=userid, anfang_ts=anfang_ts, dauer=dauer, date=TagId)
            if isinstance(ret, str):
                # display error string and cancel booking
                flash(ret)
                dll_instances[current_user.username].PNR_Buch4Clear(1, userid, sa, '', 1, GKENDCHECK, '', '', '', '', '')
                return redirect(url_for('home',username=username,))
            else:
                anfang_ts, ende_ts = ret
                print(f"[DLL] anfang_ts: {anfang_ts}, ende_ts: {ende_ts}")
                
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(beleg_nr)
                dll_instances[current_user.username].PNR_Buch4Clear(1, beleg_nr, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(userid)
                actbuchung(nr=userid, sa=sa, AAnfangTS=anfang_ts, AEndeTS=ende_ts, arbeitsplatz=pltz_id_bk, aBem=kurztext)
                return redirect(url_for("gemeinkostenandern", userid=userid))
        
        elif request.form["submit"] == "erstellen":  # create auftrag
            ret = gk_erstellen(userid=userid, dauer=dauer, date=TagId)
            if isinstance(ret, str):
                # display error string and cancel booking
                flash(ret)
                dll_instances[current_user.username].PNR_Buch4Clear(1, userid, sa, '', 1, GKENDCHECK, '', '', '', '', '')
                return redirect(url_for('home',username=username,))
            else:
                anfang_ts, ende_ts = ret
                print(f"[DLL] anfang_ts: {anfang_ts}, ende_ts: {ende_ts}")
                
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(beleg_nr)
                dll_instances[current_user.username].PNR_Buch4Clear(1, beleg_nr, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(userid)
                actbuchung(nr=userid, sa=sa, AAnfangTS=anfang_ts, AEndeTS=ende_ts, arbeitsplatz=pltz_id_bk, aBem=kurztext) 
                return redirect(url_for("gemeinkostenandern", userid=userid))

    else:
        dauer=np.linspace(0, 600, num=601).tolist()

        return render_template(
            "gemeinkostenandern.html",
            date=datetime.now(),
            anfangTS=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
@login_required
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

        result = dll_instances[current_user.username].PNR_Buch(sa, '', selectedArbeitplatz, '', '', '', 0)
        xret, ASA, AKst, APlatz, xtagid, xkstk = result

        if len(xret) == 0:
            dll_instances[current_user.username].PNR_Buch3(xtagid, ASA, AKst, APlatz, '', '', 0)
            result = dll_instances[current_user.username].PNR_Buch4Clear(1, userid, sa, '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
        
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

@app.route("/fabuchta56_dialog/<userid>/<old_total>/<platz>/<belegnr>", methods=["POST", "GET"])
@login_required
def fabuchta56_dialog(userid, old_total, platz, belegnr):
    """
    TODO
    """
    usernamepd = dbconnection.getPersonaldetails(userid)
    username = usernamepd['formatted_name']

    if request.method == 'POST':
        xScanFA=0
        xFAStatus=''
        xPersNr=0
        xTE =0.0
        xMengeAus=0.0
        xtrman=0.0
        xta11nr=''
        xcharge=''
        xVal2=0.0
        xVal3=0.0
        xVal4=0.0
        xVal5=0.0
        xbuchen=True

        if dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_T910) == True:
            xPersNr = int(dll_instances[current_user.username].gtv("T910_Nr"))
        if dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_TA06) == True:
            xTE = dll_instances[current_user.username].gtv("TA06_TE")
        
        new_total = int(float(request.form["new_total"]))
        date_string = parser.parse(request.form["datum"])
        xMengeGut = int(new_total) - int(old_total) # Difference = new_total - old_total
        xMengeAus = 0
        hour = int(request.form["uhrzeit"])
        xTS = date_string.strftime(f"%d.%m.%Y {hour}:00:00")  #Stringtransporter Datum 
        
        if xbuchen == True:
            print(f"[DLL] BuchTA56_3: ", xFAStatus, xTS, platz, xPersNr, xMengeGut, xMengeAus, xTE, xtrman,
                                                            xta11nr, xcharge, new_total, xVal2, xVal3, xVal4, xVal5, xScanFA)
            dll_instances[current_user.username].BuchTA56_3(xFAStatus, xTS, platz, xPersNr, xMengeGut, xMengeAus, xTE, xtrman,
                                                            xta11nr, xcharge, new_total, xVal2, xVal3, xVal4, xVal5, xScanFA)
            dll_instances[current_user.username].PNR_Buch4Clear(1, userid, '', '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')

        flash("Zählerstand erfolgreich zurückgemeldet.")
        return redirect(url_for('zaehlerstand_buttons', userid=userid))
    
    return render_template(
        "zaehlerdialog.html",
        date=datetime.now(),
        old_total=float(old_total),
        belegnr=belegnr,
        uhrzeit=list(range(1,25)),
        sidebarItems=get_list("sidebarItems")
    )

@app.route("/fabuchta55_dialog/<userid>/<menge_soll>/<xFAStatus>/<xFATS>/<xFAEndeTS>/<xScanFA>/<endroute>", methods=["POST", "GET"])
@login_required
def fabuchta55_dialog(userid, menge_soll, xFAStatus, xFATS, xFAEndeTS, xScanFA, endroute):
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

        # aus_fehler = request.form["aus_fehler"]
        # aus_oberflaeche = request.form["aus_oberflaeche"]
        # aus_stapel = request.form["aus_stapel"]
        # aus_kanten = request.form["aus_kanten"]

        # div_aus_fehler = request.form["div_aus_fehler"]
        # div_aus_oberflaeche = request.form["div_aus_oberflaeche"]
        # div_aus_stapel = request.form["div_aus_stapel"]
        # div_aus_kanten = request.form["div_aus_kanten"]

        # try:
        #     if menge_aus == "":  # menge_aus not defined, given split up into reasons
        #         menge_aus = sum([float(aus_fehler), float(aus_oberflaeche), float(aus_stapel), float(aus_kanten)])
        # except ValueError:
        #     menge_aus = 0.0
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
            xPersNr = dll_instances[current_user.username].gtv("T910_Nr")
            xTE = dll_instances[current_user.username].gtv("TA06_TE")
            print(f"[DLL] BuchTa55_3: {xFAStatus, xFATS, xFAEndeTS, dll_instances[current_user.username].T905_NrSelected, xPersNr, float(menge_gut), float(menge_aus), xTE, float(ruestzeit), lagerplatz, charge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA}")
            dll_instances[current_user.username].BuchTA55_3(xFAStatus, xFATS, xFAEndeTS, dll_instances[current_user.username].T905_NrSelected, xPersNr, float(menge_gut), float(menge_aus), xTE,
                             float(ruestzeit), lagerplatz, charge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA)

            # Störung setzen
            if tl51use:
                dll_instances[current_user.username].BuchTA55_3_TL(xFAEndeTS, dll_instances[current_user.username].T905_NrSelected)

            # directly add mengendialog for an Auftrag that is now starting, currently not implemented
            # if xInputMengeNew == 1:
                # add another Mengendialog, maybe just reroute with skip?
                # raise NotImplementedError

            dll_instances[current_user.username].PNR_Buch4Clear(1, userid, '', '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')

        flash("FA erfolgreich gebucht.")
        logging.info("successful")

        if endroute == "home":
            return redirect(url_for('home', username=username))
        else:
            return redirect(url_for("fertigungsauftragerfassen", userid=userid))

    return render_template(
        "mengendialog.html",
        date=datetime.now(),
        menge_soll=menge_soll,
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/fabuchta51_dialog/<userid>/", methods=["POST", "GET"])
@login_required
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
        dll_instances[current_user.username].BuchTA51_3(xTSEnd, dll_instances[current_user.username].gtv("T910_Nr"), dll_instances[current_user.username].gtv("TA06_FA_Nr"), dll_instances[current_user.username].gtv("TA06_BelegNr"),
                         xStatusMenge, dll_instances[current_user.username].gtv("T910_Entlohnung"), dll_instances[current_user.username].gtv("T905_Nr"),
                         dll_instances[current_user.username].gtv("TA06_TE"), dll_instances[current_user.username].gtv("TA06_TR"), 0, float(menge_gut), float(menge_aus),
                         float(ruestzeit), lagerplatz, charge,
                         xVal1, xVal2, xVal3, xVal4, xVal5, dll_instances[current_user.username].gtv("TA06_FA_Art"), xTS)

        xret = "FA Buchen;MSG0166" + ";" + dll_instances[current_user.username].gtv("TA06_BelegNr") + ";" + dll_instances[current_user.username].gtv("TA06_AgBez")
        dll_instances[current_user.username].PNR_Buch4Clear(1, userid, '', '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
        return redirect(url_for(home, username=username))

    return render_template(
        "mengendialog.html",
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )


def endta51cancelt905(apersnr):
    """Terminates all running GK and FA for user with 'apersnr'."""

    xret = ''
    msgr = ''
    xfa = ''
    xgk = ''
    final_ret = ''

    xmsg = dll_instances[current_user.username].EndTA51GKCheck()
    logging.info('result EndTA51GKCheck: ' + xmsg)

    if len(xmsg) > 0:
        xret = "MSG0133" #Vorgang wurde abgebrochen
        if SHOWMSGGEHT[current_user.username] == 1:
            print('Info mit Eingabeaufforderung S903_ID=MSG0178 "GK müssen erst beendet werden!"')
            # TODO: show modal
            model_yes = True  # user pressed yes
            if model_yes:
                userid = dbconnection.getUserID(apersnr)
                ret = dbconnection.doGKBeenden(userid, FirmaNr[current_user.username])
                result = dll_instances[current_user.username].EndTA51GKSave()
                if ret==True:
                    final_ret = "GK"
                else:
                    flash("GK konnten nicht beendet werden!")
                    return "error"
            else:  # user pressed no, cancel booking
                flash("GK Buchung abgebrochen!")
                return "error"
            
            msgr='ok'
        else:
            # just terminate GK without asking
            print('Info OHNE Eingabeaufforderung S903_ID=MSG0178 "GK müssen erst beendet werden!"')
            userid = dbconnection.getUserID(apersnr)
            ret = dbconnection.doGKBeenden(userid, FirmaNr[current_user.username])
            result = dll_instances[current_user.username].EndTA51GKSave()
            if ret==True:
                final_ret = "GK"
            else:
                flash("GK konnten nicht beendet werden!")
                return "error"
            msgr='ok'

    if msgr == 'ok':
        if GKENDCHECK[current_user.username] == 1:
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
    result = dll_instances[current_user.username].EndTA51FACheck(xfa, xgk)
    xret, xfa, xgk = result

    if xret is None:
        xret = ''
    logging.info(f'[DLL] endta51cancelt905 xret: {xret}, xfa: {xfa}, xgk: {xgk}')

    # FA sind zu beenden
    if len(xfa) > 0:
        print('Info mit Eingabeaufforderung S903_ID=MSG0132 "Sollen alle laufenden Aufträge ohne Mengeneingabe beendet werden? ok/no"')
        result = dll_instances[current_user.username].EndTA51Save()
        final_ret = "FA"

    # GK sind zu beenden
    if len(xgk) > 0:
        result = dll_instances[current_user.username].EndTA51GKSave()
        final_ret = "GK"

    return final_ret


def bufa(ANr="", ATA29Nr="", AFARueckend="", ata22dauer="", aAnfangTS=None, aEndeTS=None, platz=None, aBem=None, userid=None, endroute="home", sa=""):
    """Checks whether current GK/FA active in DLL is ok to be booked and decides which fabuchta is appropriate."""
    xFehler = ''  
    xbBuchZiel = 1
    xScanFA = 0
    xfanr = ''
    xt905nr = ''
    xInputMenge = 0 # Flag, 1=Menge eingeben
    xInputMengeNew = 0
    xFARueckEnd = False
    xScanFA = 0
    xFAStatus = ''
    xFATS = ''
    xFAEndeTS = ''
    xFAMeGut = 0.0
    xFAMeGes = 0.0
    xFANewScanFA = 0
    xFANewStatus = ''
    xFANewMeGes = 0.0
    xFANewMe = 0.0
    
    #Prüfen, ob WB gemacht werden muß
    #nur dann, wenn Arbeitsplatz gelesen worden ist!
    if dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_T905) is True:
        print("[DLL] dr_T905 vorhanden")
        #Vor Buchung, prüfen, ob Kst der Person mit der Kst des zu buchenden Arbeitsplatz stimmt! Wenn nicht Wechsebuchung erzeugen!
        #Wechselbuchung triggert auf T955!!
        dll_instances[current_user.username].BuFAWB(ATA29Nr)

    # Auftrag finden
    if dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_TA06) is True:
        print('[DLL] bufa CO drta06 exist')
    else:
        # FANr wird gescannt und über T905ArbGRNr oder T909 und Platz Soll wird Beleg gefunden
        # Buchung auf FA_Nr
        if dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_TA05) is True:
            xt905nr = dll_instances[current_user.username].gtv("T905_Nr")
            xfanr = dll_instances[current_user.username].gtv("TA05_FA_Nr")
            result = dll_instances[current_user.username].TA06ReadArbGrNr(xfanr, xt905nr)
            print('[DLL] TA06Read' + result)
            if result == 1:
                xScanFA = 1
            else:
                xFehler = xfanr

    if len(xFehler) == 0:
        # Prüfen, ob FA bebucht werden darf
        print(dll_instances[current_user.username].gtv("dr_TA06"))
        result = dll_instances[current_user.username].BuFANr0Status(xbBuchZiel)
        xret, xbBuchZiel = result
        print('[DLL] Bufanrstatus ' + xret + ', Buchziel ' + str(xbBuchZiel))

        if len(xFehler) == 0:
            if xbBuchZiel == 1:

                result = dll_instances[current_user.username].BuchTA55_0(xInputMenge, xInputMengeNew, xFARueckEnd, xScanFA, xFAStatus, xFATS, xFAEndeTS,
                                          xFAMeGut, xFAMeGes, xFANewScanFA, xFANewStatus, xFANewMeGes, xFANewMe)
                xret, xInputMenge, xInputMengeNew, xScanFA, xFAStatus, xFATS, xFAEndeTS, xFAMeGut, xFAMeGes, xFANewScanFA, xFANewStatus, xFANewMeGes, xFANewMe = result
                print(f"[DLL] BuchTA55_0: {result}")
                if len(xret) > 0:
                    # cancel
                    flash("Buchung fehlgeschlagen!")
                    usernamepd = dbconnection.getPersonaldetails(userid)
                    username = usernamepd['formatted_name']
                    dll_instances[current_user.username].PNR_Buch4Clear(1, userid, sa, '', 1, GKENDCHECK, '', '', '', '', '')
                    return redirect(url_for("home", username=username))

                if xInputMenge == 1:
                    # show Mengendialog
                    print("[DLL] Mengendialog")
                    xScanFA = str(xScanFA)
                    return redirect(url_for("fabuchta55_dialog", userid=userid, menge_soll=xFAMeGes, xFAStatus=xFAStatus,
                                            xFATS=xFATS, xFAEndeTS=xFAEndeTS, xScanFA=xScanFA, endroute=endroute))
                else:
                    # don't show Mengendialog
                    print("[DLL] Kein Mengendialog")
                    xFehler = fabuchta55(userid, xFAMeGes, xFAStatus, xFATS, xFAEndeTS, xScanFA)
                    dll_instances[current_user.username].PNR_Buch4Clear(1, userid, '', '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
                    flash("Fertigungsauftrag gebucht.")
                    usernamepd = dbconnection.getPersonaldetails(userid)
                    username = usernamepd['formatted_name']
                    return redirect(url_for("home", username=username))
            
            if xbBuchZiel == 2:
                if platz is None:
                    xPlatz = ""
                else:
                    xPlatz = platz
                if dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_TA06) == True:
                    belegnr = dll_instances[current_user.username].gtv("TA06_BelegNr")
                print(f"[DLL] Belegnr: {belegnr}")
                # letzten Zählerstand holen und Platz wird aus Soll_Platz des FA geholt (jeder Zähler ist einem anderen Platz zugeordnet, Person bucht für andere)
                result = dll_instances[current_user.username].BuchTA56_0(xPlatz)
                xret, xPlatz = result
                if dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_TA56) == True:
                    old_total = dll_instances[current_user.username].gtv("TA56_Wert") #letzte Zählerstand
                return redirect(url_for("fabuchta56_dialog", userid=userid, old_total=old_total, belegnr=belegnr, platz=xPlatz))
            else:
                usernamepd = dbconnection.getPersonaldetails(userid)
                username = usernamepd['formatted_name']
                return fabuchta51(ata22dauer=ata22dauer, aAnfangTS=aAnfangTS, aEndeTS=aEndeTS, platz=platz, aBem=aBem, username=username)
    else:
        usernamepd = dbconnection.getPersonaldetails(userid)
        username = usernamepd['formatted_name']
        xFehler = ("Kein Auftrag!", ata22dauer)
        if dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_TA06) is True and dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_TA05) is False:
            dll_instances[current_user.username].PNR_Buch4Clear(1, userid, sa, '', 1, GKENDCHECK, '', '', '', '', '')
            xFehler = ("Keine Kopfdaten vorhanden!", ata22dauer)
            flash("Keine Kopfdaten vorhanden!")
            return redirect(url_for("home", username=username))
        dll_instances[current_user.username].PNR_Buch4Clear(1, userid, sa, '', 1, GKENDCHECK, '', '', '', '', '')
        flash("Keinen Auftrag gefunden!")
        return redirect(url_for("home", username=username))

    return xFehler


def start_booking(nr):
    """Starts the booking process for given card nr."""

    activefkt = ""
    buaction = 7
    bufunktion = 0
    # print('parameters',type(nr), type(activefkt), type(SCANTYPE), type(SHOWHOST), type(SCANON), type(KEYCODECOMPENDE))
    result = dll_instances[current_user.username].ShowNumber(nr, activefkt, SCANTYPE, SHOWHOST, SCANON, KEYCODECOMPENDE, False, "")
    ret, checkfa, sa = result
    print(f"[DLL] ShowNumber ret: {ret}, checkfa: {checkfa}, sa: {sa}")
    result = dll_instances[current_user.username].Pruef_PNr(checkfa, nr, sa, bufunktion)
    ret, sa, bufunktion = result
    print(f"[DLL] PruefPNr ret: {ret}, sa: {sa}, bufunktion: {bufunktion}")
        
    result = dll_instances[current_user.username].Pruef_PNrFkt(nr, bufunktion, SCANTYPE, sa, buaction, APPMSCREEN2, SERIAL, activefkt, "",
                                "", "")
    ret, sa, buaction, activefkt, msg, msgfkt, msgdlg = result
    print(f"[DLL] Pruef_PNrFkt ret: {ret}, sa: {sa}, buaction: {buaction}, activefkt: {activefkt}, msg: {msg}")

    return ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg


def fabuchta55(userid, xFAMeGes, xFAStatus, xFATS, xFAEndeTS, xScanFA):
    xFAMeGut=0.0
    xMengeAus=0.0
    xtrman=0.0
    xta11nr=''
    xcharge=''
    xVal1=0.0
    xVal2=0.0
    xVal3=0.0
    xVal4=0.0
    xVal5=0.0
    tl51use=False
		
    #Auftrag in DB schreiben
    #xClDetails noch zu lösen
    xPersNr = dll_instances[current_user.username].gtv("T910_Nr")
    xTE = dll_instances[current_user.username].gtv("TA06_TE")
    xScanFA = int(xScanFA)  # make sure dtype is correct
    print(f"[DLL] BuchTA55_3 input: {xFAStatus, xFATS, xFAEndeTS, dll_instances[current_user.username].T905_NrSelected, xPersNr, xFAMeGut, xMengeAus, xTE, xtrman, xta11nr, xcharge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA}")
    dll_instances[current_user.username].BuchTA55_3(xFAStatus, xFATS, xFAEndeTS, dll_instances[current_user.username].T905_NrSelected, xPersNr, xFAMeGut, xMengeAus, xTE, xtrman, xta11nr, xcharge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA)

    #Störung setzen
    #MDEGK_Ruest FA-Nr für Rüsten muß in Global Param definiert sein
    if tl51use == True:
        dll_instances[current_user.username].BuchTA55_3_TL(xFAEndeTS, dll_instances[current_user.username].T905_NrSelected)
    
    # Below does not happen for now
    # if xInputMengeNew == 1:
    # 	xMengeAus = 0
    # 	xFATS = Now
    # 	xFAEndeTS = xFATS
    # 	#HIER MENGENDIALOG
    # 	#xbuchen = kt001_InputMenge_Modus(Nothing, ActModus, dll_instances[current_user.username].dr_TA06BuchNew("TA06_RueckArt"),
    # 	#dll_instances[current_user.username].dr_TA06BuchNew("TA06_BelegNr"), dll_instances[current_user.username].dr_TA06BuchNew("TA06_AgBez"), T905_NrSelected, dll_instances[current_user.username].dr_TA06BuchNew("TA06_Soll_Me"), dll_instances[current_user.username].dr_TA06BuchNew("TA06_Ist_Me_gut"), dll_instances[current_user.username].dr_TA06BuchNew("TA06_Ist_Me_Aus") _
    # 	#, xFANewMe, xMengeAus, xtrman, xta11nr, xFANewStatus, xcharge, xVal1, xVal2, xVal3, xVal4, xVal5, xFARueckEnd, xClDetails)

    # 	if xbuchen == True:
    # 		#Auftrag in DB schreiben
    # 		dll_instances[current_user.username].dr_TA06Buch = dll_instances[current_user.username].dr_TA06BuchNew
    # 		#xClDetails, 
    # 		xTE = dll_instances[current_user.username].gtv("TA06_TE")
    # 		dll_instances[current_user.username].BuchTA55_3(xFANewStatus, xFATS, xFAEndeTS, T905_NrSelected, 0, xFANewMe, xMengeAus, xTE, xtrman, xta11nr, xcharge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA)
    
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

    xTA22Dauer = dll_instances[current_user.username].gtv("TA22_Dauer")  # aus TA06 gelesen
    if ata22dauer.isnumeric():
        xTA22Dauer = int(ata22dauer)  # if given, take assume this

    print(f"[DLL] PRE BuchTA51_0 xTA22Dauer: {xTA22Dauer}, xTS: {xTS}, xStatusMenge: {xStatusMenge}")
    result = dll_instances[current_user.username].BuchTA51_0(xTA22Dauer, xTS, xStatusMenge)
    xret, xTS, xStatusMenge = result
    xAnfangTS = datetime.strptime(xTS, DTFORMAT)
    print(f"[DLL] BuchTA51_0 xret: {xret}, xTS: {xTS}, xStatusMenge: {xStatusMenge}")
    if not aAnfangTS is None and not aEndeTS is None:  # when booking with given Dauer
        xStatusMenge = "20"  # TODO: bug in DLL, temporarily overwrite, 20 means just book, don't validate further

    print("xTS:" + xTS + " Datum:" + xAnfangTS.strftime(DTFORMAT))
    if len(xret) > 0:
        flash("Laufende Aufträge beendet.")
        dll_instances[current_user.username].PNR_Buch4Clear(1, nr, '', '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
        print(f"Buch4Clear: nr:{nr}, sa:{''}, buaction:{1}")
        return redirect(url_for(
            'home',
            username=username,
        ))
    
    # if xTA22Dauer == 3:
    #     if xDauer > 0:
    #         xAnfangTS = xEndeTS.AddMinutes(xDauer * -1)
    #         xAnfangTS = xAnfangTS.AddSeconds(-1) #1 sekunde wird wieder draufgerechnet!
    #     else:
    #         xbCancel = True
    #         xret = "MSG0133"
 
    if xbCancel is False:
        xta22typ = dll_instances[current_user.username].gtv("TA22_Typ")
        print("xta22typ:" + xta22typ)
        if dll_instances[current_user.username].gtv("TA22_Typ") == "7":
            xDialog=True
            if xDialog == True:
                xTSEnd = xEndeTS.strftime("%d.%m.%Y %H:%M:%S")
                xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S") 
                if platz == None:
                    platz = dll_instances[current_user.username].gtv("T905_Nr")
                dll_instances[current_user.username].BuchTA51_3( xTSEnd, dll_instances[current_user.username].gtv("T910_Nr"), dll_instances[current_user.username].gtv("TA06_FA_Nr"), dll_instances[current_user.username].gtv("TA06_BelegNr"), xStatusMenge, dll_instances[current_user.username].gtv("T910_Entlohnung")
                ,platz, dll_instances[current_user.username].gtv("TA06_TE"), dll_instances[current_user.username].gtv("TA06_TR"), 0, xMengeGut, xMengeAus, xTRMan, xTA11Nr, xCharge, xVal1, xVal2, xVal3, xVal4, xVal5, dll_instances[current_user.username].gtv("TA06_FA_Art"), xTS)
                
                #msg0166=Auftrag "_Msg1" wurde gebucht!
                xret = "FA Buchen;MSG0166" + ";" + dll_instances[current_user.username].gtv("TA06_BelegNr") + ";" + dll_instances[current_user.username].gtv("TA06_AgBez")
            else:
                # 'EvtMsgDisplay("FA Buchen", "MSG0133", "", "")
                #MSG0133=Vorgang wurde abgebrochen
                xret = "FA Buchen;MSG0133;;"
                         
            # dialogue is needed so reroute to route for Mengendialog
            return redirect(url_for("fabuchta51_dialog", userid=nr))
        else:
            # vorangegangenen Auftrag unterbrechen
            xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")
            t901_nr_print = dll_instances[current_user.username].gtv("T910_Nr")
            print(f"[DLL] PRE BuchTa51_4_Cancel xTS: {xTS}, T910_Nr: {t901_nr_print}")
            dll_instances[current_user.username].BuchTA51_4_Cancel(xTS, dll_instances[current_user.username].gtv("T910_Nr"))

            if dll_instances[current_user.username].gtv("TA22_Dauer") != 1:
                if aAnfangTS is None and aEndeTS is None:
                    # if not booking with Dauer, add a second for safety (?)
                    xAnfangTS = xAnfangTS + timedelta(seconds = 1) #xAnfangTS.AddSeconds(1)
                xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")
                
                xcl = Generic.Dictionary[String,Object]() #leere liste
                xdmegut = dll_instances[current_user.username].gtv("TA06_Soll_Me")
                xsmegut = str(xdmegut)
                xmegut = float(xsmegut.replace(",","."))
                if platz == None:
                    platz = dll_instances[current_user.username].gtv("T905_Nr")
                xret = dll_instances[current_user.username].BuchTA51_3(xTSEnd, int(dll_instances[current_user.username].gtv("T910_Nr")), dll_instances[current_user.username].gtv("TA06_FA_Nr"),
                                        dll_instances[current_user.username].gtv("TA06_BelegNr"), xStatusMenge, dll_instances[current_user.username].gtv("T910_Entlohnung"),
                                        platz, dll_instances[current_user.username].gtv("TA06_TE"), dll_instances[current_user.username].gtv("TA06_TR"), 0.0,
                                        xmegut, float(0.0), xTRMan, xTA11Nr, xCharge,
                                        xVal1, xVal2, xVal3, xVal4, xVal5, dll_instances[current_user.username].gtv("TA06_FA_Art"), xTS)

            xret = "FA Buchen;MSG0166" + ";" + dll_instances[current_user.username].dr_TA06.get_Item("TA06_BelegNr") + ";" + dll_instances[current_user.username].dr_TA06.get_Item(
                "TA06_AgBez")
    dll_instances[current_user.username].PNR_Buch4Clear(1, nr, '', '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
    print(f"Buch4Clear: nr:{nr}, sa:{''}, buaction:{1}")
    flash("Gemeinkosten erfolgreich gebucht.")
    return redirect(url_for("home", username=username))


def actbuchung(kst="", t905nr="", salast="", kstlast="", tslast="", APlatz="", nr="", username="", sa="", arbeitsplatz=None, ata22dauer="", AAnfangTS=None, AEndeTS=None, aBem=None, endroute="home"):
    """K/G/A booking according to sa for user with given card nr and username."""
    xT905Last = ""
    xTA29Last = ""
    xtagid=''
    xkstk=0
    xfaruecknr=''
    xmenge=0
    result = dll_instances[current_user.username].CheckKommt(sa, kst, salast, kstlast, tslast, xT905Last, xTA29Last)
    xret, ASALast, AKstLast, ATSLast, xT905Last, xTA29Last = result
    print(f"[DLL] CheckKommt ret: {xret}, ASALast: {ASALast}, AKstLast: {AKstLast}, ATSLast: {ATSLast}, xT905Last: {xT905Last}, xTA29Last: {xTA29Last}")

    if len(xret) > 0:  # Fehler
        if dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_TA06) is True or dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_TA05) is True:
            flash("Fehler: Keine Auftragsbuchung ohne Kommt!")
            dll_instances[current_user.username].PNR_Buch4Clear(1, nr, sa, '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
            return redirect(url_for("home", username=username))
        if (xret=="MSG0065" and sa=="A") or (xret=="MSG0065" and sa=="G"):  # MSG0065 is ok if current Buchung is K
            flash("Fehler: Keine \"Kommt\"-Buchung vorhanden!")
            dll_instances[current_user.username].PNR_Buch4Clear(1, nr, sa, '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
            return redirect(url_for("home", username=username))

    xpersnr = dll_instances[current_user.username].T910NrGet()
    xret = ""

    cancel_xret = endta51cancelt905(xpersnr)
    print(f"[DLL] endta51cancelt905: {cancel_xret}")
    if cancel_xret == 'GK':
        flash('Laufende GK-Aufträge wurden beendet!')
    elif cancel_xret == 'FA':
        flash('Laufende FA-Aufträge wurden beendet!')
    elif cancel_xret == 'error':
        # flash of error already called in endta51cancelt905
        return redirect(url_for("home", username=username))

    if dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_T905) is True:
        t905nr = dll_instances[current_user.username].gtv("T905_Nr")

    if dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_TA06) is True or dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_TA05) is True:
        print("[DLL] TA06 or TA05 True")
        if dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_TA06) is True:
            print("[DLL] TA06 True")
            if dll_instances[current_user.username].gtv("T951_Arbist") != dll_instances[current_user.username].gtv("TA06_Platz_Soll"):
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
                    xFehler = "MSG0137" #'Auftrag wurde nicht erfaßt!                    
                    print("[DLL] abweichender Platz, umbuchen nicht erlaubt")
                    flash("Abweichender Platz, Umbuchen nicht erlaubt!")
                    return redirect(url_for("home", username=username))

        if len(xret) == 0:
            if dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_T905) is False:
                if dll_instances[current_user.username].CheckObject(dll_instances[current_user.username].dr_T951) is True:
                    dll_instances[current_user.username].T905Read(dll_instances[current_user.username].gtv("T951_Arbist"))

            dll_instances[current_user.username].T905_NrSelected = dll_instances[current_user.username].gtv("T905_Nr")
            return bufa(ANr=dll_instances[current_user.username].gtv("TA06_BelegNr"), ata22dauer=ata22dauer, aAnfangTS=AAnfangTS, aEndeTS=AEndeTS, platz=arbeitsplatz, aBem=aBem, userid=nr, endroute=endroute)

    if len(xret) == 0:
        if len(xret) == 0:
            if sa == "K":
                return redirect(url_for(
                    'anmelden',
                    userid=nr,
                    sa=sa
                ))               
            elif sa == "G":
                result = dll_instances[current_user.username].PNR_Buch(sa, kst, t905nr, '', '', '', 0)
                xret, ASA, AKst, APlatz, xtagid, xkstk = result
                if GKENDCHECK[current_user.username] is True:  # Param aus X998 prüfen laufende Aufträge
                    xret = dll_instances[current_user.username].PNR_Buch2Geht()
                logging.info("Already Logged In")
                flash("User wurde abgemeldet.")
            elif sa == 'A':
                result = dll_instances[current_user.username].PNR_Buch(sa, kst, t905nr, '', '', '', 0)
                xret, ASA, AKst, APlatz, xtagid, xkstk = result
                flash(arbeitsplatz)
                logging.debug(f"[DLL] booked Arbeitsplatz: {arbeitsplatz}")

            if len(xret) == 0:
                dll_instances[current_user.username].PNR_Buch3(xtagid, sa, AKst, APlatz, '', '', 0)
                print(f"[DLL] PNR_Buch3")
            dll_instances[current_user.username].PNR_Buch4Clear(1, nr, sa, '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')

        return redirect(url_for("home", username=username))


def ta06gkend(userid,AScreen2=None):
	
	xMsg = dll_instances[current_user.username].EndTA51GKCheck()
	if len(xMsg) == 0:
		flash("Keine GK zu Beenden!") # Es gibt keine Gemeinkostenaufträge zu beenden!  || nothing to terminate
	else:
		ret = dbconnection.doGKBeenden(userid, FirmaNr[current_user.username])
		if ret==True:
			flash("Laufende Aufträge beendet.")
		else:
			flash("GK konnten nicht beendet werden!")


def gk_ändern(fa_old, userid, anfang_ts, dauer, date):
	# Change existing Auftragsbuchung, TODO: somehow return error when no GK to delete is found
	ret = dbconnection.doGKLoeschen(fa_old, userid, anfang_ts, FirmaNr[current_user.username])  # delete old booking with BelegNr=scanvalue and Anfang=Anfangts
	persnr = dbconnection.getPersonaldetails(userid)["T910_Nr"]
	if dauer > 0:
		# add back booking with correct dauer
		anfang_ts, ende_ts = dbconnection.doFindTS(persnr, dauer, date, FirmaNr[current_user.username])  # find suitable begin and end for new Auftrag
		if anfang_ts is None and ende_ts is None:
			ret = dbconnection.doUndoDelete(fa_old, userid, FirmaNr[current_user.username])
			if not ret is None:
				return "Keine neue Zeitperiode gefunden und Auftrag konnte nicht wiederhergestellt werden!"
			return "Keine neue Zeitperiode gefunden!"
		return anfang_ts, ende_ts
	else:
		# dauer == 0 meaning no new booking, just delete old
		# result = dll_instances[current_user.username].PNR_Buch4Clear(1, scanvalue, sa, platz, buaction, gkendcheck, activefkt, msgfkt, msgbuch, msgzeit, msgpers)
		return "Nur gelöscht"


def gk_erstellen(userid, dauer, date):
	# create Auftragsbuchung with Dauer
	persnr = dbconnection.getPersonaldetails(userid)["T910_Nr"]
	anfang_ts, ende_ts = dbconnection.doFindTS(persnr, dauer, date, FirmaNr[current_user.username])
	if anfang_ts is None and ende_ts is None:
		return "Keine neue Zeitperiode gefunden!"
	else:
		return anfang_ts, ende_ts


def get_list(listname, userid=None):
    """Getter function for various lists needed for display in the app."""

    if listname == "arbeitsplatzgruppe":
        # Implement database calls here.
        return ["Frontendlager", "Verschiedenes (Bünde)", "Lehrwerkstatt", "AV (Bünde)"]

    if listname == "arbeitsplatz":
        arbeitsplatz_info = dbconnection.getArbeitplazlist(FirmaNr[current_user.username], X998_GrpPlatz[current_user.username])
        return [arbeitsplatz_info['T905_bez'], arbeitsplatz_info['T905_Nr']]

    if listname == "arbeitsplatzbuchung":
        persnr, arbeitsplatz, fanr = dbconnection.getArbeitplatzBuchung(FirmaNr[current_user.username], X998_GrpPlatz[current_user.username])
        return [persnr, arbeitsplatz, fanr]
    
    if listname == "gruppenbuchung_faNr":
        fanr = dbconnection.getGruppenbuchungFaNr(FirmaNr[current_user.username])
        return fanr

    if listname == "gruppe":
        gruppe = dbconnection.getGruppenbuchungGruppe(FirmaNr[current_user.username])
        return gruppe

    if listname == "fertigungsauftrag_frNr":
        return [1067, 2098, 7654, 2376, 8976]

    if listname == "gemeinkostenandern_frNr":
        return [1067, 2098, 7654, 2376, 8976]

    if listname == "statusTableItems":
        upper_items_df, lower_items_df = dbconnection.getStatustableitems(userid, FirmaNr[current_user.username])
        # create html tags out of the above data frames
        upper_items_html = upper_items_df.to_html(classes="table table-striped", index=False, justify="left").replace('border="1"','border="0"')
        lower_items_html = lower_items_df.to_html(classes="table table-striped", index=False, justify="left").replace('border="1"','border="0"')
        return [upper_items_html, lower_items_html]

    if listname == "homeButtons":
        return [["Wechselbuchung", "Gemeinkosten", "Status", "Gemeinkosten Beenden",
                 "Arbeitsplatzbuchung", "Gruppenbuchung", "Gemeinkosten ändern", "FA erfassen", "Zählerstandsrückmeldung"],
                ["arbeitsplatzwechsel", "gemeinkosten_buttons", "status", "gemeinkostenbeenden",
                 "arbeitsplatzbuchung", "gruppenbuchung", "gemeinkostenandern", "fertigungsauftragerfassen", "zaehlerstand_buttons"]]

    if listname == "gemeinkostenItems":
        gk_info = dbconnection.getGemeinkosten(userid, FirmaNr[current_user.username])
        return [gk_info["TA05_ArtikelBez"], gk_info["TA06_BelegNr"]]
    
    if listname == "zaehlerItems":
        zaehler_info = dbconnection.getZaehler(userid, FirmaNr[current_user.username])
        return [zaehler_info["TA05_ArtikelBez"], zaehler_info["TA06_BelegNr"]]

    if listname == "sidebarItems":
        return [["Wechselbuchung", "Gemeinkosten", "Status", "Gemeinkosten Beenden",
                 "Arbeitsplatzbuchung", "Gruppenbuchung", "Gemeinkosten ändern", "FA erfassen", "Zählerstandsrückmeldung"],
                ["arbeitsplatzwechsel", "gemeinkosten_buttons", "status", "gemeinkostenbeenden",
                 "arbeitsplatzbuchung", "gruppenbuchung", "gemeinkostenandern", "fertigungsauftragerfassen", "zaehlerstand_buttons"]]

# if __name__ == '__main__':
    
    # app.run(debug=True)