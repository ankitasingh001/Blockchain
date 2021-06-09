import threading
import socket
import sys
import ast
from datetime import datetime
import time
import hashlib
from random import shuffle
import struct

if len(sys.argv) != 3:
    print("ERROR: Usage: python3 Client.py <IP> <port>")
    exit(1)
# IP address and port of client node
IPAddr = sys.argv[1]
port = int(sys.argv[2])
# IP address and port of seed nodes
seed_nodes = [('10.129.131.135', 10000), ('10.196.20.144', 10000)]
# Sockets for communication with peers
socket_list = []
# To store the hash of the messages sent from and recieved at node
msg_list = []
lock = threading.Lock()


print("Welcome: ", (IPAddr+":"+str(port)))

#Listening to messages from peers and broadcasting the messages at the same time
def listen_to_connections(conn, addr, conn_port):
    global msg_list, socket_list, file, lock
    print("Listening to: ", addr)
    while True:
        # receive a message
        data = conn.recv(1024) 
        data = data.decode('utf-8')
        # Hashing the message using SHA-1
        sha_1 = hashlib.sha1()
        sha_1.update(data.encode('utf-8'))
        lock.acquire()
        if sha_1.hexdigest() not in msg_list: #See if the client already has msg#, if not add it to msg_list
            msg_list.append(sha_1.hexdigest())
            t = str(datetime.now())
            file = open("outputfile.txt", "a+")
            print(t + ": " + data + " : RECEIVED FROM " + addr[0] + ":" + str(conn_port) + ", RECEIVED AT " + IPAddr + ":" + str(port))
            file.write(t + ": " + data + " : RECEIVED FROM " + addr[0] + ":" + str(conn_port) + ", RECEIVED AT " + IPAddr + ":" + str(port) +"\n")
            file.close()
            #broadcast the message to all peers except from the one recieved
            for sock in socket_list:
                if sock != conn:
                    sock.sendall(str.encode(data))
        lock.release()

#Accept the connection request recieved from peers
def accept_connections():
    global port, IPAddr, socket_list
    print("Accepting connections...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((IPAddr, port))
    sock.listen(5)
    while True:
        conn, addr = sock.accept()
        # receives data of the form <"peer", port_no>
        unpacker = struct.Struct('4s I')
        data = conn.recv(unpacker.size)
        data = unpacker.unpack(data)
        print("In accept, connected to: " + addr[0] + ":" + str(addr[1]) + " Got data: " + str(data))
        if data[0] == b"peer":
            # start a thread to listen for messages from this peer
            t = threading.Thread(target=listen_to_connections, args=(conn,addr,data[1]))
            t.start()
            lock.acquire()
            # append the socket to socket_list to send messages to this peer
            socket_list.append(conn)
            lock.release()


def broadcast_messages():
    global seed_nodes, socket_list, port, IPAddr, msg_list
    # list to store the peer list obtained from seed nodes
    p_list = []
    print("In Broadcast...")
    connected_seeds=0
    connected_peers = 0
    shuffle(seed_nodes)
    print("shuffled seed nodes list:", seed_nodes)
    while True:
        k=0
        connected_seeds=0
        for i in range(len(seed_nodes)):
            # connect to atmost 3 seeds
            if connected_seeds == 3:
                break
            node = seed_nodes[i][0]
            node_port = seed_nodes[i][1]
            try: #get other peers info from seed node(s)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((node, node_port))
                print("Connected to seed node:", node)
                connected_seeds=connected_seeds+1
                # send request to seed node of the form <"seed", port_no>
                values = (b'seed', port)
                packer = struct.Struct('4s I')
                packed_data = packer.pack(*values)
                s.sendall(packed_data)
                data = s.recv(1024)
                data = data.decode('utf-8')
                print("Got data from seed node %s:%s " % (node, data))
                data = ast.literal_eval(data)
                p_list.extend(data)
                p_list = list(set(p_list))
                print("Peer list after connecting to seed node: "+node+" : "+str(p_list))
                s.close()
            except:
                print("Error while connection to seed node or fetching Peer list:", sys.exc_info()[1])
                k+=1
                s.close()
        if (k == len(seed_nodes)):
            print("No seed is online.")
        else:
            break
        print("Retrying after 5sec...")
        time.sleep(5)
    shuffle(p_list)

    for peer in p_list:
        if peer[0] == IPAddr and peer[1] == port :
            continue
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # connect to maximum 4 peers initially
            if connected_peers == 4:
                break
            sock.connect((peer[0], peer[1]))
            print("Connected to peer: ", peer)
            # send request to peer node of the form <"peer", port_no>
            values = (b'peer', port)
            packer = struct.Struct('4s I')
            packed_data = packer.pack(*values)
            sock.sendall(packed_data)
            lock.acquire()
            connected_peers = connected_peers + 1
            # append socket to socket_list to send data to this peer 
            socket_list.append(sock)
            lock.release()
            # start a thread to listen for messages from this peer
            t = threading.Thread(target=listen_to_connections, args=(sock,peer,peer[1]))
            t.start()
        except:
            print("Error in connecting to peer:", sys.exc_info()[1])
    done = 0
    while done == 0:
        # If this node is connected to any other peer,
        # it will send all the messages once to every peer connected
        # and then loop out
        # else if the client is not connected to any peers i.e. socket_list is empty
        # it will retry every 5 seconds to check if it has any peers before starting message generation
        if socket_list != []:
            msg_limit = 10
            done = 1
        else:
            print("No peers available to send messages. Retrying after 5s...")
            time.sleep(5)
            continue
        # send 10 messages originating from this node to all peers
        while msg_limit != 0:
            t = str(datetime.now())
            msg = t + ": " + IPAddr + ":" + str(port) + " - " + "Hello, This is message number: " +str(msg_limit)
            sha_1 = hashlib.sha1()
            sha_1.update(msg.encode('utf-8'))
            lock.acquire()
            msg_list.append(sha_1.hexdigest())
            lock.release()
            print("Sending... "+msg)
            msg_limit -= 1
            lock.acquire()
            for sock in socket_list:
                sock.sendall(str.encode(msg))
            lock.release()
            time.sleep(5)

# one thread to receive connection requests from peers
t1 = threading.Thread(target=accept_connections)
t1.start()

# one thread to get peer list from seed and send messages to them
t2 = threading.Thread(target=broadcast_messages)
t2.start()

t1.join()
t2.join()