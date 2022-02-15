import sys
import clr



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
        

checkfa=False
aktscreen=1 #0-none,1-dgt001,2-dgt002,3-dgt800
bufunktion=6 #Buchungsfunktion
showhost=1 	 #Anzeige Hostinformation im Terminal   
keycodecompende="" #Endezeichen Scanwert (manche Scanner liefern nach dem Wert noch zusätzliche Zeichen, die entfernt werden müssen)
scantype=0   #X998_SCANNER TS,CS,TP
scanon=1		#Scansimulation an (wenn über COM-Port gescannt wird, aber manuell ein scan simuliert werden soll)
sa=""
activefkt="" #Funktionsbutton gedrückt,der ausgewählte Wert
scanvalue="1024" #gescannter Wert
result=""
appmscreen2=1 #X998_STARTSCREEN2
showmsggeht=1 #X998_ShowMsgGeht 
gkendcheck=True #X998_GKEndCheck
btaetigkeit=False #X998_TAETIGKEIT - bei Arbeitsplatzauswahl, Tätigkeitsauswahl anschließen
ta29nr='' #Tätigkeit
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


#sys.path.append("c:\temp\testpks")
clr.AddReference("kt002_PersNr")
from kt002_persnr import kt002
kt002.Init()   
kt002.InitTermConfig()

#ShowNumber(ANumber As String, AActiveFkt1 As String, AktscanTyp As Integer, AShowHost As Boolean, AScanOn As Boolean, AKeyCodeCompEnde As String
#, ByRef ACheckFA As Boolean, ByRef ASA As String, ByRef ABuFunction As Integer) As String
print('ShowNumber')
result=kt002.ShowNumber(scanvalue,activefkt,scantype,showhost,scanon,keycodecompende,checkfa,sa,bufunktion)
#('1024',True,'',6) 'Checkfa
print(result)
nr="1024"
checkfa=True
sa=''
bufunktion=6
#Pruef_PNr(ByVal ACheckFA As Boolean, ByVal ANR As String, ByRef ASA As String, ByRef ABuFunction As Integer) As Boolean
print ('Pruef_PNR')
result = kt002.Pruef_PNr(checkfa, nr, sa, bufunktion) 
print(result)
#(True,'',0) Persnr gefunden,sa,bufu
bufunktion=0



#Ermitteln der Art der Aktion
#Pruef_PNrFkt(ByVal ABuFunction As Integer,  ByVal AScanTyp As Integer, ByRef ASA As String 
#                , ByRef AktAction As Integer _                                                                  
#                , ByVal AppModScreen2 As Integer _                                                              
#                , ByVal ASerial As Boolean, ByRef AActiveFkt1 As String, ByRef AMsg As String) As Boolean       

print (bufunktion,':',scantype,':',sa,':',buaction, ':',appmscreen2, ':',scanon,':',activefkt,':', msg)   
print('Pruef_PNrFkt')
result = kt002.Pruef_PNrFkt(bufunktion,scantype,sa,buaction, appmscreen2, scanon,activefkt, msg)
#(True,'K',1,'','')
print(result)  
sa='K'
buaction=1

if buaction == 1:
	#Ermitteln Buchung, ob Auftrag gescannt wurde oder nur Personalnr.
	#wenn vorher FA gescannt wurde existiert im Speicher der FA-Datensatz
	#BuAkt_Buchung(ByRef ASa As String, ByRef AT905Nr As String _                                                                                                              
	#              , ByVal AScreen2 As Integer, ByVal ATA29Nr As String, ByRef AktAction As Integer, ByVal AFARueckEnd As Boolean, ByRef ATA22Dauer As Object _kt002.BuAkt_Buchung(xsa, xt905nr, ascreen2, ata29nr, xktAction, xfarueckend, xta22dauer, xfa)
	#             , ByRef AFA As Integer) As String  
	print('BuAkt_Buchung')                                                                                                         
	result = kt002.BuAkt_Buchung(sa,t905nr, appmscreen2,ta29nr, buaction,farueckend,ta22dauer,buchfa)
	('','K','',1,0,0)
	ret=''
	print(result)
	#print (kt002.dr_T910('T910_Name')) - Test Abfrage geht nicht
	
	if len(ret)==0:
		#PNR_Buch(ByRef ASa As String, ByRef AKst As String, ByVal AT905Nr As String, ByVal ATA29Nr As String, ByRef APlatz As String _
		#         , ByRef ATagid As Date, ByRef AKstK As Integer) As String         
		print ('PNR_Buch')                   
		result= kt002.PNR_Buch(sa, kst, t905nr, ta29nr, platz, tagid, kstk)   
		#('','K','1012','G012','28.01.2022',2022') 
		print (result)
		ret=''
		kst='1012'
		platz='G012'
		tagid ='28.01.2022'
		kstk=2
		#sa='G'
	
		if len(ret) ==0:
			###EINGABE ARBEITSPLATZ
			if sa == 'K':
				if kstk == 2: 
					print ('EINGABE PLATZ')
				
			if sa == 'G':
				if showmsggeht == 1:
					print ('DIALOG wollen Sie wirklich gehen?')
					ret = '' #Ergebnis vom Dialog (Inhalt = Abbruch)
				if len(ret) == 0:
					if gkendcheck == True: #prüfen vorangegangener gkendcheck
						result = kt002.PNR_Buch2Geht() #dummy routine noch nicht realisiert
						ret =''
			
			if len(ret) == 0:
				#PNR_Buch3(ByVal ATagId As string, ByVal ASatzArt As String, ByVal AKst As String _
				#                        , ByVal APlatz As String, ByVal ATA29Nr As String, ByVal ARueckNr As String, ByVal AMengeIst As Double) As String
				print ('PNR_Buch3')
				result = kt002.PNR_Buch3(tagid, sa, kst, platz, ta29nr, ruecknr, menge)
				print (result)
#PNR_Buch4Clear(ByVal ADlgPos As Integer, ByVal AScanValue As String, ByVal ASA As String, ByVal AT905Nr As String, ByRef AktAction As Integer _
#                                          , ByVal AGKEnd As Boolean, ByRef AActiveFkt1 As String _
#                                          , ByRef AMsgFkt As String, ByRef AMsgBuch As String, ByRef AMsgZeit As String, ByRef AMsgPers As String) As Boolean
result = kt002.PNR_Buch4Clear(1,nr, sa, platz, buaction, gkendcheck, activefkt, msgfkt, msgbuch, msgzeit, msgpers)
print (result)
 