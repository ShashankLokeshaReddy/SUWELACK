import sys
import clr
import os
import time
print(os.getcwd())
sys.path.append(os.getcwd())

import dbconnection

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


sys.path.append("dll/bin")
#sys.path.append("c:\temp\testpks")
clr.AddReference("kt002_PersNr") 
clr.AddReference("System.Collections")

from System.Collections import Generic
#from System import *
from System.Collections import Hashtable
from System import String
from System import Object

os.chdir("dll/bin")
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
		msgr= "ok"
		if msgr == "ok":
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

	result = kt002.BuchTA55_0(xInputMenge, xInputMengeNew, xFARueckEnd, xScanFA, xFAStatus, xFATS, xFAEndeTS, xFAMeGut, xFAMeGes, xFANewScanFA, xFANewStatus, xFANewMeGes, xFANewMe)
	xret,xInputMenge, xInputMengeNew,xScanFA, xFAStatus, xFATS, xFAEndeTS, xFAMeGut, xFAMeGes, xFANewScanFA, xFANewStatus, xFANewMeGes, xFANewMe=result
	#print("kt002.BuchTA55_0:" + xret + "," + str(xInputMenge) + "," +  str(xInputMengeNew)  + "," + str(xScanFA) + "," +  xFAStatus+ "," +  xFATS + "," +  xFAEndeTS + "," +  str(xFAMeGut+ "," +  str(xFAMeGes) + "," + str(xFANewScanFA) + "," +  xFANewStatus + "," +  str(xFANewMeGes) + "," +  str(xFANewMe))
	print(f"BuchTA55_0: {result}")
	if len(xret) > 0:
		xbuchen=False

	if xInputMenge == 1:
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


