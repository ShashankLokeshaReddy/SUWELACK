import sys
import clr
#original
#http://pythonnet.github.io



#syntx datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
#Buchungsfunktion
#0-acfKG 'Kommt/GehtBuchung
#,1-acfKST 'Kostenstellenbuchung
#,2-acfT905 'Arbeitsplatzbuchung entweder Arbeitsplatz und dann Auftrag durchgezogen
#,3-acfTA05 'TA05 oder TA06-Buchung, abhängig davon, welche Nr. gefunden wurde dr_ta05 oder dr_ta06
#,4-acfTA02 'Colli buchen
#,5-acfPause
#,6-acfNone
#,7-acfInfo
#,8-acfFA  'Auftragsbuchung - Buchen auf FANr
#,9-acfFAEnd 'einen lfd. Auftrag unterbrechen/beenden
#,10-acfWeBtnbAct 'Button vom Web mit Personalnr. aktivieren
#,11-acFAAdminGK '02.07.2019 - GK letzte 2 Tage
#,12-acFAAdmin 'FA man. nachbuchen letzte 2 Tage

#Buchungsaktion
#0-ktacAdmin
#1-ktacBuchung
#2-ktacZuschlag
#3-ktacRuest
#4-ktacInfo 'Anzeige Flexkonto/Urlaubskonto
#5-ktacStatus 'Anzeige aktueller Buchungsstatus
#6-ktacInfoPrint
#7-ktacIgnore
#8-ktacTA06FA '09.05.2017
#9-ktacTA06GK 'GK-Auftrag Platzbezogen buchen
#10-ktacTA06END
#11-ktacGKZuo 'GK definieren (Störungen festlegen)
#12-ktacFABuch 'FA am Terminal anzeigen und buchen (Platz auswählen, dann Personalnr)
#13-ktacFASerie 'Serie/Arbeitsplatz anzeigen (Platz wird über Personalnr. ermittelt)
#14-ktacFABD 'FA nachträglich am Terminal buchen
#15-ktacWEB 'Browser starten
#16-ktacWEBAct 'Browser vom Button aus aktivieren
#17-ktacList 'FKTLST 
#18-ktacFAAdminGK '02.07.2019 FAAdmin (Gemeinkosten letzte 2 Tage verwalten)
#19-ktacFAAdmin '03.07.2019 (FA letzte 2 Tage)
       
#Scantype
#0-ktscTS 'Tastaturgeschliffen
#1-ktscCS 'Seriell über COM (interrupt)
#2-ktscTP 'Transponder (wie COM!! - nicht benutzt)
#3-ktscNone '=3
        


from datetime import datetime,timedelta   



#sys.path.append("c:\temp\testpks")
clr.AddReference("kt002_PersNr") 
clr.AddReference("System.Collections")
from System.Collections import Generic
#from System import *
from System.Collections import Hashtable
from System import String
from System import Object

from kt002_persnr import kt002
kt002.Init()   
kt002.InitTermConfig()
dtformat = "%d.%m.%Y %H:%M:%S"
dformat = "%d.%m.%Y"


"""
Routine zum Prüfen auf laufende Aufträge und Gemeinkosten
bei den Prints sollten Info-Ausgaben am Terminal kommen
hier gibt es die Optionen mit Eingabeaufforderung oder nur Anzeige, die dann selbständig verschwindet
"""
def endta51cancelt905(apersnr):
	print('in endta51cancel')
	xret=''
	msgr=''
	xfa=''
	xgk=''
	xbcancel=0
	
	xmsg=kt002.EndTA51GKCheck()
	print ('result EndTA51GKCheck:' + xmsg)
	
	if len(xmsg)>0:
		xret = "MSG0133" #Vorgang wurde abgebrochen
		if showmsggeht == 1:
			print('Info mit Eingabeaufforderung S903_ID=MSG0178 "GK müssen erst beendet werden!"')
			#ok oder no Eingabe
			msgr='ok'
		else:
			print('Info OHNE Eingabeaufforderung S903_ID=MSG0178 "GK müssen erst beendet werden!"')
			#geht mit ok weiter
			msgr='ok'
	
	if msgr == 'ok':
		if gkendcheck == 1:
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
			print('sql')
	else:
		xbcancel=1 #nix zu beenden
	
	if xbcancel == 1:
		return xret
	
	
	#Prüfen ob Fertigungsaufträge und GK-Aufträge laufen am anderen Platz laufen
	result=kt002.EndTA51FACheck(xfa, xgk)
	#print ('endta51cancelt905 bei result=kt002.EndTA51FACheck:')
	#print (result)
	xret,xfa,xgk=result #ist prozedur, weiß nicht ob rückgabewert dabei ist
	if xret is None:
		xret=''
	print('endta51cancelt905 xret:' + xret + ' xfa:' + xfa + ' xgk:' + xgk)


	#FA sind zu beenden
	if len(xfa)>0:
		print('Info mit Eingabeaufforderung S903_ID=MSG0132 "Sollen alle laufenden Aufträge ohne Mengeneingabe beendet werden? ok/no"')
		msgr=ok
		if msgr==ok:
			result=kt002.EndTA51Save()
		else:
			xret='false'

	#GK sind zu beenden
	if len(xgk)>0:
		print('Info mit Eingabeaufforderung S903_ID=MSG0180 "Laufende GK-Aufträge an _Msg1 werden beendet! ok"')
		kt002.EndTA51GKSave() #T905 muß gelesen sein kspr_TA51UpdateFAEndGKFB1
	
	return xret #endta51cancelt905(apersnr):

