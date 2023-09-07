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

try:
    server.setsockopt(socket.SOL_SOCKET, socket.SOCK_STREAM, 1)
    server.bind((socket_host, socket_port))
    
    do_run = True
    server.listen()
    
    conn, addr = server.accept()

    sys.path.append("dll/bin")
    clr.AddReference(dll_path)
    os.chdir("dll/bin")
    dll_ref = System.Reflection.Assembly.LoadFile(dll_path)
    dll_type = dll_ref.GetType('kt002_persnr.kt002')
    instance = System.Activator.CreateInstance(dll_type)
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
        write_log(f"decode {line.decode()}")
        write_log(f"stripped {line.decode().strip()}")
        split = str(line.decode().strip()).split("+++++")
        write_log(f"split {split}")
        if len(split) == 1:
            return None, None, None
        command, args, dtypes = split
        if len(args) == 0:  # no return
            return command, [], []
        args = args.split("_____")
        dtypes = dtypes.split("_____")
        args = convert_dtype(args, dtypes)
        return command, args, dtypes

    def encode(msg):
        if msg is None:
            return f"++++++++++".encode()
        else:
            dtypes = [type(x).__name__ for x in msg]
            return_params = f"{'_____'.join(map(str, msg))}+++++{'_____'.join(dtypes)}"
            return f"_+++++{return_params}".encode()

    # def returns(res):
    #     msg = msg = f"_+++++{encode(res)}"
    #     # write_log(f"encoded {msg}")
    #     sys.stdout.write(msg.encode())
    #     # sys.stdout.flush()
    
    with conn:
        # print(f"connected by {addr}")
        
        while do_run:
            data = conn.recv(1024)
            if not data:
                server.shutdown(1)
                server.close()
                break
            else:
                command, args, dtypes = decode(data)
                if command is None and args is None and dtypes is None:
                    ret = None
                # write_log(f"decoded {command}, {args}, {dtypes}")
                if command == "get":  # data attribute
                    ret = getattr(instance, *args)  # args has to be list with length 1
                elif command == "set":  # data attribute
                    ret = setattr(instance, *args)  # args has to be list with length 2 (name of attribute and value)
                elif command == "shutdown":
                    write_log("_got shutdown")
                    break  # shutdown subprocess graciously
                else:  # function
                    ret = getattr(instance, command)(*args)
                # write_log(f"ret {ret}")
                if ret is not None:
                    for string in ret:
                        if "+++++" in str(string) or "_____" in str(string):
                            raise ValueError("+++++ and _____ are used as seperators for custom encoding and may not be used in any DLL function name or argument.")
                        
                conn.sendall(encode(ret))

finally:
    # print("\nclosing server")
    server.close()











for line in sys.stdin:
    # write_log(f"received {line}")
    command, args, dtypes = decode(line)
    if command is None and args is None and dtypes is None:
        continue
    # write_log(f"decoded {command}, {args}, {dtypes}")
    if command == "get":  # data attribute
        ret = getattr(instance, *args)  # args has to be list with length 1
    elif command == "set":  # data attribute
        ret = setattr(instance, *args)  # args has to be list with length 2 (name of attribute and value)
    elif command == "shutdown":
        write_log("_got shutdown")
        returns(None)
        write_log("_returned")
        break  # shutdown subprocess graciously
    else:  # function
        ret = getattr(instance, command)(*args)
    # write_log(f"ret {ret}")
    if ret is not None:
        for string in ret:
            if "+++++" in str(string) or "_____" in str(string):
                raise ValueError("+++++ and _____ are used as seperators for custom encoding and may not be used in any DLL function name or argument.")
    returns(ret)
    
write_log("_broken out")