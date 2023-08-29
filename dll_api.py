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
    command, args, dtypes = line.strip().split("+++++")
    if len(args) == 0:  # no return
        return None, None, None
    args = args.split("_____")
    dtypes = dtypes.split("_____")
    args = convert_dtype(args, dtypes)
    return command, args, dtypes

def encode(msg):
    if msg is None:
        return f"+++++\n"
    else:
        dtypes = [type(x).__name__ for x in msg]
        return f"{'_____'.join(map(str, msg))}+++++{'_____'.join(dtypes)}\n"

def start_dll_process(python_path, dll_path, hostname):
    subprocess_path = os.path.abspath(os.path.dirname(__file__)) + "\\dll_subprocess.py"
    process = subprocess.Popen([python_path, subprocess_path, dll_path, hostname], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, universal_newlines=False)
    return process

def communicate(process, command, *args):
    for string in [command]+list(args):
        if "+++++" in str(string) or "_____" in str(string):
            raise ValueError("+++++ and _____ are used as seperators for custom encoding and may not be used in any DLL function name or argument.")
    
    data = f"{command}+++++{encode(args)}\n"
    print(f"wrote {data}")
    process.stdin.write(data.encode())
    process.stdin.flush()
    # print("flushed")
    
    # stdout = process.stdout
    # print(f"stdoud: {stdout}")
    # line_read = stdout.readline()
    # print(f"line_read: {line_read}")
    # decoded = line_read.decode()
    # print(f"decoded: {decoded}")
    decoded = process.stdout.readline().decode()
    print(f"received {decoded}")
    command, args, dtypes = decode(decoded)
    
    if args is None:
        print("returning None")
        return None
    elif len(args) > 1:
        print(f"returning {args}")
        return args
    elif len(args) == 1:
        print(f"returning {args[0]}")
        return args[0]
    else:
        print("returning None")
        return None