#Globale Auftragsbuchung
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
	serial=True

	#ByRef AInputMenge As Int16, ByRef AInputMengeNew As Int16, ByVal AFARueckEnd As Boolean, ByRef AScanFA As Integer _
	#, ByRef AFAStatus As String, ByRef AFATS As DateTime, ByRef AFAEndeTS As DateTime, ByRef AFAMeGut As Double, ByRef AFAMeGes As Double _
	#, ByRef AFANewScanFA As Integer, ByRef AFANewStatus As String, ByRef AFANewMeGes As Double, ByRef AFANewMe As Double
	result = kt002.BuchTA55_0(xInputMenge, xInputMengeNew, xFARueckEnd, xScanFA, xFAStatus, xFATS, xFAEndeTS, xFAMeGut, xFAMeGes, xFANewScanFA, xFANewStatus, xFANewMeGes, xFANewMe)
	xret,xInputMenge, xInputMengeNew,xScanFA, xFAStatus, xFATS, xFAEndeTS, xFAMeGut, xFAMeGes, xFANewScanFA, xFANewStatus, xFANewMeGes, xFANewMe=result
	#print("kt002.BuchTA55_0:" + xret + "," + str(xInputMenge) + "," +  str(xInputMengeNew)  + "," + str(xScanFA) + "," +  xFAStatus+ "," +  xFATS + "," +  xFAEndeTS + "," +  str(xFAMeGut+ "," +  str(xFAMeGes) + "," + str(xFANewScanFA) + "," +  xFANewStatus + "," +  str(xFANewMeGes) + "," +  str(xFANewMe))
	print(result)
	if len(xret) > 0:
		xbuchen=False

	if xInputMenge == 1:
		#HIER MENGENDIALOG return xbuchen
            #Diese Routine in Python erstellen
            #xbuchen = kt001_InputMenge_Modus(Nothing, ActModus, kt002.dr_TA06Buch("TA06_RueckArt"),
            #kt002.dr_TA06Buch("TA06_BelegNr"), kt002.dr_TA06Buch("TA06_AgBez"), kt002.T905_NrSelected, kt002.dr_TA06Buch("TA06_Soll_Me"), kt002.dr_TA06Buch("TA06_Ist_Me_gut"), kt002.dr_TA06Buch("TA06_Ist_Me_Aus") _
            #, xFAMeGut, xMengeAus, xtrman, xta11nr, xFAStatus, xcharge, xVal1, xVal2, xVal3, xVal4, xVal5, xFARueckEnd, xClDetails)
		print ("Dialog TA55")
		
		
	if xbuchen == True:
		#Auftrag in DB schreiben
		#xClDetails noch zu lösen
		xPersNr = kt002.gtv("T910_Nr")
		xTE = kt002.gtv("TA06_TE")
		#BuchTA55_3(ByVal AAufStat As String, ByVal ADatumTS As DateTime, ByVal AEndeTS As DateTime _
		#, ByVal APlatzIst As String, ByRef APersNr As Long _
		#, ByVal AMengeGut As Double, ByVal AMengeAus As Double, ByVal ATE As Double, ByVal ATRMan As Double, ByVal ATA11Nr As String, ByVal ACharge As String _
		#, ByVal AVal1 As Double, ByVal AVal2 As Double, ByVal AVal3 As Double, ByVal AVal4 As Double, ByVal AVal5 As Double, ByVal AScanFA As Integer)
		kt002.BuchTA55_3( xFAStatus, xFATS, xFAEndeTS, kt002.T905_NrSelected, xPersNr, xFAMeGut, xMengeAus, xTE, xtrman, xta11nr, xcharge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA)

		#Störung setzen
		#MDEGK_Ruest FA-Nr für Rüsten muß in Global Param definiert sein
		if tl51use == True:
			kt002.BuchTA55_3_TL(xFAEndeTS, kt002.T905_NrSelected)
		

		if xInputMengeNew == 1:
			xMengeAus = 0
			xFATS = Now
			xFAEndeTS = xFATS
			#HIER MENGENDIALOG
			#xbuchen = kt001_InputMenge_Modus(Nothing, ActModus, kt002.dr_TA06BuchNew("TA06_RueckArt"),
			#kt002.dr_TA06BuchNew("TA06_BelegNr"), kt002.dr_TA06BuchNew("TA06_AgBez"), T905_NrSelected, kt002.dr_TA06BuchNew("TA06_Soll_Me"), kt002.dr_TA06BuchNew("TA06_Ist_Me_gut"), kt002.dr_TA06BuchNew("TA06_Ist_Me_Aus") _
			#, xFANewMe, xMengeAus, xtrman, xta11nr, xFANewStatus, xcharge, xVal1, xVal2, xVal3, xVal4, xVal5, xFARueckEnd, xClDetails)

			if xbuchen == True:
				#Auftrag in DB schreiben
				kt002.dr_TA06Buch = kt002.dr_TA06BuchNew
				#xClDetails, 
				xTE = kt002.gtv("TA06_TE")
				kt002.BuchTA55_3(xFANewStatus, xFATS, xFAEndeTS, T905_NrSelected, 0, xFANewMe, xMengeAus, xTE, xtrman, xta11nr, xcharge, xVal1, xVal2, xVal3, xVal4, xVal5, xScanFA)
	return  xret #fabuchta55