def fabuchta51(ata22dauer, aAnfangTS=None, aEndeTS=None, aBem=None):

	xStatusMenge = ""
	# xTSLast = datetime.now()

	# if given, set begin and end according to parameter, else assume begin = end = now
	if aAnfangTS is None and aEndeTS is None:
		xEndeTS = datetime.now()
		xAnfangTS = xEndeTS
	else:
		xAnfangTS = datetime.strptime(aAnfangTS, "%d.%m.%Y %H:%M:%S")
		xEndeTS = datetime.strptime(aEndeTS, "%d.%m.%Y %H:%M:%S")
	xTS=xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")  #Stringtransporter Datum    
	xTSEnd=xEndeTS.strftime("%d.%m.%Y %H:%M:%S")

	print(f"[DLL] fabuchta51 xTS: {xTS}, xTSEnd: {xTSEnd}")

	#Dim xbFound As Boolean = True
	xTRMan = 0.0
	xTA11Nr = ""
	xCharge = ""
	# xDauer = 0 
	xVal1 = 0.0
	xVal2 = 0.0
	xVal3 = 0.0
	xVal4 = 0.0
	xVal5 = 0.0
	xbCancel=False

	xTA22Dauer = kt002.gtv("TA22_Dauer") #aus TA06 gelesen
	if ata22dauer.isnumeric() == True:    # von außen übersteuern
		xTA22Dauer = int(ata22dauer)
	
	print(f"[DLL] Pre BuchTA51_0 xTA22Dauer: {xTA22Dauer}, xTS: {xTS}, xStatusMenge: {xStatusMenge}")
	result = kt002.BuchTA51_0(xTA22Dauer, xTS, xStatusMenge)
	xret, xTS, xStatusMenge = result
	print(f"[DLL] BuchTA51_0 xret: {xret}, xTS: {xTS}, xStatusMenge: {xStatusMenge}")

	if not aAnfangTS is None and not aEndeTS is None:  # when booking with given Dauer
		xStatusMenge = "20"  # TODO: bug in DLL, temporarily overwrite, 20 means just book, don't validate further

	xAnfangTS = datetime.strptime(xTS,dtformat)
	print("xTS:" + xTS + " Datum:" + xAnfangTS.strftime("%d.%m.%Y %H:%M:%S"))
	if len(xret) > 0:
		print("nur laufenden beendet. -Inhalt Message")
		return xret  #nur laufenden beendet. -Inhalt Message
	
	# Below only for a specific customer
	# print("xTA22Dauer:" + str(xTA22Dauer))
	# if xTA22Dauer == 3:
	#     #HIER DIALOG dgt11 Gemeinkosten Buchungsdaten ändern
	#     #xDauer = PNR_TA51GKEndDauer(xTSLast, kt002.dr_TA06("TA06_FA_Nr"), kt002.dr_TA06("TA06_BelegNr"), kt002.dr_TA06("TA06_AgBez"))
	# 	if xDauer > 0:
	# 		xAnfangTS = xEndeTS.AddMinutes(xDauer * -1)
	# 		xAnfangTS = xAnfangTS.AddSeconds(-1) #1 sekunde wird wieder draufgerechnet!
	# 	else:
	# 		xbCancel = True
	# 		xret = "MSG0133"

	#14.06.2013 - auf Ende buchen und Mengenabfrage
	if xbCancel == False:
		xta22typ=kt002.gtv("TA22_Typ")
		print("xta22typ:" + xta22typ)
		if kt002.gtv("TA22_Typ")  == "7":
			xDialog=True
			if xDialog == True:
				xTSEnd = xEndeTS.strftime("%d.%m.%Y %H:%M:%S")
				xTS = xAnfangTS.strftime("%d.%m.%Y %H:%M:%S") 
				print("BuchTA51_3:")
				print(xTSEnd, int(kt002.gtv("T910_Nr")), kt002.gtv("TA06_FA_Nr"), kt002.gtv("TA06_BelegNr"),xStatusMenge,kt002.gtv("T910_Entlohnung"),kt002.gtv("T905_Nr"),kt002.gtv("TA06_TE"),kt002.gtv("TA06_TR"),0.0,xmegut,0.0,xTRMan, xTA11Nr, xCharge,xVal1,xVal2,xVal3,xVal4,xVal5,kt002.gtv("TA06_FA_Art"),xTS)
				kt002.BuchTA51_3( xTSEnd, kt002.gtv("T910_Nr"), kt002.gtv("TA06_FA_Nr"), kt002.gtv("TA06_BelegNr"), xStatusMenge, kt002.gtv("T910_Entlohnung")
				,kt002.gtv("T905_Nr"), kt002.gtv("TA06_TE"), kt002.gtv("TA06_TR"), 0, xMengeGut, xMengeAus, xTRMan, xTA11Nr, xCharge, xVal1, xVal2, xVal3, xVal4, xVal5, kt002.gtv("TA06_FA_Art"), xTS)
				
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
				if aAnfangTS is None and aEndeTS is None:
					# if not booking with Dauer, add a second for safety (?)
					xAnfangTS = xAnfangTS + timedelta(seconds = 1) #xAnfangTS.AddSeconds(1)
				xTS=xAnfangTS.strftime("%d.%m.%Y %H:%M:%S")
				
				xcl = Generic.Dictionary[String,Object]() #leere liste
				xdmegut=kt002.gtv("TA06_Soll_Me")
				xsmegut=str(xdmegut)
				xmegut=float(xsmegut.replace(",","."))
				
				print("BuchTA51_3:")
				print(xTSEnd, int(kt002.gtv("T910_Nr")), kt002.gtv("TA06_FA_Nr"), kt002.gtv("TA06_BelegNr"),xStatusMenge,kt002.gtv("T910_Entlohnung"),kt002.gtv("T905_Nr"),kt002.gtv("TA06_TE"),kt002.gtv("TA06_TR"),0.0,xmegut,0.0,xTRMan, xTA11Nr, xCharge,xVal1,xVal2,xVal3,xVal4,xVal5,kt002.gtv("TA06_FA_Art"),xTS)
				xret = kt002.BuchTA51_3(xTSEnd, int(kt002.gtv("T910_Nr")), kt002.gtv("TA06_FA_Nr"), kt002.gtv("TA06_BelegNr"),xStatusMenge,kt002.gtv("T910_Entlohnung"),kt002.gtv("T905_Nr"),kt002.gtv("TA06_TE"),kt002.gtv("TA06_TR"),0.0,xmegut,0.0,xTRMan, xTA11Nr, xCharge,xVal1,xVal2,xVal3,xVal4,xVal5,kt002.gtv("TA06_FA_Art"),xTS)
			#EvtMsgDisplay("FA Buchen", "MSG0166", kt002.dr_TA06("TA06_BelegNr"), kt002.dr_TA06("TA06_AgBez"))
			xret = "FA Buchen;MSG0166" + ";" + kt002.dr_TA06.get_Item("TA06_BelegNr") + ";" + kt002.dr_TA06.get_Item("TA06_AgBez")

	return xret #fabuchta51


