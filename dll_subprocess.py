import os
import sys
import clr
import System
import time

dll_path = sys.argv[1]
hostname = sys.argv[2]
sys.path.append("dll/bin")
clr.AddReference(dll_path)
# os.chdir("dll/bin")
dll_ref = System.Reflection.Assembly.LoadFile(dll_path)
type = dll_ref.GetType('kt002_persnr.kt002')
instance = System.Activator.CreateInstance(type)
instance.Init(hostname)
instance.InitTermConfig()

def write_log(msg):
    fpath = "C:\\Users\\MSSQL\\Desktop\\Tim\\Subprocess_Log.txt"
    os.makedirs(os.path.dirname(fpath), exist_ok=True)  # create dir if it does not exist
    with open(fpath, "a+") as fout:
        fout.write(f"\n{msg}")

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
    write_log(f"encoded {msg}")
    sys.stdout.write(msg)
    sys.stdout.flush()

for line in sys.stdin:
    write_log(f"received {line}")
    command, args, dtypes = decode(line)
    write_log(f"decoded {command}, {args}, {dtypes}")
    if command == "get":  # data attribute
        ret = getattr(instance, *args)  # args has to be list with length 1
    elif command == "set":  # data attribute
        ret = setattr(instance, *args)  # args has to be list with length 2 (name of attribute and value)
    else:  # function
        ret = getattr(instance, command)(*args)
    write_log(f"ret {ret}")
    returns(ret)