#Public Function PyFABuchTA51(ByVal ATA22Dauer As Object) As String
def fabuchta51(ata22dauer):
 	#Dim xret As String = ""
	#Dim xMsg As String = ""
	#Dim xClDetails As Collection = Nothing
	#Dim xMengeGut As Double = 0
	#Dim xMengeAus As Double = 0
	#Dim xUA51Id As Long = 0
	#Dim xTA22Dauer As Integer
	xStatusMenge = ""
	xTSLast = datetime.now()
	xEndeTS = datetime.now()
	xAnfangTS = xEndeTS
	xTS=xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")  #Stringtransporter Datum    
	xTSEnd=xAnfangTS.strftime("%d.%m.%Y %H:%M:%S") 


	#Dim xbFound As Boolean = True
	xTRMan = 0.0
	xTA11Nr = ""
	xCharge = ""
	xDauer = 0 
	xVal1 = 0.0
	xVal2 = 0.0
	xVal3 = 0.0
	xVal4 = 0.0
	xVal5 = 0.0
	xbCancel=False

	xTA22Dauer = kt002.gtv("TA22_Dauer") #aus TA06 gelesen
	if ata22dauer.isnumeric() == True:    # von außen übersteuern
	    xTA22Dauer = int(ata22dauer)
	
	#Function BuchTA51_0(ByVal ATA22Dauer As Integer, ByVal ATSAnf As Date, ByVal ATSEnd As Date, ByRef ATSLast As DateTime, ByRef AStatusMenge As String) As String
	
	print('TS' +  xAnfangTS.strftime("%d.%m.%Y %H:%M:%S") )
	result = kt002.BuchTA51_0(xTA22Dauer, xTS,  xStatusMenge)
	xret,xTS,xStatusMenge=result  
	xAnfangTS = datetime.strptime(xTS,dtformat)
	print("xTS:" + xTS + " Datum:" + xAnfangTS.strftime("%d.%m.%Y %H:%M:%S"))
	if len(xret) > 0:
		print("nur laufenden beendet. -Inhalt Message")
		return xret  #nur laufenden beendet. -Inhalt Message
	
	print("xTA22Dauer:" + str(xTA22Dauer))
	if xTA22Dauer == 3:
	    #HIER DIALOG dgt11 Gemeinkosten Buchungsdaten ändern
	    #xDauer = PNR_TA51GKEndDauer(xTSLast, kt002.dr_TA06("TA06_FA_Nr"), kt002.dr_TA06("TA06_BelegNr"), kt002.dr_TA06("TA06_AgBez"))
		if xDauer > 0:
			xAnfangTS = xEndeTS.AddMinutes(xDauer * -1)
			xAnfangTS = xAnfangTS.AddSeconds(-1) #1 sekunde wird wieder draufgerechnet!
		else:
			xbCancel = True
			xret = "MSG0133"

	#14.06.2013 - auf Ende buchen und Mengenabfrage
	if xbCancel == False:
		xta22typ=kt002.gtv("TA22_Typ")
		print("xta22typ:" + xta22typ)
		if kt002.gtv("TA22_Typ")  == "7":
			#HIER DIALOG PYTHON
	        #if kt001_InputMenge_Modus(Nothing, ActModus, kt002.dr_TA06("TA06_RueckArt"),
	        #         kt002.dr_TA06("TA06_BelegNr"), kt002.dr_TA06("TA06_AgBez"), T905_NrSelected, kt002.dr_TA06("TA06_Soll_Me"), kt002.dr_TA06("TA06_Ist_Me_gut"), kt002.dr_TA06("TA06_Ist_Me_Aus") _
	        #        , xMengeGut, xMengeAus, xTRMan, xTA11Nr, xStatusMenge, xCharge, xVal1, xVal2, xVal3, xVal4, xVal5, False, xClDetails) = True Then
			#NACH DIALOG buchen

			#Public Shared Function BuchTA51_3(ByVal AClDetails As Collection, ByVal ADate As Date, ByVal APersNr As Long, ByVal AFANr As String, ByVal ABelegNr As String, ByVal AStatus As String, ByVal AEntl As String, ByVal AArbPlatz As String,
			#	ByVal ATE As Double, ByVal ATR As Double, ByVal AZus As Double, ByVal AMengeIstGut As Double, ByVal AMengeIstAus As Double, ByVal ATRMan As Double, ByVal ATA11Nr As String, ByVal ACharge As String _
			#, ByVal AVal1 As Double, ByVal AVal2 As Double, ByVal AVal3 As Double, ByVal AVal4 As Double, ByVal AVal5 As Double _
			#, ByVal AFAArt As String, ByVal AAnfangTS As Date) As String
			xDialog=True
			if xDialog == True:
				xTSEnd = xEndeTS.strftime("%d.%m.%Y %H:%M:%S")
				xTS=xAnfangTS.strftime("%d.%m.%Y %H:%M:%S") 
				kt002.BuchTA51_3( xTSEnd, kt002.gtv("T910_Nr"), kt002.gtv("TA06_FA_Nr"), kt002.gtv("TA06_BelegNr"), xStatusMenge, kt002.gtv("T910_Entlohnung")
				,kt002.gtv("T905_Nr"), kt002.gtv("TA06_TE"), kt002.gtv("TA06_TR"), 0, xMengeGut, xMengeAus, xTRMan, xTA11Nr, xCharge, xVal1, xVal2, xVal3, xVal4, xVal5, kt002.gtv("TA06_FA_Art"), xTS)
				
				#EvtMsgDisplay("FA Buchen", "MSG0166", kt002.dr_TA06("TA06_BelegNr"), kt002.dr_TA06("TA06_AgBez"))
				#msg0166=Auftrag "_Msg1" wurde gebucht!
				xret = "FA Buchen;MSG0166" + ";" + kt002.gtv("TA06_BelegNr") + ";" + kt002.gtv("TA06_AgBez")
			else:
				# 'EvtMsgDisplay("FA Buchen", "MSG0133", "", "")
				#MSG0133=Vorgang wurde abgebrochen
				xret = "FA Buchen;MSG0133;;"


		else:
			#vorangegangenen Auftrag unterbrechen
			#Public Shared Sub BuchTA51_4_Cancel(ByVal ADate As Date, ByVal APersNr As Long)
			print("BUCHENFA")
			xTS=xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")
			kt002.BuchTA51_4_Cancel(xTS, kt002.gtv("T910_Nr"))
			#23.11.2010
			if kt002.gtv("TA22_Dauer") != 1:
				xAnfangTS = xAnfangTS + timedelta(seconds = 1) #xAnfangTS.AddSeconds(1)
				xTS=xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")
				
				xcl = Generic.Dictionary[String,Object]() #leere liste
				xdmegut=kt002.gtv("TA06_Soll_Me")
				xsmegut=str(xdmegut)
				xmegut=float(xsmegut.replace(",","."))
				#alle integer sind long in Python
				xret = kt002.BuchTA51_3(xTSEnd, int(kt002.gtv("T910_Nr")), kt002.gtv("TA06_FA_Nr"), kt002.gtv("TA06_BelegNr"),xStatusMenge,kt002.gtv("T910_Entlohnung"),kt002.gtv("T905_Nr"),kt002.gtv("TA06_TE"),kt002.gtv("TA06_TR"),0.0,xmegut,0.0,xTRMan, xTA11Nr, xCharge,xVal1,xVal2,xVal3,xVal4,xVal5,kt002.gtv("TA06_FA_Art"),xTS)
	        #EvtMsgDisplay("FA Buchen", "MSG0166", kt002.dr_TA06("TA06_BelegNr"), kt002.dr_TA06("TA06_AgBez"))
			xret = "FA Buchen;MSG0166" + ";" + kt002.dr_TA06.get_Item("TA06_BelegNr") + ";" + kt002.dr_TA06.get_Item("TA06_AgBez")

	return xret #fabuchta51




	
