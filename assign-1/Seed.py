import threading
import socket
import sys
import ast
from datetime import datetime
import time
import hashlib
import struct

if len(sys.argv) != 3:
    print("ERROR: Usage: python3 Seed.py <Seed IP> <Seed port>")
    exit(1)
# IP address and port of seed node
IPAddr = sys.argv[1]
peer_list = []
port = int(sys.argv[2])

print("Welcome to seed node : ", (IPAddr+":"+str(port)))

def accept_connections():
    global peer_list, port, IPAddr
    print("Accepting connections from peers...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((IPAddr, port))
    sock.listen(5) #max no of qued connections=5 here
    while True:
        #conn is a new socket object usable to send and receive data on 
        #the connection, and address is the address bound to the socket on the other
        #end of the connection        
        conn, addr = sock.accept()
        # receives data of the form <"seed", port_no>
        unpacker = struct.Struct('4s I')
        data = conn.recv(unpacker.size)
        data = unpacker.unpack(data)
        print("In accept, connected to:", addr[0], ":", data[1], "Got data:", data)
        if data[0] == b'seed':
            conn.send(str.encode(str(peer_list)))
            addr = (addr[0], data[1])
            # append IP address and port of the peer that sent the request to peer_list
            peer_list.append(addr)
            peer_list = list(set(peer_list))
            conn.close()
			
t1 = threading.Thread(target=accept_connections)
t1.start()
t1.join()