def bufa(ANr, ATA29Nr, AFARueckend, ata22dauer, aAnfangTS=None, aEndeTS=None):
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
				xFehler = fabuchta51(ata22dauer, aAnfangTS=aAnfangTS, aEndeTS=aEndeTS)
				print("xFehler shashank",xFehler)
	else:
		xFehler = "Kein Auftrag!"
		if kt002.CheckObject(kt002.dr_TA06) == True and kt002.CheckObject(kt002.dr_TA05)== False:
			xFehler = "Keine Kopfdaten vorhanden!"

	return xFehler #bufa



def actbuchung(ta29nr,AKst,ASA,t905nr,ASALast,AKstLast,ATSLast,APlatz,AAnfangTS=None,AEndeTS=None):

	xT905Last =''
	xTA29Last =''
	xtagid=''
	xkstk=0
	xfaruecknr=''
	xmenge=0
	
	print("actbuchung SA:" + ASA)
	result = kt002.CheckKommt(ASA, AKst, ASALast, AKstLast, ATSLast, xT905Last, xTA29Last)
	xret,ASALast,AKstLast,ATSLast,xT905Last,xTA29Last=result
	print("checkkommt shashank")
	print(xret,ASALast,AKstLast,ATSLast,xT905Last,xTA29Last)
	print(result)
	if len(xret) > 0:
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
				#Abweichender Arbeitsplatz! Umbuchen? || Differing workstation! book to another workstation?
				if T905AllowRoute == True:
					#abweichender Platz, umbuchen (umrouten) || Differing workstation, book to another workstation
					if RouteDialog == 0:
						#14.11.2022 - Meldungsausgaben im PKS
						#SBSTools.to020.G_MsgSuppress = MsgSuppress.NoSuppress
						#xMsgBox = to001_Msg.Msg(MsgType.mtError, Nothing, "MSG0136", "kt001 - Pruef_AgNr", "", "", MessageBoxButtons.YesNo, MessageBoxDefaultButton.Button1, xmld_S903)
						#if xMsgBox == MsgBoxResult.No:
							#xFehler = "MSG0137" #Auftrag wurde nicht erfaßt!
						print("RouteDialog=0 Auftrag nicht erfaßt")
				else:
					#'abweichender Platz, umbuchen nicht erlaubt || Differing workstation, booking to another workstation not allowed
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
			xret = bufa(kt002.gtv("TA06_BelegNr"), ta29nr, xfaruecknr, '', aAnfangTS=AAnfangTS, aEndeTS=AEndeTS)
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


#yVal AScreen2 As Terminal.kt001.ApplModus'
def ta06gkend(AScreen2):
	
	xMsg = kt002.EndTA51GKCheck()
	if len(xMsg) == 0:
		return "MSG0179"  # Es gibt keine Gemeinkostenaufträge zu beenden!  || nothing to terminate
	else:
		# execute this stored procedure like the other ones in dbconnection.py, replace default values
		FirmaNr = 'TE'
		PersNr = 99999
		xSql = f"exec ksmaster.dbo.kspr_TA51GKEnd2FB1 '{FirmaNr}', {PersNr}" 
		return True

####### End Procedures/Functions

# default values added as constants for testing
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