#PyBuFA(ByVal ANr As String, ByVal ATA29Nr As String, ByVal AFARueckend As Boolean, ByVal ATA22Dauer As Object) As String
#ta22dauer - Übersteuerung der Einstellung TA21 - Auftrag mit Dauer buchen
def bufa(ANr,ATA29Nr,AFARueckend,ata22dauer):
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


	#Auftrag finden
	if kt002.CheckObject(kt002.dr_TA06) == True:
		print('bufa CO drta06 exist')
	else:
		#FANr wird gescannt und über T905ArbGRNr oder T909 und Platz Soll wird Beleg gefunden
		#Buchung auf FA_Nr
		if kt002.CheckObject(kt002.dr_TA05) == True:
			xt905nr=kt002.gtv("T905_Nr")
			xfanr=kt002.gtv("TA05_FA_Nr")
			result = kt002.TA06ReadArbGrNr(xfanr,xt905nr )
			print ('TA06Read' + result)
			if result == 1:
				xScanFA = 1
			else:
				xFehler = xfanr



	if len(xFehler) == 0:
	    #Prüfen, ob FA bebucht werden darf
	    #setzen Zieltabelle
		result = kt002.BuFANr0Status(xbBuchZiel)
		xret,xbBuchZiel=result
		print ('Bufanrstatus' + xret + ' Buchzile'+ str(xbBuchZiel))
		
		if len(xFehler) == 0:
			if xbBuchZiel == 1:
				xFehler = fabuchta55()
			else:
				xFehler = fabuchta51(ata22dauer)
	       
	else:
		xFehler = "Kein Auftrag!"
		if kt002.CheckObject(kt002.dr_TA06) == True and kt002.CheckObject(kt002.dr_TA05)== False:
			xFehler = "Keine Kopfdaten vorhanden!"

	return xFehler #bufa



