import subprocess
import time
import os

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
    print(line)
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

def start_dll_process(python_path, dll_path, hostname):
    subprocess_path = os.path.abspath(os.path.dirname(__file__)) + "\\dll_subprocess.py"
    process = subprocess.Popen([python_path, subprocess_path, dll_path, hostname], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, universal_newlines=False)
    return process

def communicate(process, command, *args):
    data = f"{command}█{encode(args)}\n"
    print(f"writing {data}")
    process.stdin.write(data.encode())
    process.stdin.flush()
    
    decoded = process.stdout.readline().decode()
    print(f"return {decoded}")
    command, args, dtypes = decode(decoded)
    
    if len(args) > 1:
        return args
    elif len(args) == 1:
        return args[0]
    else:
        return None
