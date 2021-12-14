import ctypes


#loading dll into memory

DLLFile = ctypes.CDLL("dll/testDll.dll")

#Simple function call with no return type
DLLFile.foo()

#Passing integer type arguments and returning sum
print(DLLFile.MyAdd(4,5))

#print(DLLFile)

#Passing a String to dll
DLLFile.textreturn.argtypes = [ctypes.c_char_p,ctypes.c_char_p,ctypes.c_size_t] #defining the datatype of arguments
DLLFile.textreturn.restype = ctypes.c_char_p #defining return type

phrase = b"Hellloooooo" #b' used to specify its a byte string
result = ctypes.create_string_buffer(100)
res = DLLFile.textreturn(phrase,result,ctypes.sizeof(result))
print(res)
print(result.value)


#DLLFile.Init()
#DLLFile.to020.init()
#DLLFile2 = ctypes.CDLL("termdll/kt002_PersNr.dll")
#DLLFile2.Init_TermConfig()
#xret = DLLFile2.ShowNumber("1050", 0, 0, True, True, "", xsa, xfkt)
#print("Hello World")



"""
functionProtoptype = ctypes.WINFUNCTYPE(
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_bool,
    ctypes.c_bool,
    ctypes.c_char,
    ctypes.c_char,
    ctypes.c_char
)
functionparameters = (1050,0,0,True,True,"", 0, 0)

functionAPI = functionProtoptype(("ShowNumber",DLLFile2),functionparameters)

p1 = ctypes.c_int (1050)
p2 = ctypes.c_int (0)
p3 = ctypes.c_int (0)
p4 = ctypes.c_bool(True)
p5 = ctypes.c_bool (True)
p6 = ctypes.c_char ("")
p7 = ctypes.c_int (0)
p8 = ctypes.c_int (0)

functionAPI (ctypes.byref(p1),ctypes.byref(p2),ctypes.byref(p3), p4,p5,p6,ctypes.byref(p7),ctypes.byref(p8),)


"""