def actbuchung(ta29nr,AKst,ASA,t905nr,ASALast,AKstLast,ATSLast,APlatz):

	#Dim xret As String = ""
  #Dim xbcancel As Boolean 'temporär für test dll
  #Dim xkstk As Integer
  #Dim xfarueckend As Integer
  #Dim xtagid As Date
  #Dim xmenge As Integer
  #Dim xMsgBox As MsgBoxResult
  #Dim xFehler As String = ""
  #' Dim AKst As String
	xT905Last =''
	xTA29Last =''
	xtagid=''
	xkstk=0
	xfaruecknr=''
	xmenge=0
	
	print("actbuchung SA:" + ASA)
	#Public Shared Function CheckKommt(ByVal ASa As String, ByVal AKst As String,
  #ByRef ASALast As String, ByRef AKstLast As String, ByRef ATSLast As String, ByRef AT905Last As String, ByRef ATA29Last As String) as string
	result = kt002.CheckKommt(ASA, AKst, ASALast, AKstLast, ATSLast, xT905Last, xTA29Last)
	xret,ASALast,AKstLast,ATSLast,xT905Last,xTA29Last=result
	print(result)
	if len(xret) > 0:
		#'!!!MSG Warnung !!!!
		print("KEINE KOMMT BUCHUNG?")
		# 'keine Auftragsbuchung ohne Kommt!
		if kt002.CheckObject(kt002.dr_TA06)== True or kt002.CheckObject(kt002.dr_TA05)== True:
			return xret

	xret = ''
	
	xpersnr=kt002.T910NrGet()
	#if kt002.CheckObject(kt002.dr_T905)== False:
		#kt002.T905Read(xT905Last) #lesen Arbeitsplatz letzter Platz (bei Geht)


	xret = endta51cancelt905(xpersnr)
	
	if kt002.CheckObject(kt002.dr_T905)== True:
		t905nr = kt002.gtv("T905_Nr")
	print('Platz:' + t905nr)
	
	if kt002.CheckObject(kt002.dr_TA06) == True or kt002.CheckObject(kt002.dr_TA05) == True:
		if kt002.CheckObject(kt002.dr_TA06) == True:
			if kt002.gtv("T951_Arbist") != kt002.gtv("TA06_Platz_Soll"):
				#Abweichender Arbeitsplatz! Umbuchen?
				if T905AllowRoute == True:
					#abweichender Platz, umbuchen (umrouten)
					if RouteDialog == 0:
						#14.11.2022 - Meldungsausgaben im PKS
						#SBSTools.to020.G_MsgSuppress = MsgSuppress.NoSuppress
						#xMsgBox = to001_Msg.Msg(MsgType.mtError, Nothing, "MSG0136", "kt001 - Pruef_AgNr", "", "", MessageBoxButtons.YesNo, MessageBoxDefaultButton.Button1, xmld_S903)
						#if xMsgBox == MsgBoxResult.No:
							#xFehler = "MSG0137" #Auftrag wurde nicht erfaßt!
						print("RouteDialog=0 Auftrag nicht erfaßt")
				else:
					#'abweichender Platz, umbuchen nicht erlaubt
					#'23.06.2016
					if ShowMsgGeht == True:
						SBSTools.to020.G_MsgSuppress = MsgSuppress.NoSuppress
						xMsgBox = to001_Msg.Msg(MsgType.mtWarning, Nothing, "MSG0194", "kt001 - Pruef_AgNr", "", "", MessageBoxButtons.OK, MessageBoxDefaultButton.Button1, xmld_S903)
					else:
						SBSTools.to020.G_MsgSuppress = MsgSuppress.Auto #'von alleine wieder schließen
						xMsgBox = to001_Msg.Msg(MsgType.mtWarning, Nothing, "MSG0194", "kt001 - Pruef_AgNr", "", "", MessageBoxButtons.OK, MessageBoxDefaultButton.Button1, xmld_S903)
					
					xFehler = "MSG0137" #'Auftrag wurde nicht erfaßt!
					
 
		if len(xret) == 0:
			if kt002.CheckObject(kt002.dr_T905) == False:
				if kt002.CheckObject(kt002.dr_T951) == True:
					kt002.T905Read(kt002.gtv("T951_Arbist"))
			
			kt002.T905_NrSelected = kt002.gtv("T905_Nr") #14.11.2022
			xret = bufa(kt002.gtv("TA06_BelegNr"), ta29nr, xfaruecknr, '')
			return xret
		
	if len(xret) == 0:
		result = kt002.PNR_Buch(ASA, AKst, t905nr, ta29nr, APlatz, xtagid, xkstk)
		xret,ASA,AKst,APlatz,xtagid,xkstk=result
		print('pnrbuch' + xret + ' SA' + ASA + ' kstk:' + str(xkstk))
		
		if len(xret) == 0:
			if ASA == "K":
				if xkstk == 2:
					#'xplatz = PYTHON Auswahl Platz
					print ('Auswahl Platz')
					xplatz='0006'
			if ASA == "G":
				if showmsggeht == 1:
                      #'Eingabeaufforderung wollen Sie  wirklich gehen?
                      #MSG0133 wurde abgebrochen
					print ('Wollen Sie wirklich gehen msg0133')

				if gkendcheck == True: #Param aus X998 prüfen laufende Aufträge
					xret = kt002.PNR_Buch2Geht()
		
			if len(xret) == 0:
				kt002.PNR_Buch3(xtagid, ASA, AKst, APlatz, ta29nr, xfaruecknr, xmenge)
	return xret #actbuchung




