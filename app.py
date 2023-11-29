import os
import sys
import xml.etree.ElementTree as ET
import getpass
import socket

from flask import Flask, session, send_from_directory
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import PickleType
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length
from flask_wtf import FlaskForm
from flask import json
from werkzeug.exceptions import HTTPException

from datetime import datetime, timedelta
from dateutil import parser
import time
import shutil

import dbconnection
from dll_api import *
import logging
logging.basicConfig(level=logging.INFO)

from flask_babel import Babel, format_datetime, gettext

import clr
import System
import pandas as pd
from ctypes import *
import numpy as np
import pandas as pd

# CONSTANTS
verwaltungsterminal = True   # variable to show Gruppen field in the UI or not
root  = {}
DTFORMAT = "%d.%m.%Y %H:%M:%S"
DFORMAT = "%d.%m.%Y"
ROOT_DIR = os.path.abspath(os.path.dirname(__file__)) + "\\"  # directory which directly contains app.py
# PYTHON_PATH = os.path.abspath(os.path.dirname(sys.executable) + "\\python")
PYTHON_PATH = "C:/Users/MSSQL/PycharmProjects/DLLTest/venv/Scripts/python"
# PYTHON_PATH = "C:\\Python\\Python310\\python"
APPMSCREEN2 = True  # bool(int(root.findall('X998_StartScreen2')[0].text)) # X998_STARTSCREEN2
SHOWMSGGEHT = {} # X998_ShowMsgGeht
GKENDCHECK = {} # X998_GKEndCheck
BTAETIGKEIT = {} # X998_TAETIGKEIT
FirmaNr = {}
X998_GrpPlatz = {}
DLL_PATHS = {}
SCANTYPE = True  # root.findall('X998_SCANNER')[0].text # X998_SCANNER TS,CS,TP
SCANON = True  # Scansimulation an
KEYCODECOMPENDE = ""  # Endzeichen Scanwert
SHOWHOST = False  # Anzeige Hostinformation im Terminal
SERIAL = True
SCANCARDNO = True
T905ALLOWROUTE = True
ROUTEDIALOG = True
SHOW_BUTTON_IDS = False  # If true, show Arbeitsplatz and GK IDs after their name for debugging
SOCKETHOST = "localhost"  # host for DLL communication sockets
SOCKET_TIMEOUT = 5  # secs
SOCKET_INTERVAL = 0.01  # secs, connect interval
DB_TIMEOUT = 5  # secs
DB_RETRIES = 3

dcX998User = dict() #liste benutzerabhängiger Config key =User Liste=X998-dict
dcX998UserFkt =dict() #Liste der Funktionsknöppedef. key = User  Liste = Fktconfig
#dcX998Fkt =dict() #Liste der Funktionsknöppe für 1 Terminal


sys.path.append("dll/bin")
clr.AddReference("System.Collections")
os.chdir("dll/bin")

from System.Collections import Generic
from System.Collections import Hashtable
from System import String
from System import Object
from System import Type
import functools
import sqlalchemy.exc
import time

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

def retry_db_calls(max_retries, timeout):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0

            while retries < max_retries:
                try:
                    if retries > 0:
                        # try reconnecting to db
                        write_log("Trying to reconnect to database")
                        dbconnection.reconnect()
                        print("Reconnected")
                        try:
                            # terminate running dll subprocess to start new one
                            communicate(dll_instances[current_user.username], "shutdown")
                            dll_instances[current_user.username].shutdown(1)
                            dll_instances[current_user.username].close()
                            del dll_instances[current_user.username]
                            time.sleep(0.1)  # give subprocess time to shut down
                        except ConnectionAbortedError:
                            write_log("Could not shut down socket, already shut down?")
                            del dll_instances[current_user.username]  # still delete reference and make new one
                            
                    result = func(*args, **kwargs)
                    # print(f"result: {result}")
                    return result
                
                except (sqlalchemy.exc.SQLAlchemyError, ConnectionError) as e:
                    # Handle other SQLAlchemy-related errors
                    write_log(f"SQLAlchemyError: {str(e)}")
                    write_log(f"Retrying database call (attempt {retries + 1}/{max_retries})...")
                    retries += 1
                    time.sleep(timeout)
                    flash_message = "Es konnte keine Verbindung zur Datenbank aufgebaut werden!"
                    
            # If all retries fail, raise the exception to the top-level exception handling
            # raise Exception("Database call failed after multiple retries")
            flash(flash_message)
            return redirect(url_for('home'))
        
        return wrapper

    return decorator

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
subprocess_ports = {}

# Function to create a copy of the DLL for a given user
def create_dll_copy(username):
    src_path_data = ROOT_DIR+"dll\\data\\X998.xml"
    dest_path_data = ROOT_DIR+f"dll\\data\\X998-{username}.xml"
    # 27.10.2023 DG Prüfen, ob vorhanden und ob Datei neuer ist
    # bei copy wird das Änderungsdateum auf den Erstellungszeitpunkt gesetzt und nicht der Originaldatei beibehalten!
    # Prüfen löschen dll bei delete_user - wird nicht gelöscht, da vorher auf Fehler läuft; ist gut so, das nicht gelöscht - wann werden die dlls dann mal bereinigt?
    #10.11.2023 xtsrc = os.path.getmtime(src_path_data)
    #10.11.2023 xtdst = os.path.getmtime(dest_path_data)
    # print(f"copy from {src_path_data} to {dest_path_data}") - von dll erstell wird nicht mehr kopiert
    # shutil.copyfile(src_path_data, dest_path_data)
    
   

    src_path = ROOT_DIR+"dll\\bin\\kt002_PersNr.dll"
    dest_path = ROOT_DIR+f"dll\\bin\\kt002_PersNr-{username}.dll"
    xtsrc = os.path.getmtime(src_path)
    if os.path.exists(dest_path) == False:
        shutil.copyfile(src_path, dest_path)
        print(f"copy from {src_path} to {dest_path}")
    else:
        xtsrc = os.path.getmtime(src_path)
        xtdst = os.path.getmtime(dest_path)
        if xtdst < xtsrc:
            shutil.copyfile(src_path, dest_path)
            print(f"copy from {src_path} to {dest_path}")
    os.utime (dest_path,(xtsrc,xtsrc))
    return dest_path_data, dest_path

# Function to delete the DLL copy for a given user
def delete_dll_copy(user):
    if os.path.exists(user.dll_path):
        os.remove(user.dll_path)
    else:
        write_log(user.dll_path + " DLL-Datei wurde nicht gelöscht")
    if os.path.exists(user.dll_path_data):
        os.remove(user.dll_path_data)
    else:
        write_log(user.dll_path_data + " DLL-Datei wurde nicht gelöscht")



#einlesen der Konfig
def Readx998Config(ausername):
    xsrc =  ROOT_DIR+f"dll\\data\\X998-{ausername}.xml"
    try:
        xdcX998 = dcX998User[ausername]
    except:
        xdcX998=dict()
    
    if os.path.exists(xsrc) == True:
        xtree = ET.parse(xsrc)
        xcfg = xtree.find("X998_ConfigTerm") #den 1. finden   
        for element in xcfg:
            xdcX998[element.tag] = element.text
        dcX998User[ausername]=xdcX998

        
        xlcX998Fkt =[]

        result = GetFkt(xdcX998["X998_F1Btn1"])
        xret,xdcFkt = result
        if xret == True:
            xlcX998Fkt.append(xdcFkt)
        result = GetFkt(xdcX998["X998_F1Btn2"])
        xret,xdcFkt = result
        if xret == True:
            xlcX998Fkt.append(xdcFkt)
        result = GetFkt(xdcX998["X998_F1Btn3"])
        xret,xdcFkt = result
        if xret == True:
            xlcX998Fkt.append(xdcFkt)
        result = GetFkt(xdcX998["X998_F1Btn4"])
        xret,xdcFkt = result
        if xret == True:
            xlcX998Fkt.append(xdcFkt)
        result = GetFkt(xdcX998["X998_F1Btn5"])
        xret,xdcFkt = result
        if xret == True:
            xlcX998Fkt.append(xdcFkt)
        result = GetFkt(xdcX998["X998_F1Btn6"])
        xret,xdcFkt = result
        if xret == True:
            xlcX998Fkt.append(xdcFkt)
        result = GetFkt(xdcX998["X998_F1Btn7"])
        xret,xdcFkt = result
        if xret == True:
            xlcX998Fkt.append(xdcFkt)
        result = GetFkt(xdcX998["X998_F1Btn8"])
        xret,xdcFkt = result
        if xret == True:
            xlcX998Fkt.append(xdcFkt)
        result = GetFkt(xdcX998["X998_F1Btn9"])
        xret,xdcFkt = result
        if xret == True:
            xlcX998Fkt.append(xdcFkt)
        result = GetFkt(xdcX998["X998_F1Btn10"])
        xret,xdcFkt = result
        if xret == True:
            xlcX998Fkt.append(xdcFkt)
        result = GetFkt(xdcX998["X998_F1Btn11"])
        xret,xdcFkt = result
        if xret == True:
            xlcX998Fkt.append(xdcFkt)
        result = GetFkt(xdcX998["X998_F1Btn12"])
        xret,xdcFkt = result
        if xret == True:
            xlcX998Fkt.append(xdcFkt)

        dcX998UserFkt[ausername]=xlcX998Fkt
        xlcX998Fkt =None



