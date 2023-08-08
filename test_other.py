import os
import sys
import clr
import System
import time


sys.path.append("dll/bin")
clr.AddReference("kt002_PersNr")
os.chdir("dll/bin")
dll_ref = System.Reflection.Assembly.LoadFile(os.path.abspath(os.path.dirname(__file__)) + "\\dll\\bin\\kt002_PersNr.dll")
type = dll_ref.GetType('kt002_persnr.kt002')
instance = System.Activator.CreateInstance(type)
instance.Init()
instance.InitTermConfig()

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

def returns(res):
    msg = f"_█{encode(res)}"
    sys.stdout.write(msg)
    sys.stdout.flush()

for line in sys.stdin:
    command, args, dtypes = decode(line)
    if command == "get":  # data attribute
        ret = getattr(instance, *args)  # args has to be list with length 1
    elif command == "set":  # data attribute
        ret = setattr(instance, *args)  # args has to be list with length 2 (name of attribute and value)
    else:  # function
        ret = getattr(instance, command)(*args)
    returns(ret)