#ByVal ABelegNr As String, ByVal AktAction As ktAction, ByVal AScreen2 As ApplModus, ByVal ATA29Nr As String _
#                          , ByVal AKst As String _
#                          , ByRef ASA As String, ByRef AFA As Integer
def ta06gk(ABelegNr,AktAction,AScreen2,ATA29Nr,AKst,ASA,AFA):
	xret =''
	xsalast=''
	xT905Last=''
	xTA29Last=''
	xBelegNr=''
	xKstLast=''
	xTSLast=''   
	xsalast=''   
	xkstlast=''
	xtslast=''
	xfarueckend=''

	#prüfen ob person anwesend ist und aktueller Arbeitsplatz
	result = kt002.CheckKommt(ASA, AKst, xsalast, xkstlast, xtslast, xT905Last, xTA29Last)
	xret,xsalast,xkstlast,ATSLast,xT905Last,xTA29Last=result   
	print('ta06g kcheckkommt:' + xret + ' salast:' + xsalast + ' kstlast:' + xkstlast + ' Tslast:' + ATSLast + ' xt905last:' + xT905Last + ' xTA29Last' + xTA29Last)
	print ('länge xret:' + str(len(xret)) + ' ABelegNr:' + ABelegNr)
	#DIALOG AUSWAHL GEMEINKOSTEN
	if len(xret) == 0:
		if len(ABelegNr) == 0:
			#HIER DIALOG AUFBAUEN
			#xBelegNr = DIALOG RÜCKGABE kt001_ShowTA06GK(xT905Last)
			print ('Dialog Auswahl Gemeinkosten')
			xBelegNr = 'GK0120350'
		else:
			xBelegNr = ABelegNr


	if len(xBelegNr) > 0:
		if kt002.TA06Read(xBelegNr) == True:
			if kt002.CheckObject(kt002.dr_T905) == False:
				kt002.T905Read(xT905Last) 
			
			xpersnr=kt002.T910NrGet()
			#Laufende Aufträge am anderen Arbeitsplatz beenden
			xret = endta51cancelt905(xpersnr)

			if len(xret) == 0:
				xret = bufa(xBelegNr, "", xfarueckend,'' )
	
	return xret #ta06gk


#yVal AScreen2 As Terminal.kt001.ApplModus'
def ta06gkend(AScreen2):
	xret = False
	
	xMsg = kt002.EndTA51GKCheck()
    #nix zu beenden
	if len(xMsg) == 0:
		if SBSTools.SysVar.G_KUNDENKN.ToUpper == 'ERGRO':
			ta06gk("", AScreen2, "", "", "", "") 
		else:
			xret = "MSG0179" #Es gibt keine Gemeinkostenaufträge zu beenden!

	return xret

	xret = True
    #Private GK-Aufträge beenden
	xSql = "exec ksmaster.dbo.kspr_TA51GKEnd2FB1 '" + SBSTools.to020.G_Comp.Nr + "'" 
	xSql = xSql + " ," + kt002.dr_T910("T910_Nr").ToString
		## exec sql
    #SBSTools.ks000.SQLDirect(xSql, "PNR_TA51GKEnd", Nothing)


	return xret #end ta06gkend

####### End Procedures/Functions

