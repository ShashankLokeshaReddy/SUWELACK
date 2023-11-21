import subprocess
import time
import os
import socket

SOCKET_TIMEOUT = 5  # secs
SOCKET_INTERVAL = 0.01  # secs, connect interval

def convert_dtype(args, dtypes):
    out = []
    for arg, dtype in zip(args, dtypes):
        if dtype == "bool":
            if arg == "True":
                out.append(True)
            else:
                out.append(False)
        elif dtype == "NoneType":
            out.append(None)
        else:
            out.append(eval(dtype)(arg))
    return out

def decode(msg):
    command, args, dtypes = msg.decode().strip().split("+++++")
    if len(dtypes) == 0:  # no return
        return None, None, None
    args = args.split("_____")
    dtypes = dtypes.split("_____")
    args = convert_dtype(args, dtypes)
    return command, args, dtypes

def encode(msg):
    if msg is None:
        return f"++++++++++"
    else:
        dtypes = [type(x).__name__ for x in msg]
        return f"{'_____'.join(map(str, msg))}+++++{'_____'.join(dtypes)}"

def start_dll_process(python_path, dll_path, hostname, socket_host, socket_port, start_subprocess=False):
    if start_subprocess:
        subprocess_path = os.path.abspath(os.path.dirname(__file__)) + "\\dll_subprocess.py"
        process = subprocess.Popen([python_path, subprocess_path, dll_path, hostname, socket_host, str(socket_port)])

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    start_time = time.time()
    while time.time() - start_time < SOCKET_TIMEOUT:
        try:
            client.connect((socket_host, socket_port))
            break  # if above successfull, break
        except socket.error:
            time.sleep(SOCKET_INTERVAL)  # wait short interval before next try to not waste compute resources
    else:
        raise TimeoutError(f"Unable to connect to {socket_host}:{socket_port} within {SOCKET_TIMEOUT} seconds.")
    return client

def communicate(client, command, *args):
    for string in [command]+list(args):
        if "+++++" in str(string) or "_____" in str(string):
            raise ValueError("+++++ and _____ are used as seperators for custom encoding and may not be used in any DLL function name or argument.")
    
    data = f"{command}+++++{encode(args)}\n"
    client.sendall(data.encode())
    
    received = client.recv(1024)
    if received:
        command, args, dtypes = decode(received)
    
        if args is None:
            return None
        elif (isinstance(args, list) and len(args) > 1) or isinstance(args, str) or isinstance(args, bool) or isinstance(args, int) or isinstance(args, float):
            # multiple return variables or single primitive datatype
            return args
        elif isinstance(args, list) and len(args) == 1:
            # if return is just a single variable, return it without list wrapper
            if args[0] == "exception":
                return None
            else:
                return args[0]
        else:
            return None
