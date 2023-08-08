import os
import sys
import clr
import System
import time

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

# dll_ref1 = System.Reflection.Assembly.LoadFile("C:\\Users\\MSSQL\\PycharmProjects\\suwelack\\dll\\bin\\kt002_PersNr.dll")
#dll_ref2 = System.Reflection.Assembly.LoadFile("C:\\Users\\MSSQL\\PycharmProjects\\suwelack\\dll\\bin\\kt002_PersNr_2.dll")
# type1 = dll_ref1.GetType('kt002_persnr.kt002')
#type2 = dll_ref2.GetType('kt002_persnr.kt002')
# instance1 = System.Activator.CreateInstance(type1)
#instance2 = System.Activator.CreateInstance(type2)

# from kt002_persnr import kt002 as kt002_1
# from kt002_persnr import kt002 as kt002_2

# os.chdir("dll/bin")

# kt002_1.Init()
# kt002_1.InitTermConfig()
# kt002_2.Init()
# kt002_2.InitTermConfig()

# instance1.Init()
# instance1.InitTermConfig()
#instance2.Init()
#instance2.InitTermConfig()

#res1 = instance1.ShowNumber("1024",activefkt,SCANTYPE,SHOWHOST,SCANON,KEYCODECOMPENDE,checkfa,sa)
#res2 = instance2.ShowNumber("1035",activefkt,SCANTYPE,SHOWHOST,SCANON,KEYCODECOMPENDE,checkfa,sa)
#ret1, checkfa1, sa1 = res1
#ret2, checkfa2, sa2 = res2

# result = instance1.PNR_Buch("G", '', "M001", '', '', '', 0)

#res1 = instance1.Pruef_PNr(False, "1024", "G", bufunktion)
# print(instance1.gtv("T910_Nr"))
#res2 = instance2.Pruef_PNr(checkfa2, "1035", sa2, bufunktion)
#print(instance2.gtv("T910_Nr"))
# ret1, sa1, bufunktion1 = res1
#ret2, sa2, bufunktion2 = res2

# print(instance1.gtv("T910_Nr"))
#print(instance2.gtv("T910_Nr"))
# print("")

# for i in range(1000):
#     start = time.time()
#     dll_ref1 = System.Reflection.Assembly.LoadFile("C:\\Users\\MSSQL\\PycharmProjects\\suwelack\\dll\\bin\\kt002_PersNr.dll")
#     type1 = dll_ref1.GetType('kt002_persnr.kt002')
#     instance1 = System.Activator.CreateInstance(type1)
#     instance1.Init()
#     instance1.InitTermConfig()
#     end = time.time()
#     print(f"iteration: {i}, time: {end-start}")


import subprocess
import time


def convert_dtype(args, dtypes):
    out = []
    for arg, dtype in zip(args, dtypes):
        if dtype == "bool":
            if arg == "True":
                out.append(True)
            else:
                out.append(False)
        else:
            out.append(eval(dtype)(arg))
    return out

def decode(line):
    command, args, dtypes = line.strip().split("█")
    if len(args) == 0:  # no return
        return None, None, None
    args = args.split("▌")
    dtypes = dtypes.split("▌")
    args = convert_dtype(args, dtypes)
    return command, args, dtypes

def encode(msg):
    if msg is None:
        return f"█\n"
    else:
        dtypes = [type(x).__name__ for x in msg]
        return f"{'▌'.join(map(str, msg))}█{'▌'.join(dtypes)}\n"

def start_dll_process(python_path):
    process = subprocess.Popen([python_path, "test_other.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=False)
    return process

def communicate(process, command, *args):
    data = f"{command}█{encode(args)}\n"
    process.stdin.write(data.encode())
    process.stdin.flush()
    
    decoded = process.stdout.readline().decode()
    command, args, dtypes = decode(decoded)
    
    if len(args) > 1:
        return args
    elif len(args) == 1:
        return args[0]
    else:
        return None


for i in range(100):
    start = time.time()
    dll_process = start_dll_process('C:\\Users\\MSSQL\\PycharmProjects\\DLLTest\\venv\\Scripts\\python')

    args = ["1024",activefkt,SCANTYPE,SHOWHOST,SCANON,KEYCODECOMPENDE,checkfa,sa]
    result1 = communicate(dll_process, "ShowNumber", *args)
    print(result1)
    
    args = ["1024",activefkt,SCANTYPE,SHOWHOST,SCANON,KEYCODECOMPENDE,checkfa,sa]
    result2 = communicate(dll_process, "ShowNumber", *args)
    print(result2)
    
    args = [False, "1024", "G", bufunktion]
    result3 = communicate(dll_process, "Pruef_PNr", *args)
    print(result3)
    
    args = ["dr_TA05"]
    result3 = communicate(dll_process, "attribute", *args)
    print(result3)

    dll_process.terminate()
    end = time.time()
    print(f"iteration: {i}, time: {end-start}")
    print("------------------------------------")