checkfa=False
aktscreen=1 #0-none,1-dgt001,2-dgt002,3-dgt800
bufunktion=6 #Buchungsfunktion
showhost=1 	 #Anzeige Hostinformation im Terminal
keycodecompende="" #Endezeichen Scanwert (manche Scanner liefern nach dem Wert noch zusätzliche Zeichen, die entfernt werden müssen)
scantype=0   #X998_SCANNER TS,CS,TP
scanon=1		#Scansimulation an (wenn über COM-Port gescannt wird, aber manuell ein scan simuliert werden soll)
scancardno=True
sa=""
activefkt="" #Funktionsbutton gedrückt,der ausgewählte Wert

result=""
appmscreen2=1 #X998_STARTSCREEN2
showmsggeht=1 #X998_ShowMsgGeht
gkendcheck=False #X998_GKEndCheck
btaetigkeit=False #X998_TAETIGKEIT - bei Arbeitsplatzauswahl, Tätigkeitsauswahl anschließen
ta29nr='' #Tätigkeit - bei Arbeitsplatzauswahl gesetzt und bleibt erhalten!
buaction=7 #ignore
msg=''
kst=''
t905nr='' #Arbeitsplatz
platz=''
farueckend=0 #Mengendialog Eingabe Menge oder automatisiert
ruecknr=''
menge=0
ta22dauer=0
buchfa=0 #Buchungsart 0=K/G, 1=FA-Buchung
tagid=''
kstk=0	#aus Personalstamm
ret=''
msgfkt=''
msgbuch=''
msgzeit=''
msgpers=''
salast=''
kstlast=''
tslast=''
platz=''
tl51use = False #Störungen mit buchen
T905AllowRoute=True
RouteDialog=0
MsgSuppress=1