def GetFkt(afkt):
    xret = False
    xFkt = dbconnection.getX998Fkt(afkt)
    xdcFkt = dict() #erstellen und nicht benutzen - wann wird bereinigt?
    if len(xFkt)> 0:
        xtree = ET.fromstring(xFkt)
        xcfg = xtree.find("root") #den 1. finden   
        for element in xtree:
            xdcFkt[element.tag] = element.text
        xret = True
        xs = xdcFkt["Text"]
        xt = dbconnection.getS903("DEU","FORM",xs,"")
        xdcFkt["Text"] = xt
    return xret,xdcFkt
        


        
# Function to register user
def register_user(username, password, verbose=False):
    if db.session.query(User).filter_by(username=username).count() < 1:
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        dll_path_data, dll_path = create_dll_copy(new_user.username)
        new_user.dll_path = dll_path
        new_user.dll_path_data = dll_path_data
        db.session.commit()
        if verbose:
            flash('Sie haben sich erfolgreich registriert!')
        return True
    else:
        if verbose:
            flash('Benutzer existiert bereits!')
        return False
        
# Function to create and login user with hostname
def create_and_login(request, hostname):
    if not hostname:
        hostname = socket.gethostbyaddr(request.environ["REMOTE_ADDR"])[0]
        hostname = hostname.split(".")[0]
        #hostname = "pks866"  # dummy value for testing
    user = User(username=hostname, password=hostname)
    newly_registred = register_user(hostname, hostname)
    user = User.query.filter_by(username=hostname).first()
    login_user(user)
    
    return hostname, user, newly_registred

def prepare_subprocess(hostname, user, newly_registred):
    dll_path = ROOT_DIR+f"dll\\bin\\kt002_PersNr-{hostname}.dll"
    if not user.username in subprocess_ports:
        subprocess_ports[user.username] = get_free_port()
        start_subprocess = True
        
        if not newly_registred:
            dll_path_data, dll_path = create_dll_copy(hostname)
            user.dll_path = dll_path
            user.dll_path_data = dll_path_data
            db.session.commit()
    else:
        start_subprocess = False
    
    return dll_path, start_subprocess

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
                clr.AddReference(dll_path)
                dll_ref = System.Reflection.Assembly.LoadFile(dll_path)
                type = dll_ref.GetType('kt002_persnr.kt002')
                instance = System.Activator.CreateInstance(type)
                dll_instances[user.username] = instance
                # instance.Init(user.username)
                instance.Init()
                instance.InitTermConfig()
                # time.sleep(1)
                root[user.username] = ET.parse(f"../../dll/data/X998-{user.username}.xml").getroot()[0]  # parse X998.xml file for config
                SHOWMSGGEHT[user.username]  = bool(int(root[user.username].findall('X998_ShowMsgGeht')[0].text))  # X998_ShowMsgGeht
                GKENDCHECK[user.username]  = bool(int(root[user.username].findall('X998_GKEndCheck')[0].text))  # X998_GKEndCheck
                BTAETIGKEIT[user.username]  = bool(int(root[user.username].findall('X998_Taetigkeit')[0].text))  # X998_TAETIGKEIT
                FirmaNr[user.username]  = root[user.username].findall('X998_FirmaNr')[0].text  # X998_GKEndCheck
                X998_GrpPlatz[user.username]  = root[user.username].findall('X998_GrpPlatz')[0].text  # X998_TAETIGKEIT
                return True

        return False

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    flash(f"Fehler {str(e.code)}. Bitte versuchen Sie es erneut!")
    
    # restart subprocess server
    del subprocess_ports[current_user.username]  # delete port to trigger restarting of subprocess server
    hostname, user, newly_registred = create_and_login(request, current_user.username)
    
    start_time = time.time()
    while time.time() - start_time < SOCKET_TIMEOUT:
        try:
            dll_path, start_subprocess = prepare_subprocess(hostname, user, newly_registred)
            break  # if above successfull, break
        except PermissionError as e:
            if current_user.username in subprocess_ports:
                del subprocess_ports[current_user.username]  # delete port to trigger restarting of subprocess server
            time.sleep(SOCKET_INTERVAL)  # wait short interval before next try to not waste compute resources
    else:
        raise PermissionError(f"Unable to access DLL for {hostname}.")
    try:
        process = start_dll_process(PYTHON_PATH, dll_path, hostname, SOCKETHOST,
                                    subprocess_ports[user.username], start_subprocess)
    except TimeoutError:
        write_log("DLL Subprozess konnte nicht gestartet werden!")
        return redirect(url_for("home"))
    dll_instances[user.username] = process
    
    return redirect(url_for('home'))

@app.route('/index')
def index():
    return render_template('index.html', buttonValues=get_list("homeButtons"), sidebarItems=get_list("sidebarItems"))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        register_user(form.username.data, form.password.data, verbose=True)
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
        flash('Ungültiger Benutzername oder Passwort!')
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
        flash('Benutzer nicht gefunden!')
        return redirect(url_for('dashboard'))

def delete_user(user):
    try:
        db.session.delete(user)
        db.session.commit()
        delete_dll_copy(user)
        return True
    except:
        return False

@app.route('/delete_user/<int:user_id>')
@login_required
def delete_user_route(user_id):
    user = User.query.get(user_id)
    if user:
        if delete_user(user):
            flash('Benutzer erfolgreich gelöscht.')
        else:
            flash('Benutzer konnte nicht gelöscht werden!')
    else:
        flash('Benutzer nicht gefunden!')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    # Delete the dll_instance for the logged out user
    del dll_instances[current_user.username]
    logout_user()
    return redirect(url_for('index'))

def write_log(msg):
    date_formatted = datetime.now().strftime("%Y_%m_%d")
    datetime_formatted = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]
    # print(f"{datetime_formatted} {username} -- {msg}")
    print(f"{datetime_formatted} -- {msg}")
    # fpath = ROOT_DIR+f"dll\\log\\{username}\\l_{date_formatted}\\AppLog_{date_formatted}.txt"
    fpath = ROOT_DIR+f"dll\\log\\l_{date_formatted}\\AppLog_{date_formatted}.txt"
    os.makedirs(os.path.dirname(fpath), exist_ok=True)  # create dir if it does not exist
    with open(fpath, "a+") as fout:
        # fout.write(f"\n{datetime_formatted} {username} -- {msg}")
        fout.write(f"\n{datetime_formatted} -- {msg}")
        
def get_free_port():
    """Opens new socket and returns open port assigned by OS."""
    sock = socket.socket()
    sock.bind(('', 0))
    free_port = sock.getsockname()[1]
    sock.close()
    return free_port

# @babel.localeselector
# def get_locale():
#     return 'de'

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/images'),
                               'pks_icon_small.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/", methods=["POST", "GET"])