def do_stuff(scanvalue, anfang_ts=None, ende_ts=None):
	
	# default values added as constants for testing
	checkfa = False
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
	ta29nr = ''  # Tätigkeit - bei Arbeitsplatzauswahl gesetzt und bleibt erhalten!
	buaction = 7  # ignore
	msg = ''
	kst = ''
	t905nr = ''  # Arbeitsplatz
	platz = ''
	ret = ''
	msgfkt = ''
	msgbuch = ''
	msgzeit = ''
	msgpers = ''
	salast = ''
	kstlast = ''
	tslast = ''
	platz = ''
	serial=True #14.11.2022
	msgdlg=""
	xmsg=""

	#Wechselbuchung einleiten
	#kt002.T905Read('F004')

	print(f"SCANWERT= {scanvalue}")
	print(f"[DLL] Pre ShowNumber scanvalue: {scanvalue},activefkt: {activefkt}, scantype: {scantype},showhost: {showhost},scanon: {scanon},keycodcompende: {keycodecompende}, checkfa: {checkfa}, sa: {sa}")
	result=kt002.ShowNumber(scanvalue,activefkt,scantype,showhost,scanon,keycodecompende,checkfa,sa)
	ret, checkfa, sa = result
	print(f"[DLL] ShowNumber ret: {ret}, checkfa: {checkfa}, sa: {sa}")

	nr = scanvalue


	print(f"[DLL] Pre PruefPNr checkfa: {checkfa}, nr: {nr}, sa: {sa}, bufunktion: {bufunktion}")
	result = kt002.Pruef_PNr(checkfa, nr, sa, bufunktion)
	ret,sa,bufunktion=result
	print(f"[DLL] PruefPNr ret: {ret}, sa: {sa}, bufunktion: {bufunktion}")

	xpnr=kt002.gtv("T910_Nr")
	print(f"[DLL] Nach Pruef_PNr Persnr: {xpnr}")


	if ret == True:
			msgfkt=""
			msgdlg=""
			serial=True

			print(f"[DLL] Pre Pruef_PNRFkt nr: {nr}, bufunktion: {bufunktion}, scantype: {scantype}, sa: {sa}, buaction: {buaction}, appmscreen2: {appmscreen2}, serial: {serial}, activefkt: {activefkt},msg: {msg}, msgfkt: {msgfkt}, msgdlg: {msgdlg}")
			result = kt002.Pruef_PNrFkt(nr, bufunktion, scantype, sa, buaction, appmscreen2, serial, activefkt, msg, msgfkt, msgdlg)
			ret,sa,buaction,activefkt,msg,msgfkt,msgdlg=result
			print(f"Result:  ret: {ret},sa: {sa},buaction: {buaction}, activefkt: {activefkt}, msg: {msg}")
			

			#Buchung K/G oder FA (PersNr gescannt oder FA gescannt
			if buaction == 1:
				#if BUCHFA == 3:
					#sa=''
				result=actbuchung(ta29nr,kst,sa,t905nr,salast,kstlast,tslast,platz,AAnfangTS=anfang_ts,AEndeTS=ende_ts)  # propagate anfang and ende when booking with Dauer

			#TA06END- GK beenden gedrückt
			if buaction == 10:
				result = ta06gkend(appmscreen2)

			# ignore - keine Aktion ermittelt (verketteter Scan 1. FA-Nr, 2. anschließend Persnr)
			# ignore - action could not be resolved (this is the first of two calls for FA/GK buchen, next will be with userid/PersNr)
			if buaction == 7:
				if bufunktion == 3:
					if scancardno == True:
						xmsg = "MSG0147C" #Kartennummer scannen
					else:
						xmsg = "MSG0147" #Personalnummer scannen

			print(f"[DLL] do_stuff xmsg: {xmsg}")
			if len(xmsg) == 0:
				print("Buch4Clear")
				print(1, nr, sa, platz, buaction, gkendcheck, activefkt, msgfkt, msgbuch, msgzeit, msgpers)
				result = kt002.PNR_Buch4Clear(1, nr, sa, platz, buaction, gkendcheck, activefkt, msgfkt, msgbuch, msgzeit, msgpers)
				print("")
			

def gk_ändern(fa_old, userid, anfang_ts, dauer):
	# Change existing Auftragsbuchung, TODO: somehow return error when no GK to delete is found
	ret = dbconnection.doGKLoeschen(fa_old, userid, anfang_ts)  # delete old booking with BelegNr=scanvalue and Anfang=Anfangts
	if dauer > 0:
		# add back booking with correct dauer
		anfang_ts, ende_ts = dbconnection.doFindTS(userid, dauer)  # find suitable begin and end for new Auftrag
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
	anfang_ts, ende_ts = dbconnection.doFindTS(userid, dauer)
	if anfang_ts is None and ende_ts is None:
		return "Keine neue Zeitperiode gefunden!"
	else:
		return anfang_ts, ende_ts