def do_stuff(ascanvalue):
	checkfa = False
	aktscreen = 1  # 0-none,1-dgt001,2-dgt002,3-dgt800
	bufunktion = 0  # Buchungsfunktion
	showhost = 1  # Anzeige Hostinformation im Terminal
	keycodecompende = ""  # Endezeichen Scanwert (manche Scanner liefern nach dem Wert noch zusätzliche Zeichen, die entfernt werden müssen)
	scantype = 0  # X998_SCANNER TS,CS,TP
	scanon = 1  # Scansimulation an (wenn über COM-Port gescannt wird, aber manuell ein scan simuliert werden soll)
	scancardno = True
	sa = ""
	activefkt = ""  # Funktionsbutton gedrückt,der ausgewählte Wert

	result = ""
	appmscreen2 = 1  # X998_STARTSCREEN2
	showmsggeht = 1  # X998_ShowMsgGeht
	gkendcheck = False  # X998_GKEndCheck
	btaetigkeit = False  # X998_TAETIGKEIT - bei Arbeitsplatzauswahl, Tätigkeitsauswahl anschließen
	ta29nr = ''  # Tätigkeit - bei Arbeitsplatzauswahl gesetzt und bleibt erhalten!
	buaction = 7  # ignore
	msg = ''
	kst = ''
	t905nr = ''  # Arbeitsplatz
	platz = ''
	farueckend = 0  # Mengendialog Eingabe Menge oder automatisiert
	ruecknr = ''
	menge = 0
	ta22dauer = 0
	buchfa = 0  # Buchungsart 0=K/G, 1=FA-Buchung
	tagid = ''
	kstk = 0  # aus Personalstamm
	ret = ''
	msgfkt = ''
	msgbuch = ''
	msgzeit = ''
	msgpers = ''
	salast = ''
	kstlast = ''
	tslast = ''
	platz = ''
	tl51use = False  # Störungen mit buchen
	serial=True #14.11.2022
	msgdlg=""
	xmsg=""

	#Wechselbuchung einleiten
	#kt002.T905Read('F004')

	#Debugmode
	#BUCHFA = debug #0= K/G 1=FA Buchen 2=WB

	# scanvalue="1035" #gescannter Wert
	scanvalue=ascanvalue #gescannter Wert
	#person=1035 dbnull-fehler
	# scanvalue='GK0120350'


	print(f"SCANWERT= {ascanvalue}")
	#ShowNumber(ANumber As String, AActiveFkt1 As String, AktscanTyp As Integer, AShowHost As Boolean, AScanOn As Boolean, AKeyCodeCompEnde As String
	#, ByRef ACheckFA As Boolean, ByRef ASA As String) As String
	print(f"[DLL] ShowNumber scanvalue: {scanvalue},activefkt: {activefkt}, scantype: {scantype},showhost: {showhost},scanon: {scanon},keycodcompende: {keycodecompende}, checkfa: {checkfa}, sa: {sa}")
	result=kt002.ShowNumber(scanvalue,activefkt,scantype,showhost,scanon,keycodecompende,checkfa,sa)
	ret, checkfa, sa = result
	
	print(f"[DLL] ShowNumber ret: {ret}, checkfa: {checkfa}, sa: {sa}")

	n=result
	print(result)
	nr=scanvalue


	#Pruef_PNr(ByVal ACheckFA As Boolean, ByVal ANR As String, ByRef ASA As String, ByRef ABuFunction As Integer) As Boolean
	print ('Pruef_PNR')
	print(f"[DLL] PruefPNr checkfa: {checkfa},nr: {nr}, sa: {sa}, bufunktion: {bufunktion}")
	
	result = kt002.Pruef_PNr(checkfa, nr, sa, bufunktion)
	ret,sa,bufunktion=result
	print(f"[DLL] PruefPNr ret: {ret}, sa: {sa}, bufunktion: {bufunktion}")
	print('ret,sa,bufunktion')
	print(result)
	xpnr=kt002.gtv("T910_Nr")
	print(f"Nach Pruef_PNr:: Persnr: {xpnr}")

	#Ermitteln der Art der Aktion
	#Pruef_PNrFkt(ByVal ABuFunction As Integer,  ByVal AScanTyp As Integer, ByRef ASA As String
	#                , ByRef AktAction As Integer _
	#                , ByVal AppModScreen2 As Integer _
	#                , ByVal ASerial As Boolean, ByRef AActiveFkt1 As String, ByRef AMsg As String) As Boolean


	if ret == True:

	#Public Shared Function Pruef_PNrFkt(ByVal AScanValue As String, ByVal ABuFunction As Integer, ByVal AScanTyp As Integer, ByRef ASA As String _
	#           , ByRef AktAction As Integer _
	#            , ByVal AppModScreen2 As Integer _
	#            , ByVal ASerial As Boolean, ByRef AActiveFkt1 As String, ByRef AMsg As String, ByRef AMsgFkt As String, ByRef AMsgDlg As String) As Boolean

			print(f"Pruef_PNRFkt:: nr: {nr},bufunktion: {bufunktion},scantype: {scantype}, sa; {sa},buaction; {buaction},appmscreen2; {appmscreen2},serial: {serial},activefkt: {activefkt},msg: {msg},msgfkt: {msgfkt}, msgdlg: {msgdlg}")
			msgfkt=""
			msgdlg=""
			serial=True
			result = kt002.Pruef_PNrFkt(nr,bufunktion,scantype,sa,buaction, appmscreen2,serial,activefkt, msg,msgfkt,msgdlg)
			ret,sa,buaction,activefkt,msg,msgfkt,msgdlg=result
			print(f"Result:  ret: {ret},sa: {sa},buaction: {buaction}, activefkt: {activefkt}, msg: {msg}")
			

			#Buchung K/G oder FA (PersNr gescannt oder FA gescannt
			if buaction == 1:
				#if BUCHFA == 3:
					#sa=''
				result=actbuchung(ta29nr,kst,sa,t905nr,salast,kstlast,tslast,platz)

			#TA06GK - GK beginnen
			if buaction == 9:
				result  = ta06gk(belegnr, buaction, appmscreen2, ta29nr, xKst, xsa, xfa)

			#TA06END- GK beenden gedrück
			if buaction == 10:
				result = ta06gkend(appmscreen2)

			#ignore - keine Aktion ermittelt (verketteter Scan 1. FA-Nr, 2. anschließend Persnr
			if buaction == 7:
				if bufunktion == 3:
					if scancardno == True:
						xmsg = "MSG0147C" #Kartennummer scannen
					else:
						xmsg = "MSG0147" #Personalnummer scannen

			#GKBuchung
			#PNR_Buch4Clear(ByVal ADlgPos As Integer, ByVal AScanValue As String, ByVal ASA As String, ByVal AT905Nr As String, ByRef AktAction As Integer _
			#                                          , ByVal AGKEnd As Boolean, ByRef AActiveFkt1 As String _
			#                                          , ByRef AMsgFkt As String, ByRef AMsgBuch As String, ByRef AMsgZeit As String, ByRef AMsgPers As String) As Boolean

			print(f"do_stuff:: xmsg: {xmsg}")
			if len(xmsg) == 0:
				print("Clear Data")
				result = kt002.PNR_Buch4Clear(1,nr, sa, platz, buaction, gkendcheck, activefkt, msgfkt, msgbuch, msgzeit, msgpers)
			


import time

#do_stuff(ascanvalue="1035")  # Kommen
#print("------------------------------------------------------")
#time.sleep(3)
#do_stuff(ascanvalue="GK0080150")  # GK anfangen
#print("------------------------------------------------------")
#time.sleep(3)
#do_stuff(ascanvalue="1035")  # GK buchen
#print("------------------------------------------------------")
time.sleep(3)
do_stuff(ascanvalue="FA00300150")  # FA Buchen auf 0006  funktion: fabuchta55
print("------------------------------------------------------")
time.sleep(3)
do_stuff(ascanvalue="1035")  #  buchen
print("------------------------------------------------------")
time.sleep(3)
#do_stuff(debug=0)  # Gehen