@app.route("/<hostname>", methods=["POST", "GET"])
@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
def home(hostname=None):
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

    # inst_current_user = dll_instances[current_user.username]
    if request.method == 'POST':
        if current_user.is_authenticated:
            user = current_user
            logout_user()  # log out user, will get logged in again when beginning booking
            delete_user(user)  # also delete user, will newly register when booking to get resh XML copy
        
        hostname, user, newly_registred = create_and_login(request, hostname)
        dll_path, start_subprocess = prepare_subprocess(hostname, user, newly_registred)
        
        try:
            process = start_dll_process(PYTHON_PATH, dll_path, hostname, SOCKETHOST,
                                        subprocess_ports[user.username], start_subprocess)
        except TimeoutError:
            write_log("DLL Subprozess konnte nicht gestartet werden.")
            return redirect(url_for("home", username=username))
        dll_instances[user.username] = process
        
        root[user.username] = ET.parse(f"../../dll/data/X998-{user.username}.xml").getroot()[0]  # parse X998.xml file for config
        SHOWMSGGEHT[user.username]  = bool(int(root[user.username].findall('X998_ShowMsgGeht')[0].text))  # X998_ShowMsgGeht
        GKENDCHECK[user.username]  = bool(int(root[user.username].findall('X998_GKEndCheck')[0].text))  # X998_GKEndCheck
        BTAETIGKEIT[user.username]  = bool(int(root[user.username].findall('X998_Taetigkeit')[0].text))  # X998_TAETIGKEIT
        FirmaNr[user.username]  = root[user.username].findall('X998_FirmaNr')[0].text  # X998_GKEndCheck
        X998_GrpPlatz[user.username]  = root[user.username].findall('X998_GrpPlatz')[0].text  # X998_TAETIGKEIT

        inputBarValue = request.form["inputbar"]
        username = None #21.11.2023 DG 
        if "selectedButton" in request.form:
            selectedButton = request.form["selectedButton"]

            if selectedButton == "arbeitsplatzwechsel" and len(inputBarValue) > 0:
                return redirect(url_for("arbeitsplatzwechsel", userid=inputBarValue))
            else:
                return redirect(url_for("identification", page=selectedButton))

        elif "anmelden_submit" in request.form:
            try:
                nr = inputBarValue #21.11.2023 DG
                usernamepd = dbconnection.getPersonaldetails(inputBarValue)
                username = usernamepd['formatted_name']
            except IndexError as e:
                if username is None:
                    # handle the case where username is not valid
                    flash("Kartennummer ungültig!")
                    write_log(f"invalid card number: {nr}")
                    return redirect(url_for("home", username=""))
            # something was put into the inputbar and enter was pressed
            nr = inputBarValue
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(nr)
            if not ret:
                # something went wrong or Auftragsbuchung
                if msg == "MSG0147C":  # Kartennummer scannen
                    communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, nr, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
                    write_log(f"Buch4Clear: nr:{nr}, sa:{sa}, buaction:{buaction}")
                    return redirect(url_for("identification", page="_auftragsbuchung"))
                elif msg == "MSG0085":
                    flash("Keine Berechtigung zur Buchung!")
                #22.11.2023 DG
                elif msg == "MSG0067C":
                    flash("Keine gültige Kartennummer!")
                elif msg == "MSG0162":
                    flash("Kartennummer ist inaktiv!")
                else:
                    flash("Unerwarter Fehler!")
                communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, nr, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
                return redirect(url_for("home", username=username))
            else:
                #22.11.2023 DG
                if username is None:
                    # handle the case where username is not valid
                    flash("Kartennummer ungültig!")
                    write_log(f"invalid card number: {nr}")
                    return redirect(url_for("home", username=""))
                else:
                    # K/G Buchung
                    return actbuchung(nr=nr, username=username, sa=sa)

    elif request.method == "GET":
                
        if not "first_request" in session:  # on first GET request of each session
            session["first_request"] = True
            # start dll in subprocess once on first connection
            hostname, user, newly_registred = create_and_login(request, hostname)
            dll_path, start_subprocess = prepare_subprocess(hostname, user, newly_registred)
            try:
                process = start_dll_process(PYTHON_PATH, dll_path, hostname, SOCKETHOST,
                                            subprocess_ports[user.username], start_subprocess)
            except TimeoutError:
                write_log("DLL Subprozess konnte nicht gestartet werden.")
                return redirect(url_for("home", username=username))
            dll_instances[user.username] = process
        
        if current_user.is_authenticated:
                if current_user.username in dll_instances:
                    try:
                        # terminate running dll subprocess when returning to home
                        communicate(dll_instances[current_user.username], "shutdown")
                        dll_instances[current_user.username].shutdown(1)
                        dll_instances[current_user.username].close()
                        del dll_instances[current_user.username]
                        time.sleep(0.1)  # give subprocess time to shut down
                    except ConnectionAbortedError:
                        write_log("Could not shut down socket, already shut down?")
                        del dll_instances[current_user.username]  # still delete reference and make new one
        
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
@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
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

    usernamepd = dbconnection.getPersonaldetails(userid)
    username = usernamepd['formatted_name']

    if request.method == 'POST':
        selectedArbeitsplatz = request.form["arbeitplatzbuttons"]
        # Retrieve the value of selected button
        selectedArbeitsplatz, arbeitsplatzName = selectedArbeitsplatz.split(",")
        nr = userid
        write_log(f"Arbeitsplatzwechsel: nr:{nr}, selectedArbeitsplatz:{selectedArbeitsplatz}, arbeitsplatzName:{arbeitsplatzName}")
        communicate(dll_instances[current_user.username], "T905Read", selectedArbeitsplatz)
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
@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
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
        write_log(f"Gememeinkosten: selected_gk:{selectedGemeinkosten}, gk_name:{gk_name}")

        ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(selected_gk)  # start with GK nr
        communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, selected_gk, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
        write_log(f"Buch4Clear: nr:{selected_gk}, sa:{sa}, buaction:{buaction}")

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
@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
@login_required
def zaehlerstand_buttons(userid):
    """
    Route for choosing Zähler as Buttons.
    Uses 'gemeinkostenbuttons.html'.

    Args:
        userid: Kartennummer that was input into the inputbar on the identification screen.

    Routes to:
        fabuchta56_dialog: shows dialogue to input new Zählerstand.
        home: if any error occured.
    """

    usernamepd = dbconnection.getPersonaldetails(userid)
    username = usernamepd['formatted_name']

    if request.method == 'POST':
        # Retrieve the value of selected button from frontend
        selected_zs = request.form["gemeinkostenbuttons"]
        selected_zs, zs_name = selected_zs.split(",")
        write_log(f"Zählerstand: selected_zs:{selected_zs}, zs_name:{zs_name}")

        ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(selected_zs)  # start with GK nr
        communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, selected_zs, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
        write_log(f"Buch4Clear: nr:{selected_zs}, sa:{sa}, buaction:{buaction}")

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
@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
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
        # dauer = request.form.get('dauer') 
        dauer = int(request.form["dauer"])
        userid = dbconnection.getUserID(persnr)
        Belegnr = dbconnection.getBelegNr(FA_Nr, Platz, FirmaNr[current_user.username])
        if Belegnr == "error":
            flash("GK Auftrag für diesen Platz nicht definiert!")
            return redirect(url_for("arbeitsplatzbuchung", userid=userid))
        ret = communicate(dll_instances[current_user.username], "TA06Read", Belegnr)  # prese the BelegNr in the DLL
        if ret == False:
            communicate(dll_instances[current_user.username], "TA06ReadPlatz", Belegnr, Platz) 
        write_log(f"gk_erstellen: userid:{userid}, dauer:{dauer}, date:{TagId}")
        ret = gk_erstellen(userid, dauer, TagId)  # find time window
        if isinstance(ret, str):
            flash(ret)
            return redirect(url_for("arbeitsplatzbuchung", userid=userid))
        if not isinstance(ret, str):
            anfang_ts, ende_ts = ret
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(Belegnr) 
            communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, Belegnr, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(str(userid))
            return actbuchung(nr=userid, username=username, sa=sa, AAnfangTS=anfang_ts, AEndeTS=ende_ts)
        return redirect(url_for("home", userid=userid, username=username))
    dauer=np.linspace(0, 600, num=601).tolist()
    return render_template(
        "arbeitsplatzbuchung.html",
        arbeitplatz_dfs=get_list("arbeitsplatzbuchung",userid),
        date=datetime.now().date(),
        dauer=[int(i) for i in dauer],
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/gemeinkosten/", methods=["POST", "GET"])
@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
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
        try:
            userid = request.form["inputfield"]
            usernamepd = dbconnection.getPersonaldetails(userid)
            username = usernamepd['formatted_name']
        except IndexError as e:
            if username is None:
                # handle the case where username is not valid
                flash("Kartennummer ungültig!")
                write_log(f"invalid card number: {userid}")
                return redirect(url_for("home", username=""))

        ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(nr)
        return actbuchung(nr=nr, username=username, sa=sa)

    return render_template(
        "gemeinkosten.html",
        page="home",
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/identification/<page>", methods=["POST", "GET"])
@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
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
        try:
            userid = request.form["inputfield"]
            usernamepd = dbconnection.getPersonaldetails(userid)
            username = usernamepd['formatted_name']
        except IndexError as e:
            if username is None:
                # handle the case where username is not valid
                flash("Kartennummer ungültig!")
                write_log(f"invalid card number: {userid}")
                return redirect(url_for("home", username=""))

        if page == "_auftragsbuchung":
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(userid)
            return actbuchung(nr=userid, username=username, sa=sa, endroute="home")
        
        if page == "gemeinkostenbeenden":
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(userid)
            ta06gkend(userid=userid)
            communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, userid, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
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
@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
@login_required
def status(userid):
    return render_template(
        "status.html",
        tableItems=get_list("statusTableItems",userid),
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/berichtdrucken/<userid>", methods=["POST", "GET"])
@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
@login_required
def berichtdrucken(userid):
    return render_template(
        "berichtdrucken.html",
        arbeitsplatzgruppe=get_list("arbeitsplatzgruppe"),
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/gruppenbuchung/<userid>", methods=["POST", "GET"])
@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
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
        # dauer = request.form.get('dauer')
        dauer = int(request.form["dauer"])
        person_list = dbconnection.getGroupMembers(GruppeNr, TagId, FirmaNr[current_user.username])  # get all persons from this group
        person_nrs = [round(x) for x in person_list['T951_PersNr'].tolist()]
        
        for per_nr in person_nrs:
            userid = dbconnection.getUserID(per_nr)
            usernamepd = dbconnection.getPersonaldetails(userid)
            username = usernamepd['formatted_name']
            Platz = dbconnection.getLastbooking(userid).loc[0,'T951_ArbIst']
            Belegnr = dbconnection.getBelegNr(FA_Nr, Platz, FirmaNr[current_user.username])
            if Belegnr == "error":
                flash("GK Auftrag für diesen Platz nicht definiert!")
                continue
            ret = communicate(dll_instances[current_user.username], "TA06Read", Belegnr)  # preset the BelegNr in the DLL
            if ret == False: 
                communicate(dll_instances[current_user.username], "TA06ReadPlatz", Belegnr, Platz)
            write_log(f"gk_erstellen: userid:{userid}, dauer:{dauer}, date:{TagId}")
            ret = gk_erstellen(userid, dauer, TagId) # find time window
            if isinstance(ret, str):
                flash(ret)
            if not isinstance(ret, str):
                anfang_ts, ende_ts = ret
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(Belegnr)  # GK ändern booking, this is the new GK BelegNr
                communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, Belegnr, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(str(userid))
                actbuchung(nr=userid, username=username, sa=sa, AAnfangTS=anfang_ts, AEndeTS=ende_ts)
                time.sleep(0.25)  # make sure database has time to catch up
        return redirect(url_for("home", username=""))
    dauer=np.linspace(0, 600, num=601).tolist()
    return render_template(
        "gruppenbuchung.html",
        terminal = verwaltungsterminal,
        date=datetime.now().date(),
        frNr=get_list("gruppenbuchung_faNr"),
        gruppe=get_list("gruppe"),
        dauer=[int(i) for i in dauer],
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/fertigungsauftragerfassen/<userid>", methods=["POST", "GET"])
@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
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
        if request.form["submit"] == "erstellen": 
            datum = request.form["datum"]
            arbeitsplatz = request.form["arbeitsplatz"]
            beleg_nr = request.form["auftrag"]
            ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(beleg_nr)
            communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, beleg_nr, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
            if bufunktion == 3:
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(userid)
                return actbuchung(nr=userid, sa=sa, endroute="fertigungsauftragerfassen")
            else:
                flash("Buchung fehlgeschlagen!")
                communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, userid, sa, '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
                return redirect(url_for('home',username=username,))
    else:
        return render_template(
            "fertigungsauftrag.html",
            date=datetime.now().date(),
            auftraglst=auftraglst,
            auftraglst_ajax=auftraglst_ajax,
            anfangTS=datetime.today().strftime(DTFORMAT),
            username=usernamepd['formatted_name'],
            pers_no=usernamepd['T910_Nr'],
            tablecontent=tablecontent,
            sidebarItems=get_list("sidebarItems")
        )


@app.route("/gemeinkostenandern/<userid>", methods=["POST", "GET"])
@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
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
        dauer = int(request.form["dauer"])
        anfang_ts = request.form["anfangTS"]
        if datum == "":
            datum = anfang_ts
        date_string = parser.parse(datum)
        TagId = date_string.strftime("%Y-%m-%dT00:00:00")
        arbeitsplatz = request.form["arbeitsplatz"]
        for i in range(len(auftraglst)):
            for j in range(len(auftraglst[i])):
                if auftraglst[i][j][1] == arbeitsplatz:
                    pltz_id_bk = auftraglst[i][j][0]

        beleg_nr_old = request.form["old_beleg_nr"]
        beleg_nr = request.form["gemeinkosten"]
        kurztext = request.form["kurztext"]
        
        write_log(f"Gemeinkostenandern: datum:{datum}, dauer:{dauer}, anfangTS:{anfang_ts}, arbeitsplatz:{arbeitsplatz}, pltz_id_bk:{pltz_id_bk}, beleg_nr_old:{beleg_nr_old}, beleg_nr:{beleg_nr}, kurztext:{kurztext}")
        
        if request.form["submit"] == "ändern":  # change selected Auftrag
            ret = gk_ändern(fa_old=beleg_nr_old, userid=userid, anfang_ts=anfang_ts, dauer=dauer, date=TagId)
            if isinstance(ret, str):
                # display error string and cancel booking
                flash(ret)
                write_log(f"ERROR ret:{ret}")
                return redirect(url_for('home',username=username,))
            else:
                anfang_ts, ende_ts = ret
                write_log(f"anfang_ts: {anfang_ts}, ende_ts: {ende_ts}")
                
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(beleg_nr)
                communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, beleg_nr, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(userid)
                actbuchung(nr=userid, sa=sa, AAnfangTS=anfang_ts, AEndeTS=ende_ts, arbeitsplatz=pltz_id_bk, aBem=kurztext)
                return redirect(url_for("gemeinkostenandern", userid=userid))
        
        elif request.form["submit"] == "erstellen":  # create auftrag
            write_log(f"gk_erstellen: userid:{userid}, dauer:{dauer}, date:{TagId}")
            ret = gk_erstellen(userid=userid, dauer=dauer, date=TagId)
            if isinstance(ret, str):
                # display error string and cancel booking
                flash(ret)
                return redirect(url_for('home',username=username,))
            else:
                anfang_ts, ende_ts = ret
                write_log(f"anfang_ts: {anfang_ts}, ende_ts: {ende_ts}")
                
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(beleg_nr)
                communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, beleg_nr, sa, '', buaction, GKENDCHECK[current_user.username], '', '', '', '', '')
                ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg = start_booking(userid)
                actbuchung(nr=userid, sa=sa, AAnfangTS=anfang_ts, AEndeTS=ende_ts, arbeitsplatz=pltz_id_bk, aBem=kurztext) 
                return redirect(url_for("gemeinkostenandern", userid=userid))

    else:
        dauer=np.linspace(0, 600, num=601).tolist()

        return render_template(
            "gemeinkostenandern.html",
            date=datetime.now().date(),
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
@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
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
        write_log("%s at %s %s" % (username, selectedArbeitplatz, arbeitsplatzName))

        try:
            result = communicate(dll_instances[current_user.username], "PNR_Buch", sa, '', selectedArbeitplatz, '', '', '', 0)
            xret, ASA, AKst, APlatz, xtagid, xkstk = result
            if len(xret) == 0:
                write_log(f"PNR_Buch3: xtagid:{xtagid}, ASA:{ASA}. AKst:{AKst}, APlatz:{APlatz}")
                communicate(dll_instances[current_user.username], "PNR_Buch3", xtagid, ASA, AKst, APlatz, '', '', 0)
        except System.NullReferenceException:
            flash("Unerwarter Fehler!")
                
        write_log(f"PNR_Buch4Clear: userid:{userid}, sa:{sa}")
        result = communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, userid, sa, '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')

        return redirect(url_for('home', username=username))

    elif request.method == "GET":
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
@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
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
        
        if request.form["submit"] == "submit_cancel":
            write_log(f"fabuchta56_dialog: canceling")
            communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, userid, '', '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
            return redirect(url_for('home', username=username))

        dr_T910 = communicate(dll_instances[current_user.username], "get", "dr_T910")
        if dr_T910 is None:
            xPersNr = int(communicate(dll_instances[current_user.username], "gtv", "T910_Nr"))
        dr_TA06 = communicate(dll_instances[current_user.username], "get", "dr_TA06")
        if dr_TA06 is None:
            xTE = communicate(dll_instances[current_user.username], "gtv", "TA06_TE")
        
        try:
            new_total = int(request.form["new_total"])
        except ValueError:
            flash(f"Der Zählerstand muss als ganze Zahl angegeben werden!")
            return redirect(url_for('fabuchta56_dialog', userid=userid, old_total=old_total, platz=platz, belegnr=belegnr))
        
        if int(old_total) > new_total:
            flash(f"Neuer Zählerstand muss größer als alter Zählerstand sein!")
            return redirect(url_for('fabuchta56_dialog', userid=userid, old_total=int(old_total), platz=platz, belegnr=belegnr))
            
        date_string = parser.parse(request.form["datum"])
        xMengeGut = new_total - int(old_total) # Difference = new_total - old_total
        if xMengeGut < 0:
            flash(f"Neuer Zählerstand muss größer als alter Zählerstand sein!")
            return redirect(url_for('fabuchta56_dialog', userid=userid, old_total=old_total, platz=platz, belegnr=belegnr))
        
        xMengeAus = 0
        hour = int(request.form["uhrzeit"])
        xTS = date_string.strftime(f"%d.%m.%Y {hour}:00:00")  #Stringtransporter Datum 
        
        if xbuchen == True:
            write_log(f"BuchTA56_3: {xFAStatus, xTS, platz, xPersNr, xMengeGut, xMengeAus, xTE, xtrman, xta11nr, xcharge, new_total, xVal2, xVal3, xVal4, xVal5, xScanFA}")
            communicate(dll_instances[current_user.username], "BuchTA56_3", xFAStatus, xTS, platz, xPersNr, xMengeGut, xMengeAus, xTE, xtrman,
                                                            xta11nr, xcharge, new_total, xVal2, xVal3, xVal4, xVal5, xScanFA)
            communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, userid, '', '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')

        flash("Zählerstand erfolgreich zurückgemeldet.")
        return redirect(url_for('zaehlerstand_buttons', userid=userid))
    
    return render_template(
        "zaehlerdialog.html",
        date=datetime.now(),
        old_total=int(old_total),
        belegnr=belegnr,
        uhrzeit=list(range(1,25)),
        sidebarItems=get_list("sidebarItems")
    )


@app.route("/fabuchta55_dialog/<userid>/<menge_soll>/<xFAStatus>/<xFATS>/<xFAEndeTS>/<xScanFA>/<endroute>", methods=["POST", "GET"])
@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
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
        elif request.form["submit"] == "submit_cancel":
            write_log(f"fabuchta55_dialog: canceling")
            communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, userid, '', '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
            return redirect(url_for('home', username=username))
            
        try:
            error = "Sollmenge"
            menge_soll = float(request.form["menge_soll"])
            error = "Menge Aus"
            menge_aus = float(request.form["menge_aus"])
            error = "Menge Gut"
            menge_gut = float(request.form["menge_gut"])
            error = "Rüstzeit"
            ruestzeit = float(request.form["ruestzeit"])
        except ValueError:
            flash(f"Werte im Feld \"{error}\" müssen Zahlen sein! Nachkommastellen mit Punkt!")
            write_log(f"fabuchta55_dialog: ValueError")
            return redirect(url_for('fabuchta55_dialog', userid=userid, menge_soll=menge_soll, xFAStatus=xFAStatus,
                                    xFATS=xFATS, xFAEndeTS=xFAEndeTS, xScanFA=xScanFA, endroute=endroute))
        
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
            xPersNr = int(str(communicate(dll_instances[current_user.username], "gtv", "T910_Nr")))
            # print(xPersNr)
            # print(System.Decimal.ToInt32(xPersNr))
            # print(int(str(xPersNr)))
            xTE = communicate(dll_instances[current_user.username], "gtv", "TA06_TE")
            T905_NrSelected = communicate(dll_instances[current_user.username], "get", "T905_NrSelected")
            write_log(f"BuchTa55_3: {xFAStatus, xFATS, xFAEndeTS, T905_NrSelected, xPersNr, float(menge_gut), float(menge_aus), xTE, float(ruestzeit), lagerplatz, charge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA}")
            communicate(dll_instances[current_user.username], "BuchTA55_3", xFAStatus, xFATS, xFAEndeTS, T905_NrSelected, xPersNr, float(menge_gut), float(menge_aus), xTE,
                             float(ruestzeit), lagerplatz, charge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA)

            # Störung setzen
            if tl51use:
                T905_NrSelected = communicate(dll_instances[current_user.username], "get", "T905_NrSelected")
                write_log(f"BuchTA55_3_TL: {xFAEndeTS, T905_NrSelected}")
                communicate(dll_instances[current_user.username], "BuchTA55_3_TL", xFAEndeTS, T905_NrSelected)

            # directly add mengendialog for an Auftrag that is now starting, currently not implemented
            # if xInputMengeNew == 1:
                # add another Mengendialog, maybe just reroute with skip?
                # raise NotImplementedError

            communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, userid, '', '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')

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
@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
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
        T910_Nr = communicate(dll_instances[current_user.username], "gtv", "T910_Nr")
        TA06_FA_Nr = communicate(dll_instances[current_user.username], "gtv", "TA06_FA_Nr")
        TA06_BelegNr = communicate(dll_instances[current_user.username], "gtv", "TA06_BelegNr")
        T910_Entlohnung = communicate(dll_instances[current_user.username], "gtv", "T910_Entlohnung")
        T905_Nr = communicate(dll_instances[current_user.username], "gtv", "T905_Nr")
        TA06_TE = communicate(dll_instances[current_user.username], "gtv", "TA06_TE")
        TA06_TR = communicate(dll_instances[current_user.username], "gtv", "TA06_TR")
        TA06_FA_Art = communicate(dll_instances[current_user.username], "gtv", "TA06_FA_Art")
        communicate(dll_instances[current_user.username], "BuchTA51_3", xTSEnd, T910_Nr, TA06_FA_Nr, TA06_BelegNr,
                         xStatusMenge, T910_Entlohnung, T905_Nr, TA06_TE, TA06_TR, 0, float(menge_gut), float(menge_aus),
                         float(ruestzeit), lagerplatz, charge, xVal1, xVal2, xVal3, xVal4, xVal5, TA06_FA_Art, xTS)

        TA06_BelegNr = communicate(dll_instances[current_user.username], "gtv", "TA06_BelegNr")
        TA06_AgBez = communicate(dll_instances[current_user.username], "gtv", "TA06_AgBez")
        xret = "FA Buchen;MSG0166" + ";" + TA06_BelegNr + ";" + TA06_AgBez
        communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, userid, '', '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
        return redirect(url_for(home, username=username))

    return render_template(
        "mengendialog.html",
        date=datetime.now(),
        sidebarItems=get_list("sidebarItems")
    )


@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
def endta51cancelt905(apersnr):
    """Terminates all running GK and FA for user with 'apersnr'."""

    xret = ''
    msgr = ''
    xfa = ''
    xgk = ''
    final_ret = ''

    xmsg = communicate(dll_instances[current_user.username], "EndTA51GKCheck")
    logging.info('result EndTA51GKCheck: ' + xmsg)

    if len(xmsg) > 0:
        xret = "MSG0133" #Vorgang wurde abgebrochen
        if SHOWMSGGEHT[current_user.username] == 1:
            write_log(f'endta51cancelt905: vorangegangen GK beenden')
            # TODO: show modal
            model_yes = True  # user pressed yes
            if model_yes:
                userid = dbconnection.getUserID(apersnr)
                ret = dbconnection.doGKBeenden(userid, FirmaNr[current_user.username])
                result = communicate(dll_instances[current_user.username], "EndTA51GKSave")
                if ret==True:
                    final_ret = "GK"
                else:
                    flash("GK konnten nicht beendet werden!")
                    write_log(f'endta51cancelt905: GK konnten nicht beendet werden')
                    return "error"
            else:  # user pressed no, cancel booking
                flash("GK Buchung abgebrochen!")
                return "error"
            
            msgr='ok'
        else:
            # just terminate GK without asking
            write_log(f'endta51cancelt905: vorangegangen GK beenden')
            userid = dbconnection.getUserID(apersnr)
            ret = dbconnection.doGKBeenden(userid, FirmaNr[current_user.username])
            result = communicate(dll_instances[current_user.username], "EndTA51GKSave")
            if ret==True:
                final_ret = "GK"
            else:
                flash("GK konnten nicht beendet werden!")
                write_log(f'endta51cancelt905: GK konnten nicht beendet werden')
                return "error"
            msgr='ok'

    if msgr == 'ok':
        if GKENDCHECK[current_user.username] == 1:
            write_log('dialog GK-Kosten ändern (Platz/Belegnummer/Anfangszeitpunkt/Endezeitpunkt')
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
    result = communicate(dll_instances[current_user.username], "EndTA51FACheck", xfa, xgk)
    #21.11.2023
    xret, xfa, xgk = result
    # xfa, xgk = result

    if xret is None:
        xret = ''
    write_log(f'endta51cancelt905 xret: {xret}, xfa: {xfa}, xgk: {xgk}')

    # FA sind zu beenden
    if len(xfa) > 0:
        write_log('Info mit Eingabeaufforderung S903_ID=MSG0132 "Sollen alle laufenden Aufträge ohne Mengeneingabe beendet werden? ok/no"')
        result = communicate(dll_instances[current_user.username], "EndTA51Save")
        final_ret = "FA"

    # GK sind zu beenden
    if len(xgk) > 0:
        result = communicate(dll_instances[current_user.username], "EndTA51GKSave")
        final_ret = "GK"

    return final_ret


@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
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
    dr_T905 = communicate(dll_instances[current_user.username], "get", "dr_T905")
    if dr_T905 is not None:
        write_log("dr_T905 vorhanden")
        #Vor Buchung, prüfen, ob Kst der Person mit der Kst des zu buchenden Arbeitsplatz stimmt! Wenn nicht Wechsebuchung erzeugen!
        #Wechselbuchung triggert auf T955!!
        communicate(dll_instances[current_user.username], "BuFAWB", ATA29Nr)

    # Auftrag finden
    dr_TA06 = communicate(dll_instances[current_user.username], "get", "dr_TA06")
    if dr_TA06 is not None:
        write_log('bufa CO drta06 exist')
    else:
        # FANr wird gescannt und über T905ArbGRNr oder T909 und Platz Soll wird Beleg gefunden
        # Buchung auf FA_Nr
        dr_TA05 = communicate(dll_instances[current_user.username], "get", "dr_TA05")
        if dr_TA05 is not None:
            xt905nr = communicate(dll_instances[current_user.username], "gtv", "T905_Nr")
            xfanr = communicate(dll_instances[current_user.username], "gtv", "TA05_FA_Nr")
            result = communicate(dll_instances[current_user.username], "TA06ReadArbGrNr", xfanr, xt905nr)
            write_log('TA06Read ' + result)
            if result == 1:
                xScanFA = 1
            else:
                xFehler = xfanr

    if len(xFehler) == 0:
        # Prüfen, ob FA bebucht werden darf
        dr_TA06 = communicate(dll_instances[current_user.username], "gtv", "dr_TA06")
        result = communicate(dll_instances[current_user.username], "BuFANr0Status", xbBuchZiel)
        xret, xbBuchZiel = result
        write_log('Bufanrstatus ' + xret + ', Buchziel ' + str(xbBuchZiel))

        if len(xFehler) == 0:
            if xbBuchZiel == 1:

                result = communicate(dll_instances[current_user.username], "BuchTA55_0", xInputMenge, xInputMengeNew, xFARueckEnd, xScanFA, xFAStatus, xFATS, xFAEndeTS,
                                          xFAMeGut, xFAMeGes, xFANewScanFA, xFANewStatus, xFANewMeGes, xFANewMe)
                xret, xInputMenge, xInputMengeNew, xScanFA, xFAStatus, xFATS, xFAEndeTS, xFAMeGut, xFAMeGes, xFANewScanFA, xFANewStatus, xFANewMeGes, xFANewMe = result
                write_log(f"BuchTA55_0: {result}")
                if len(xret) > 0:
                    # cancel
                    flash("Buchung fehlgeschlagen!")
                    write_log(f"Buchung fehlgeschlagen!")
                    usernamepd = dbconnection.getPersonaldetails(userid)
                    username = usernamepd['formatted_name']
                    communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, userid, sa, '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
                    return redirect(url_for("home", username=username))

                if xInputMenge == 1:
                    # show Mengendialog
                    write_log("Mengendialog")
                    xScanFA = str(xScanFA)
                    return redirect(url_for("fabuchta55_dialog", userid=userid, menge_soll=xFAMeGes, xFAStatus=xFAStatus,
                                            xFATS=xFATS, xFAEndeTS=xFAEndeTS, xScanFA=xScanFA, endroute=endroute))
                else:
                    # don't show Mengendialog
                    write_log("Kein Mengendialog")
                    xFehler = fabuchta55(userid, xFAMeGes, xFAStatus, xFATS, xFAEndeTS, xScanFA)
                    communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, userid, '', '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
                    flash("Fertigungsauftrag gebucht.")
                    usernamepd = dbconnection.getPersonaldetails(userid)
                    username = usernamepd['formatted_name']
                    return redirect(url_for("home", username=username))
            
            if xbBuchZiel == 2:
                if platz is None:
                    xPlatz = ""
                else:
                    xPlatz = platz
                dr_TA06 = communicate(dll_instances[current_user.username], "get", "dr_TA06")
                if dr_TA06 is not None:
                    belegnr = communicate(dll_instances[current_user.username], "gtv", "TA06_BelegNr")
                write_log(f"Buchziel 2: Belegnr:{belegnr}")
                # letzten Zählerstand holen und Platz wird aus Soll_Platz des FA geholt (jeder Zähler ist einem anderen Platz zugeordnet, Person bucht für andere)
                result = communicate(dll_instances[current_user.username], "BuchTA56_0", xPlatz)
                xret, xPlatz = result
                write_log(f"BuchTA56_0: xret:{xret}, xPlatz:{xPlatz}")
                dr_TA56 = communicate(dll_instances[current_user.username], "get", "dr_TA56")
                if dr_TA56 is not None:
                    old_total = int(communicate(dll_instances[current_user.username], "gtv", "TA56_Wert")) # letzter Zählerstand
                return redirect(url_for("fabuchta56_dialog", userid=userid, old_total=old_total, belegnr=belegnr, platz=xPlatz))
            else:
                usernamepd = dbconnection.getPersonaldetails(userid)
                username = usernamepd['formatted_name']
                return fabuchta51(ata22dauer=ata22dauer, aAnfangTS=aAnfangTS, aEndeTS=aEndeTS, platz=platz, aBem=aBem, username=username)
    else:
        usernamepd = dbconnection.getPersonaldetails(userid)
        username = usernamepd['formatted_name']
        xFehler = ("Kein Auftrag!", ata22dauer)
        dr_TA06 = communicate(dll_instances[current_user.username], "get", "dr_TA06")
        dr_TA05 = communicate(dll_instances[current_user.username], "get", "dr_TA05")
        if dr_TA06 is not None and dr_TA05 is None:
            xFehler = ("Keine Kopfdaten vorhanden!", ata22dauer)
            write_log(f"Keine Kopfdaten vorhanden!, ata22dauer:{ata22dauer}")
            flash("Keine Kopfdaten vorhanden!")
            return redirect(url_for("home", username=username))
        flash("Keinen Auftrag gefunden!")
        write_log(f"Keinen Auftrag gefunden!")
        return redirect(url_for("home", username=username))

    return xFehler


@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
def start_booking(nr):
    """Starts the booking process for given card nr."""

    activefkt = ""
    buaction = 7
    bufunktion = 0
    result = communicate(dll_instances[current_user.username], "ShowNumber", nr, activefkt, SCANTYPE, SHOWHOST, SCANON, KEYCODECOMPENDE, False, "")
    ret, checkfa, sa = result
    write_log(f"ShowNumber ret: {ret}, checkfa: {checkfa}, sa: {sa}")
    result = communicate(dll_instances[current_user.username], "Pruef_PNr", checkfa, nr, sa, bufunktion)
    ret, sa, bufunktion = result
    write_log(f"PruefPNr ret: {ret}, sa: {sa}, bufunktion: {bufunktion}")
    
    result = communicate(dll_instances[current_user.username], "Pruef_PNrFkt", nr, bufunktion, SCANTYPE, sa, buaction, APPMSCREEN2, SERIAL, activefkt, "",
                                "", "")
    ret, sa, buaction, activefkt, msg, msgfkt, msgdlg = result
    write_log(f"Pruef_PNrFkt ret: {ret}, sa: {sa}, buaction: {buaction}, activefkt: {activefkt}, msg: {msg}")

    return ret, sa, buaction, bufunktion, activefkt, msg, msgfkt, msgdlg


@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
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
		
    # Auftrag in DB schreiben
    # xClDetails noch zu lösen
    xPersNr = communicate(dll_instances[current_user.username], "gtv", "T910_Nr")
    xTE = communicate(dll_instances[current_user.username], "gtv", "TA06_TE")
    xScanFA = int(xScanFA)  # make sure dtype is correct
    T905_NrSelected = communicate(dll_instances[current_user.username], "get", "T905_NrSelected")
    write_log(f"BuchTA55_3 input: {xFAStatus, xFATS, xFAEndeTS, T905_NrSelected, xPersNr, xFAMeGut, xMengeAus, xTE, xtrman, xta11nr, xcharge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA}")
    communicate(dll_instances[current_user.username], "BuchTA55_3", xFAStatus, xFATS, xFAEndeTS,
                T905_NrSelected, xPersNr, xFAMeGut, xMengeAus, xTE, xtrman, xta11nr, xcharge, xVal1,
                xVal2, xVal3, xVal4, xVal5, xScanFA)

    #Störung setzen
    #MDEGK_Ruest FA-Nr für Rüsten muß in Global Param definiert sein
    if tl51use == True:
        T905_NrSelected = communicate(dll_instances[current_user.username], "get", "T905_NrSelected")
        communicate(dll_instances[current_user.username], "BuchTA55_3_TL", xFAEndeTS, T905_NrSelected)
    
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
    
    return  "" #fabuchta55


@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
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

    xTA22Dauer = int(communicate(dll_instances[current_user.username], "gtv", "TA22_Dauer"))  # aus TA06 gelesen
    if ata22dauer.isnumeric():
        xTA22Dauer = int(ata22dauer)  # if given, take assume this

    write_log(f"PRE BuchTA51_0 xTA22Dauer: {xTA22Dauer}, xTS: {xTS}, xStatusMenge: {xStatusMenge}")
    result = communicate(dll_instances[current_user.username], "BuchTA51_0", xTA22Dauer, xTS, xStatusMenge)
    xret, xTS, xStatusMenge = result
    xAnfangTS = datetime.strptime(xTS, DTFORMAT)
    write_log(f"BuchTA51_0 xret: {xret}, xTS: {xTS}, xStatusMenge: {xStatusMenge}")
    if not aAnfangTS is None and not aEndeTS is None:  # when booking with given Dauer
        xStatusMenge = "20"  # TODO: bug in DLL, temporarily overwrite, 20 means just book, don't validate further

    write_log("xTS:" + xTS + " Datum:" + xAnfangTS.strftime(DTFORMAT))
    if len(xret) > 0:
        flash("Laufende Aufträge beendet.")
        communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, nr, '', '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
        write_log(f"Buch4Clear: nr:{nr}, sa:{''}, buaction:{1}")
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
        xta22typ = communicate(dll_instances[current_user.username], "gtv", "TA22_Typ")
        write_log("xta22typ:" + xta22typ)
        if xta22typ == "7":
            xDialog = True
            if xDialog == True:
                xTSEnd = xEndeTS.strftime("%d.%m.%Y %H:%M:%S")
                xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S") 
                if platz == None:
                    platz = communicate(dll_instances[current_user.username], "gtv", "T905_Nr")
                
                T910_Nr = communicate(dll_instances[current_user.username], "gtv", "T910_Nr")
                TA06_FA_Nr = communicate(dll_instances[current_user.username], "gtv", "TA06_FA_Nr")
                TA06_BelegNr = communicate(dll_instances[current_user.username], "gtv", "TA06_BelegNr")
                T910_Entlohnung = communicate(dll_instances[current_user.username], "gtv", "T910_Entlohnung")
                TA06_TE = communicate(dll_instances[current_user.username], "gtv", "TA06_TE")
                TA06_TR = communicate(dll_instances[current_user.username], "gtv", "TA06_TR")
                TA06_FA_Art = communicate(dll_instances[current_user.username], "gtv", "TA06_FA_Art")
                xMengeGut = 0
                xMengeAus = 0
                communicate(dll_instances[current_user.username], "BuchTA51_3", xTSEnd, int(str(T910_Nr)), TA06_FA_Nr, TA06_BelegNr, xStatusMenge,
                                                                T910_Entlohnung, platz, TA06_TE, TA06_TR, 0, xMengeGut, xMengeAus,
                                                                xTRMan, xTA11Nr, xCharge, xVal1, xVal2, xVal3, xVal4, xVal5,
                                                                TA06_FA_Art, xTS)
                
                #msg0166=Auftrag "_Msg1" wurde gebucht!
                TA06_BelegNr = communicate(dll_instances[current_user.username], "gtv", "TA06_BelegNr")
                TA06_AgBez = communicate(dll_instances[current_user.username], "gtv", "TA06_AgBez")
                xret = "FA Buchen;MSG0166" + ";" + TA06_BelegNr + ";" + TA06_AgBez
            else:
                # 'EvtMsgDisplay("FA Buchen", "MSG0133", "", "")
                #MSG0133=Vorgang wurde abgebrochen
                xret = "FA Buchen;MSG0133;;"
                         
            # dialogue is needed so reroute to route for Mengendialog
            return redirect(url_for("fabuchta51_dialog", userid=nr))
        else:
            # vorangegangenen Auftrag unterbrechen
            xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")
            T910_Nr = communicate(dll_instances[current_user.username], "gtv", "T910_Nr")
            t901_nr_print = int(str(T910_Nr))
            write_log(f"PRE BuchTa51_4_Cancel xTS: {xTS}, T910_Nr: {t901_nr_print}")
            communicate(dll_instances[current_user.username], "BuchTA51_4_Cancel", xTS, int(str(T910_Nr)))

            TA22_Dauer = int(communicate(dll_instances[current_user.username], "gtv", "TA22_Dauer"))
            if TA22_Dauer != 1:
                if aAnfangTS is None and aEndeTS is None:
                    # if not booking with Dauer, add a second for safety (?)
                    xAnfangTS = xAnfangTS + timedelta(seconds = 1) #xAnfangTS.AddSeconds(1)
                xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")
                
                xcl = Generic.Dictionary[String,Object]() #leere liste
                xdmegut = communicate(dll_instances[current_user.username], "gtv", "TA06_Soll_Me")
                xsmegut = str(xdmegut)
                xmegut = float(xsmegut.replace(",","."))
                if platz == None:
                    platz = communicate(dll_instances[current_user.username], "gtv", "T905_Nr")
                
                T910_Nr = communicate(dll_instances[current_user.username], "gtv", "T910_Nr")
                TA06_FA_Nr = communicate(dll_instances[current_user.username], "gtv", "TA06_FA_Nr")
                TA06_BelegNr = communicate(dll_instances[current_user.username], "gtv", "TA06_BelegNr")
                T910_Entlohnung = communicate(dll_instances[current_user.username], "gtv", "T910_Entlohnung")
                TA06_TE = communicate(dll_instances[current_user.username], "gtv", "TA06_TE")
                TA06_TR = communicate(dll_instances[current_user.username], "gtv", "TA06_TR")
                TA06_FA_Art = communicate(dll_instances[current_user.username], "gtv", "TA06_FA_Art")
                xret = communicate(dll_instances[current_user.username], "BuchTA51_3", xTSEnd, int(str(T910_Nr)), TA06_FA_Nr,
                                                                       TA06_BelegNr, xStatusMenge, T910_Entlohnung,
                                                                       platz, TA06_TE, TA06_TR, 0.0, xmegut,
                                                                       float(0.0), xTRMan, xTA11Nr, xCharge, xVal1,
                                                                       xVal2, xVal3, xVal4, xVal5, TA06_FA_Art, xTS)
                write_log(f"2nd BuchTA51_3: {xret}")
            
            TA06_BelegNr = communicate(dll_instances[current_user.username], "gtv", "TA06_BelegNr")
            TA06_AgBez = communicate(dll_instances[current_user.username], "gtv", "TA06_AgBez")
            xret = "FA Buchen;MSG0166" + ";" + TA06_BelegNr + ";" + TA06_AgBez
    communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, nr, '', '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
    write_log(f"Buch4Clear: nr:{nr}, sa:{''}, buaction:{1}")
    flash("Gemeinkosten erfolgreich gebucht.")
    return redirect(url_for("home", username=username))


@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
def actbuchung(kst="", t905nr="", salast="", kstlast="", tslast="", APlatz="", nr="", username="", sa="",
               arbeitsplatz=None, ata22dauer="", AAnfangTS=None, AEndeTS=None, aBem=None, endroute="home"):
    """K/G/A booking according to sa for user with given card nr and username."""
    xT905Last = ""
    xTA29Last = ""
    xtagid=''
    xkstk=0
    xfaruecknr=''
    xmenge=0
    result = communicate(dll_instances[current_user.username], "CheckKommt", sa, kst, salast, kstlast, tslast, xT905Last, xTA29Last)
    xret, ASALast, AKstLast, ATSLast, xT905Last, xTA29Last = result
    write_log(f"CheckKommt ret: {xret}, ASALast: {ASALast}, AKstLast: {AKstLast}, ATSLast: {ATSLast}, xT905Last: {xT905Last}, xTA29Last: {xTA29Last}")

    if len(xret) > 0:  # Fehler
        dr_TA06 = communicate(dll_instances[current_user.username], "get", "dr_TA06")
        dr_TA05 = communicate(dll_instances[current_user.username], "get", "dr_TA05")
        if dr_TA06 is not None or dr_TA05 is not None:
            flash("Fehler: Keine Auftragsbuchung ohne Kommt!")
            write_log("Keine Auftragsbuchung ohne Kommt!")
            communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, nr, sa, '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
            return redirect(url_for("home", username=username))
        if (xret=="MSG0065" and sa=="A") or (xret=="MSG0065" and sa=="G"):  # MSG0065 is ok if current Buchung is K
            flash("Fehler: Keine \"Kommt\"-Buchung vorhanden!")
            write_log(f"Keine \"Kommt\"-Buchung vorhanden!, nr:{nr}, sa:{sa}")
            communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, nr, sa, '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')
            return redirect(url_for("home", username=username))

    xpersnr = communicate(dll_instances[current_user.username], "T910NrGet")
    xret = ""

    cancel_xret = endta51cancelt905(xpersnr)
    write_log(f"endta51cancelt905: {cancel_xret}")
    if cancel_xret == 'GK':
        flash('Laufende GK-Aufträge wurden beendet!')
    elif cancel_xret == 'FA':
        flash('Laufende FA-Aufträge wurden beendet!')
    elif cancel_xret == 'error':
        # flash of error already called in endta51cancelt905
        return redirect(url_for("home", username=username))

    dr_T905 = communicate(dll_instances[current_user.username], "get", "dr_T905")
    if dr_T905 is not None:
        t905nr = communicate(dll_instances[current_user.username], "gtv", "T905_Nr")

    dr_TA06 = communicate(dll_instances[current_user.username], "get", "dr_TA06")
    dr_TA05 = communicate(dll_instances[current_user.username], "get", "dr_TA05")
    if dr_TA06 is not None or dr_TA05 is not None:
        write_log("TA06 or TA05 True")
        if dr_TA06 is not None:
            write_log("TA06 True")
            T951_Arbist = communicate(dll_instances[current_user.username], "gtv", "T951_Arbist")
            TA06_Platz_Soll = communicate(dll_instances[current_user.username], "gtv", "TA06_Platz_Soll")
            if T951_Arbist != TA06_Platz_Soll:
                write_log("Abweichender Platz")
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
                    write_log("Abweichender Platz, Umbuchen nicht erlaubt")
                    flash("Abweichender Platz, Umbuchen nicht erlaubt!")
                    return redirect(url_for("home", username=username))

        if len(xret) == 0:
            if dr_T905 is None:
                dr_T951 = communicate(dll_instances[current_user.username], "get", "dr_T951")
                if dr_T951 is not None:
                    T951_Arbist = communicate(dll_instances[current_user.username], "gtv", "T951_Arbist")
                    communicate(dll_instances[current_user.username], "T905Read", T951_Arbist)

            T905_Nr = communicate(dll_instances[current_user.username], "gtv", "T905_Nr")
            communicate(dll_instances[current_user.username], "set", "T905_NrSelected", T905_Nr)
            TA06_BelegNr = communicate(dll_instances[current_user.username], "gtv", "TA06_BelegNr")
            return bufa(ANr=TA06_BelegNr, ata22dauer=ata22dauer, aAnfangTS=AAnfangTS, aEndeTS=AEndeTS, platz=arbeitsplatz, aBem=aBem, userid=nr, endroute=endroute)

    if len(xret) == 0:
        if len(xret) == 0:
            if sa == "K":
                return redirect(url_for(
                    'anmelden',
                    userid=nr,
                    sa=sa
                ))
            elif sa == "G":
                result = communicate(dll_instances[current_user.username], "PNR_Buch", sa, kst, t905nr, '', '', '', 0)
                xret, ASA, AKst, APlatz, xtagid, xkstk = result
                if GKENDCHECK[current_user.username] is True:  # Param aus X998 prüfen laufende Aufträge
                    xret = communicate(dll_instances[current_user.username], "PNR_Buch2Geht")
                flash("User wurde abgemeldet.")
            elif sa == 'A':
                result = communicate(dll_instances[current_user.username], "PNR_Buch", sa, kst, t905nr, '', '', '', 0)
                xret, ASA, AKst, APlatz, xtagid, xkstk = result
                flash(arbeitsplatz)
                write_log(f"Booked Arbeitsplatz: {arbeitsplatz}")

            if len(xret) == 0:
                write_log(f"PNR_Buch3: xtagid:{xtagid}, sa:{sa}, AKst:{AKst}, APlatz:{APlatz}")
                communicate(dll_instances[current_user.username], "PNR_Buch3", xtagid, sa, AKst, APlatz, '', '', 0)
            write_log(f"PNR_Buch4Clear: nr:{nr}, sa:{sa}")
            communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, nr, sa, '', 1, GKENDCHECK[current_user.username], '', '', '', '', '')

        return redirect(url_for("home", username=username))