# examples for bookings, the currently uncommented code assumes that userid=1024 is signed in and that a GK Auftrag begins exactly at anfang_ts and has the stated BelegNr (fa_old)
# it will change the booking to the defined Dauer, in this case 10 minutes
# you can check your bookins in Microsoft SQL Studio, load file "DLL_QUERY_CHECK.sql" and run ("Ausführen")
# top table is Kommen/Gehen/Wechsel, middle is GK and bottom is FA
# you can safely reset the last bookings by setting @xclear=1
# but be careful with removing Kommen! A time window might be found that is after the deleted and before the new Kommen Buchung, in that case a new booking won't show up!
#  -> to resolve it, manually set a time window after the new Kommen booking

# do_stuff(scanvalue="1024")  # Kommen/Gehen
# print("------------------------------------------------------")
# time.sleep(3)  # add sleep so DLL has time to book in background before starting next queries
# do_stuff(scanvalue="GK0080150")  # GK anfangen
# print("------------------------------------------------------")
# time.sleep(3)
# do_stuff(scanvalue="1024")  # buchen
# # anfang_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")  # in real application, get anfang timestamp from booking to change from table, make sure to use T notation
# print("------------------------------------------------------")
# time.sleep(3)
# do_stuff(scanvalue="GK0080150")  # GK beenden
# print("------------------------------------------------------")
# time.sleep(3)
# do_stuff(scanvalue="1024")  # buchen
# print("------------------------------------------------------")
# time.sleep(3)
# find out timewindow for changed booking with Dauer, provide exact begin timestamp of Auftrag that has to be changed
anfang_ts = "2023-01-31T22:03:58"  # in real application, get anfang timestamp from booking to change from table, make sure to use T notation
ret = gk_ändern(fa_old="GKP0011550", userid="1025", anfang_ts=anfang_ts, dauer=10)
if isinstance(ret, str):
	# display error string and cancel booking
	print(ret)
else:
	anfang_ts, ende_ts = ret
	print(f"[DLL] anfang_ts: {anfang_ts}, ende_ts: {ende_ts}")
time.sleep(3)
ret = do_stuff(scanvalue="GKP0011550")  # GK ändern booking, this is the new GK BelegNr
print("------------------------------------------------------")
time.sleep(3)
do_stuff(scanvalue="1025", anfang_ts=anfang_ts, ende_ts=ende_ts)  # buchen

# print("------------------------------------------------------")
#time.sleep(3)
# do_stuff(scanvalue="FA00300150")  # FA Buchen auf 0006  funktion: fabuchta55
# print("------------------------------------------------------")
# time.sleep(3)
# do_stuff(scanvalue="1035")  #  buchen

# Pseudocode for Gruppenbuchung
# Belegnr = ...  # from dialogue
# GruppeNr = ...  # from dialogue
# TagId = ...  # from dialogue
# person_list = dbconnection.getGroupMembers(GruppeNr, TagId)  # get all persons from this group
# for person in person_list:
# 	ret = kt002.TA06Read(Belegnr)  # preset the BelegNr in the DLL
# 	if ret == False:  # if BelegNr not found, i'm not quite sure what the TA06Read returns in that case
# 		kt002.TA06ReadPlatz(Belegnr, Platz)  # specify Platz (depends on last booking of person)
# 	ret = gk_erstellen(userid, dauer)  # find time window
	# if not isinstance(ret, str):
	# 	anfang_ts, ende_ts = ret
# 		# no error when finding time window
# 		do_stuff(FA_Nr)  # GK erstellen
# 		do_stuff(scanvalue=userid, anfang_ts=anfang_ts, ende_ts=ende_ts)  # book

# For Arbeitsplatzbuchung also just booking with Dauer, may need to propagate the Arbeitsplatz down further from the outside
