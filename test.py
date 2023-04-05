import os
import sys
import clr
import System

DTFORMAT = "%d.%m.%Y %H:%M:%S"
DFORMAT = "%d.%m.%Y"
APPMSCREEN2 = True  # bool(int(root.findall('X998_StartScreen2')[0].text)) # X998_STARTSCREEN2
SHOWMSGGEHT = True
GKENDCHECK = True
BTAETIGKEIT = True
SCANTYPE = 0  # root.findall('X998_SCANNER')[0].text # X998_SCANNER TS,CS,TP
SCANON = 1  # Scansimulation an
KEYCODECOMPENDE = ""  # Endzeichen Scanwert
SHOWHOST = 1  # Anzeige Hostinformation im Terminal
SERIAL = True
SCANCARDNO = True
T905ALLOWROUTE = True
ROUTEDIALOG = True
SHOW_BUTTON_IDS = False  # If true, show Arbeitsplatz and GK IDs after their name for debugging
activefkt = ""
buaction = 7
bufunktion = 0
checkfa = False
sa = ""

sys.path.append("dll/bin")
clr.AddReference("kt002_PersNr")
# clr.AddReference("kt002_PersNr_2")

print(os.getcwd())

dll_ref1 = System.Reflection.Assembly.LoadFile("C:\\Users\\MSSQL\\PycharmProjects\\suwelack\\dll\\bin\\kt002_PersNr.dll")
dll_ref2 = System.Reflection.Assembly.LoadFile("C:\\Users\\MSSQL\\PycharmProjects\\suwelack\\dll\\bin\\kt002_PersNr_2.dll")
type1 = dll_ref1.GetType('kt002_persnr.kt002')
type2 = dll_ref2.GetType('kt002_persnr.kt002')
instance1 = System.Activator.CreateInstance(type1)
instance2 = System.Activator.CreateInstance(type2)

# from kt002_persnr import kt002 as kt002_1
# from kt002_persnr import kt002 as kt002_2

os.chdir("dll/bin")

# kt002_1.Init()
# kt002_1.InitTermConfig()
# kt002_2.Init()
# kt002_2.InitTermConfig()

instance1.Init()
instance1.InitTermConfig()
instance2.Init()
instance2.InitTermConfig()

res1 = instance1.ShowNumber("1024",activefkt,SCANTYPE,SHOWHOST,SCANON,KEYCODECOMPENDE,checkfa,sa)
res2 = instance2.ShowNumber("1035",activefkt,SCANTYPE,SHOWHOST,SCANON,KEYCODECOMPENDE,checkfa,sa)
ret1, checkfa1, sa1 = res1
ret2, checkfa2, sa2 = res2

res1 = instance1.Pruef_PNr(checkfa1, "1024", sa1, bufunktion)
print(instance1.gtv("T910_Nr"))
res2 = instance2.Pruef_PNr(checkfa2, "1035", sa2, bufunktion)
print(instance2.gtv("T910_Nr"))
ret1, sa1, bufunktion1 = res1
ret2, sa2, bufunktion2 = res2

print(instance1.gtv("T910_Nr"))
print(instance2.gtv("T910_Nr"))
print("")
