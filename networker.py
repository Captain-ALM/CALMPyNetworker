#BSD 3-Clause, (C) Captain ALM 2022
import pickle
import json
import socket
import time
from threading import Thread
import base64
#import traceback

#Defines a message class that has a type, header and a body.
class Message:

    def __init__(self, mtype, header, content):
        self.mtype = mtype
        self.header = header
        if mtype == MTYPE_File:
            try:
                f = open(header, "rb")
                try:
                    self.content = f.read()
                except:
                    print("An issue writing the message for \"" + self.header + "\" occured.")
                    f.close()
            except:
                print("An issue when opening a file for reading: \"" + self.header + "\" occured.")
                #print(traceback.format_exc())
        else:
            self.content = content

    def saveContent(self):
        if self.mtype != MTYPE_File: pass
        try:
            f = open(str(self.header), "wb")
            try:
                if type(self.content) == bytes or type(self.content) == bytearray:
                    f.write(bytes(self.content))
                else:
                    f.write(bytes(self.content, encoding='utf-8'))
            except:
                print("An issue writing the message for \"" + str(self.header) + "\" occured.")
                #print(traceback.format_exc())
            f.close()
        except:
            print("An issue when opening a file for writing: \"" + str(self.header) + "\" occured.")

    def toDict(self):
        toReturn = {"mtype":self.mtype, "header":self.header, "ident__":"Message"}
        if type(self.content) == bytes or type(self.content) == bytearray:
            toReturn["contentb64"] = True
            toReturn["content"] = base64.b64encode(bytes(self.content)).decode()
        else:
            toReturn["contentb64"] = False
            toReturn["content"] = self.content
        return toReturn

#Message from dict:
def MessageFromDict(d):
    if type(d) != None and d.get("ident__") == "Message":
        if d.get("contentb64") != None:
            if d.get("contentb64"):
                return Message(int(d.get("mtype")),d.get("header"), base64.b64decode(d.get("content")))
            else:
                return Message(int(d.get("mtype")),d.get("header"), d.get("content"))
    print("Invalid message dictionary!")
    return None

#mtype Definitions:
MTYPE_Text = 0;
MTYPE_File = 1;

#Pickle Translator for Message to and from bytes.
class PickleTranslate:
    def toString(self, m):
        try:
            return pickle.dumps(m)
        except:
            #print(traceback.format_exc())
            return None
    def fromString(self, b):
        try:
            return pickle.loads(b)
        except:
            #print(traceback.format_exc())
            return None

#JSON Translator for Message to and from bytes.
class JSONTranslate:
    def toString(self, m):
        try:
            return json.dumps(m.toDict())
        except:
            #print(traceback.format_exc())
            return None
    def fromString(self, b):
        try:
            return MessageFromDict(json.loads(b))
        except:
            #print(traceback.format_exc())
            return None

#Connection class
class Connection:
    active = True
    sockets = dict()
    threads = dict()
    actives = dict()
    def __init__(self, binder, translator, onconn, onrecv, onend):
        if binder != None:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind(binder)
            self.socket.listen(8)
        else:
            self.socket = None
        self.translator = translator
        self.onconn = onconn
        self.onrecv = onrecv
        self.onend = onend
    def listener(self):
        if self.socket == None:
            return
        while self.active:
            s, a = self.socket.accept()
            ac = a[0] + ":" + str(a[1])
            try:
                self.onconn(str(ac))
            except:
                print("Failure to call onconn for: " + str(ac))
            self.sockets[str(ac)] = s
            self.actives[str(ac)] = True
            self.threads[str(ac)] = Thread(target=self.processor, args=(str(ac),))
            self.threads[str(ac)].start();
        self.socket.close()

    def processor(self, addr):
        while self.active and self.actives[addr]:
            try:
                head = self.sockets[addr].recv(2)
                if type(head) == None or len(head) != 2:
                    print("An issue reading the packet header has occured for: " + addr)
                    break
                dataSize = 0
                try:
                    dataSize = int(head[0]) * 256 + int(head[1])
                except:
                    print("An issue reading the packet header has occured for: " + addr)
                    break
                if dataSize < 1:
                    continue
                data = bytearray()
                while dataSize > 0:
                    dataL = self.sockets[addr].recv(dataSize)
                    dataSize -= len(dataL)
                    data.extend(dataL)
                try:
                    self.onrecv(addr, self.translator.fromString(data))
                except:
                    print("Failure to call onrecv for: " + addr)
            except:
                print("A network issue has occured for: " + addr)
                self.actives[addr] = False
                break
        self.onend(addr)

    def send(self, addr, m):
        if self.active and self.actives[addr]:
            try:
                toSendData = self.translator.toString(m)
                toSend = []
                if type(toSendData) == bytes or type(toSendData) == bytearray:
                    toSend = bytes(self.translator.toString(m))
                else:
                    toSend = bytes(self.translator.toString(m), encoding='utf-8')
                sendLength = len(toSend)
                if sendLength < 1:
                    print("Message for: " + addr + " empty?")
                    return
                if sendLength > 65535:
                    print("Message for: " + addr + " too big!")
                    return
                head = bytearray(2)
                head[0] = sendLength//256
                sendLength -= int(head[0])*256
                head[1] = sendLength
                sendLength = -2
                try:
                    sendLength += self.sockets[addr].send(bytes(head))
                    sendLength += self.sockets[addr].send(toSend)
                except:
                    try:
                        if sendLength >= 0:
                           self.sockets[addr].send(bytes(len(toSend) - sendLength))
                    except:
                        print("A network issue has occured for: " + addr)
                        self.actives[addr] = False
            except:
                print("A send failure has occured for: " + addr)
                #print(traceback.format_exc())

    def close(self):
        self.active = False
        for x in self.actives: self.actives[x] = False
        for x in self.sockets: self.sockets[x].close()
        ndone = True
        while ndone:
            ndone = False
            for x in self.threads:
                if self.threads[x].is_alive():
                    ndone = True
                    break
            time.sleep(0.0001)
        self.threads.clear()
        if self.socket != None: self.socket.close()

    def addresses(self):
        if self.active:
            tL = []
            for x in self.actives:
                if self.actives[x]:
                    tL.append(x)
            return tL
        else:
            return []

    def connect(self, target):
        ac = target[0]+":"+str(target[1])
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(target)
            try:
                self.onconn(str(ac))
            except:
                print("Failure to call onconn for: " + str(ac))
            self.sockets[str(ac)] = s
            self.actives[str(ac)] = True
            self.threads[str(ac)] = Thread(target=self.processor, args=(str(ac),))
            self.threads[str(ac)].start()
        except:
            print("A connection error has occured for: " + ac)

    def disconnect(self, addr):
        if self.actives[addr]:
            self.actives[addr] = False
            self.sockets[addr].close()
        