@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
def ta06gkend(userid,AScreen2=None):
	
	xMsg = communicate(dll_instances[current_user.username], "EndTA51GKCheck")
	if len(xMsg) == 0:
		flash("Keine GK zu Beenden!") # Es gibt keine Gemeinkostenaufträge zu beenden!  || nothing to terminate
	else:
		ret = dbconnection.doGKBeenden(userid, FirmaNr[current_user.username])
		if ret==True:
			flash("Laufende Aufträge beendet.")
		else:
			flash("GK konnten nicht beendet werden!")


@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
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
		write_log("nur gelöscht")
		# result = communicate(dll_instances[current_user.username], "PNR_Buch4Clear", 1, scanvalue, sa, platz, buaction, gkendcheck, activefkt, msgfkt, msgbuch, msgzeit, msgpers)
		return "Nur gelöscht"


@retry_db_calls(max_retries=DB_RETRIES, timeout=DB_TIMEOUT)
def gk_erstellen(userid, dauer, date):
	# create Auftragsbuchung with Dauer
	persnr = dbconnection.getPersonaldetails(userid)["T910_Nr"]
	anfang_ts, ende_ts = dbconnection.doFindTS(persnr, dauer, date, FirmaNr[current_user.username])
	if anfang_ts is None and ende_ts is None:
		write_log("Keine neue Zeitperiode gefunden!")
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
                 # "Arbeitsplatzbuchung", "Gruppenbuchung",
                 "Gemeinkosten ändern", "FA erfassen", "Zählerstandsrückmeldung"],
                ["arbeitsplatzwechsel", "gemeinkosten_buttons", "status", "gemeinkostenbeenden",
                 # "arbeitsplatzbuchung", "gruppenbuchung",
                 "gemeinkostenandern", "fertigungsauftragerfassen", "zaehlerstand_buttons"]]

    if listname == "gemeinkostenItems":
        gk_info = dbconnection.getGemeinkosten(userid, FirmaNr[current_user.username])
        return [gk_info["TA05_ArtikelBez"], gk_info["TA06_BelegNr"]]
    
    if listname == "zaehlerItems":
        private_data, global_data = dbconnection.getZaehler(userid, FirmaNr[current_user.username])
        return [private_data["TA05_ArtikelBez"], private_data["TA06_BelegNr"], global_data["TA05_ArtikelBez"], global_data["TA06_BelegNr"]]

    if listname == "sidebarItems":
        return [["Wechselbuchung", "Gemeinkosten", "Status", "Gemeinkosten Beenden",
                 # "Arbeitsplatzbuchung", "Gruppenbuchung",
                 "Gemeinkosten ändern", "FA erfassen", "Zählerstandsrückmeldung"],
                ["arbeitsplatzwechsel", "gemeinkosten_buttons", "status", "gemeinkostenbeenden",
                 # "arbeitsplatzbuchung", "gruppenbuchung",
                 "gemeinkostenandern", "fertigungsauftragerfassen", "zaehlerstand_buttons"]]

# if __name__ == '__main__':
    
    # app.run(debug=True)