#BSD 3-Clause, (C) Captain ALM 2022
import networker as net
import sys
from threading import Thread
#import traceback

translators = (net.PickleTranslate(), net.JSONTranslate())

inter = ""
port = 0
translator = None
conn = None
allowFiles = False
log = []

def listAsTypes(lin):
    toret = "["
    for x in lin:
        toret += str(type(x)) + ", "
    toret = toret[:-2]
    return toret + "]"

def onConn(addr):
    log.append(addr + " # Connection Established")

def onEnd(addr):
    log.append(addr + " # Connection Ended")

def onRecv(addr, msg):
    global allowFiles
    if type(msg) != net.Message:
        log.append("Invalid Message received from: " + addr)
        return
    if msg.mtype == net.MTYPE_Text:
        log.append(addr + " ; " + str(msg.header) + " ; " + str(msg.content))
    elif msg.mtype == net.MTYPE_File:
        if allowFiles:
            log.append(addr + " ; " + str(msg.header))
            msg.saveContent()
        else:
            log.append(addr + " ; File Rejected")
    else:
        log.append("Unknown Message type received from: " + addr)

def main():
    global allowFiles
    conn = net.Connection((inter, port), translator, onConn, onRecv, onEnd)
    ct = Thread(target=conn.listener, args=())
    ct.start()
    print("Listener started @ " + inter + ":" + str(port))
    print("Format: \"command;ip:port;argument\"")
    print("Commands: connect, disconnect, list, log, file_allowed, toggle_file_allowed, message, send, help, exit")
    while conn.active:
        cmd = input("> ").lower()
        csplt = cmd.split(";", 2)
        try:
            if len(csplt) > 0:
                if csplt[0] == "list":
                    print(conn.addresses())
                    continue
                elif csplt[0] == "help":
                    print("Help:")
                    print("connect;ip:port             -- Connects to the specified IP:Port")
                    print("disconnect;ip:port          -- Disonnects from the specified IP:Port")
                    print("list                        -- Lists the available IP:Port connections")
                    print("log                         -- Gets the message log")
                    print("file_allowed                -- Gets if file receiving is allowed")
                    print("toggle_file_allowed         -- Toggles if file receiving is allowed")
                    print("message;ip:port;header:body -- Sends a message to the specified IP:Port")
                    print("send;ip:port;path           -- Sends a file message to the specified IP:Port")
                    print("help                        -- Shows this message")
                    print("exit                        -- Exits this program closing all connections")
                    continue
                elif csplt[0] == "exit":
                    conn.close()
                    break
                elif csplt[0] == "log":
                    while len(log) > 0:
                        print(log.pop(0))
                    continue
                elif csplt[0] == "file_allowed":
                    print("Receive File Status: " + str(allowFiles))
                    continue
                elif csplt[0] == "toggle_file_allowed":
                    allowFiles = not allowFiles
                    print("Receive File Status set to: " + str(allowFiles))
                    continue
                if len(csplt) > 1:
                    if csplt[0] == "connect":
                        print("Attempting Connection to: " + csplt[1])
                        ippsplt = csplt[1].split(":", 1)
                        conn.connect((ippsplt[0], int(ippsplt[1])))
                        continue
                    elif csplt[0] == "disconnect":
                        print("Attempting Disconnection from: " + csplt[1])
                        conn.actives[csplt[1]] = False
                        conn.sockets[csplt[1]].close()
                        continue
                    if len(csplt) > 2:
                        if csplt[0] == "message":
                            datasplt = csplt[2].split(":", 1)
                            print("Attempting to send message to: " + csplt[1])
                            conn.send(csplt[1], net.Message(net.MTYPE_Text, datasplt[0], datasplt[1]))
                            continue
                        elif csplt[0] == "send":
                            print("Attempting to send file to: " + csplt[1])
                            conn.send(csplt[1], net.Message(net.MTYPE_File, csplt[2], None))
                            continue
            print("Invalid Command!")
                    
        except Exception as e:
            print("Command Error!")
            #print(traceback.format_exc())
    exit
                    

if __name__ == "__main__":
    print("Python Communicator (C) Alfred Manville 2022 BSD-3-Clause")
    if len(sys.argv) > 1:
        inter = sys.argv[1]
    else:
        inter = input("Enter the listening interface: ")
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    else:
        port = int(input("Enter the listening port: "))
    if len(sys.argv) > 3:
        translator = translators[int(sys.argv[3]) - 1]
    else:
        translator = translators[int(input("Enter the message translator position " + listAsTypes(translators) + " : ")) - 1]
    main()
    
        
