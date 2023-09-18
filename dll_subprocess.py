import datetime
import os
import sys
import clr
import System
import time
import socket

dll_path = sys.argv[1]
hostname = sys.argv[2]
socket_host = sys.argv[3]
socket_port = int(sys.argv[4])
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ROOT_DIR = os.path.abspath(os.path.dirname(__file__)) + "\\"  # directory which directly contains dll_subprocess.py

try:
    server.setsockopt(socket.SOL_SOCKET, socket.SOCK_STREAM, 1)
    server.bind((socket_host, socket_port))
    
    do_run = True
    server.listen()
    
    conn, addr = server.accept()

    sys.path.append("dll/bin")
    clr.AddReference(dll_path)
    # os.chdir("dll/bin")
    dll_ref = System.Reflection.Assembly.LoadFile(dll_path)
    dll_type = dll_ref.GetType('kt002_persnr.kt002')
    instance = System.Activator.CreateInstance(dll_type)
    instance.Init(hostname)
    instance.InitTermConfig()

    def write_log(msg):
        date_formatted = datetime.datetime.now().strftime("%Y_%m_%d")
        datetime_formatted = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]
        # print(f"{datetime_formatted} {username} -- {msg}")
        print(f"{datetime_formatted} -- {msg}")
        # fpath = ROOT_DIR+f"dll\\log\\{username}\\l_{date_formatted}\\AppLog_{date_formatted}.txt"
        fpath = ROOT_DIR+f"dll\\log\\l_{date_formatted}\\SubprocessLog_{date_formatted}.txt"
        os.makedirs(os.path.dirname(fpath), exist_ok=True)  # create dir if it does not exist
        with open(fpath, "a+") as fout:
            # fout.write(f"\n{datetime_formatted} {username} -- {msg}")
            fout.write(f"\n{datetime_formatted} -- {msg}")

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

    def decode(line):
        split = str(line.decode().strip()).split("+++++")
        if len(split) == 1:
            return None, None, None
        command, args, dtypes = split
        if len(dtypes) == 0:  # no return
            return command, [], []
        args = args.split("_____")
        dtypes = dtypes.split("_____")
        args = convert_dtype(args, dtypes)
        return command, args, dtypes

    def encode(msg):
        write_log(f"encoding msg: {msg}")
        if msg is None:
            return f"++++++++++".encode()
        else:
            if not hasattr(msg, '__iter__') or isinstance(msg, str):  # primitive datatypes including strings
                msg = [msg]
            dtypes = [type(x).__name__ for x in msg]
            return_params = f"{'_____'.join(map(str, msg))}+++++{'_____'.join(dtypes)}"
            return f"_+++++{return_params}".encode()
    
    with conn:
        while do_run:
            data = conn.recv(1024)
            if not data:
                server.shutdown(1)
                server.close()
                break
            else:
                write_log(f"received: {str(data.decode())}")
                command, args, dtypes = decode(data)
                write_log(f"decoded: {command, args, dtypes}")
                if command is None and args is None and dtypes is None:
                    ret = None
                if command == "get":  # data attribute
                    ret = getattr(instance, *args)  # args has to be list with length 1
                elif command == "set":  # data attribute
                    ret = setattr(instance, *args)  # args has to be list with length 2 (name of attribute and value)
                elif command == "shutdown":
                    write_log("_got shutdown")
                    break  # shutdown subprocess graciously
                else:  # function
                    ret = getattr(instance, command)(*args)
                
                write_log(f"ret: {ret}")
                
                if ret is not None and not (isinstance(ret, tuple) or isinstance(ret, list) or isinstance(ret, int) or isinstance(ret, str) or isinstance(ret, bool) or isinstance(ret, float)):
                    try:
                        ret = str(ret)  # e.g. System.Data.DataRow. In app.oy only checks for not None with these objects, can be any non None object
                    except:
                        ret = "Non Serializable Object"
                if ret is not None:
                    if isinstance(ret, str):
                        if "+++++" in str(string) or "_____" in str(string):
                            raise ValueError("+++++ and _____ are used as seperators for custom encoding and may not be used in any DLL function name or argument.")
                    elif hasattr(ret, '__iter__'):  # check if multiple returns
                        for string in ret:
                            if "+++++" in str(string) or "_____" in str(string):
                                raise ValueError("+++++ and _____ are used as seperators for custom encoding and may not be used in any DLL function name or argument.")
                        
                conn.sendall(encode(ret))

finally:
    server.close()
