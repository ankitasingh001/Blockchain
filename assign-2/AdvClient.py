import threading
import socket
import sys
import ast
from datetime import datetime, timedelta
import time
import hashlib
from random import shuffle, expovariate
import struct
import sqlite3
import pickle 

#Defining the block structure of blockchain

class Block():
    def __init__(self, idx, timestamp, merkelroot, previous_hash,height):
        self.idx = idx  #To be stored globally
        self.timestamp = timestamp
        self.merkelroot = merkelroot
        self.previous_hash = previous_hash
        self.height = height #This is not included in hash
        self.hash = self.hash_block()
    def hash_block(self):
        sha = hashlib.sha256()
        sha.update(str(self.idx).encode('utf-8'))
        sha.update(str(self.height).encode('utf-8'))
        sha.update(str(self.timestamp).encode('utf-8'))
        sha.update(str(self.merkelroot).encode('utf-8'))
        sha.update(str(self.previous_hash).encode('utf-8'))
        return sha.hexdigest()[-4:] 
        
# Class for validating and adding new blocks to DB and public chain

class validateAndAddBlock:

    def __init__(self,dbfile,tablename): # Initialize and create new database/table for each client 
        self.dictionary_of_hash ={}
        self.dictionary_of_hash['9e1c'] = '0'  # Initialising dictionary with genesis block
        self.public_chain = ['9e1c'] # Initialising public chain
        self.private_chain = ['9e1c']
        self.private_branch = [] # Contains blocks generated in private branch
        self.private_branch_len = 0
        self.conn = None
        self.db_file= dbfile
        self.tablename = tablename
        self.conn=sqlite3.connect(self.db_file)
        self.cur = self.conn.cursor()
        self.conn.execute("DROP TABLE IF EXISTS "+str(self.tablename)+";")
        self.conn.execute("CREATE TABLE IF NOT EXISTS "+str(self.tablename)+"( idx INT , height INT NOT NULL , MerkleRoot TEXT  , Timestramp DATETIME NOT NULL,previous_hash TEXT NOT NULL, current_hash TEXT NOT NULL);")
        genesis_data = (0,0,"genesisMerkel",datetime.utcnow(),"0",'9e1c')
        self.cur.execute("INSERT INTO "+str(self.tablename)+" (idx , height , MerkleRoot , Timestramp ,previous_hash , current_hash ) VALUES (?, ?, ?, ?, ?, ?);", genesis_data)
        self.conn.commit()
     
    #Stores the block in the database as well as appends the dictionary of hashes of block
    def addBlocktoDB(self, Block):
        #self.blocks.append(Block)
        self.conn=sqlite3.connect(self.db_file)
        self.cur = self.conn.cursor()
        self.dictionary_of_hash[Block.hash] = Block.previous_hash
        block_data = (Block.idx,Block.height,"BlockMerkel",Block.timestamp,Block.previous_hash,Block.hash)
        self.cur.execute("INSERT INTO "+str(self.tablename)+" (idx , height , MerkleRoot , Timestramp ,previous_hash , current_hash  ) VALUES (?, ?, ?, ?, ?, ?);", block_data)
        self.conn.commit()
        
    def getPublicChain(self): 
        print(self.public_chain)
        return self.public_chain

    #Verifies if the block recieved is valid
    def verifyBlockHeader(self,Block):
        valid = True
	   # Check if the timestamp of the block added is valid
        if (Block.timestamp > (datetime.utcnow() + timedelta(hours =1)) or
            Block.timestamp < (datetime.utcnow() - timedelta(hours =1))) :
                valid = False
                print ("Timestramp exceeds one hour range ")

        # Check if the previous hash of block exists / is valid
        if Block.previous_hash not in self.dictionary_of_hash: 
            valid = False
            print("Block added has incorrect hash")

        # Check if we already have the block
        if Block.hash in self.dictionary_of_hash:
            valid = False
            print("Already received the block")

        return valid

    #append the incoming block to the public chain if the block creates a longer chain
    def addBlocktoPublicChain(self,Block):
        chainLen = len(self.public_chain)-1
        #print(self.dictionary_of_hash)
        if(Block.height > chainLen):
            self.public_chain.append(Block.hash)
            hashOfBlock = Block.previous_hash
            while(hashOfBlock != self.public_chain[chainLen]):
                self.public_chain[chainLen] = hashOfBlock
                hashOfBlock = self.dictionary_of_hash[hashOfBlock]
                chainLen = chainLen -1
            return True
        return False

    #prints the database
    def print_all(self):
        self.conn=sqlite3.connect(self.db_file)
        cursor = self.conn.execute("SELECT * from "+str(self.tablename))
        for row in cursor:
            print(row[0],'\t',row[1],'\t',row[2],'\t',row[3],'\t',row[4],'\t',row[5])

    # If block is generated privately :         
    def block_created(self,Block):
        released =0
        delta = len(self.private_chain) - len(self.public_chain)
        # Appending new block to private chain
        self.private_chain.append(Block.hash)
        self.private_branch.append(Block)
        self.private_branch_len += 1
        # Case where there was a tie with a branch of one, 
        # private branch wins because of lead of 1
        if delta==0 and self.private_branch_len ==2 :
            released = 1
            self.private_branch_len = 0
            branch = self.private_branch.copy()
            self.private_branch =[]
            return branch
        #If no private blocks released return empty list
        if released == 0:
            return []

    #In case where other nodes mine the block first   
    def block_found(self,Block):
        delta = len(self.private_chain) - len(self.public_chain)
        #appending new block to public chain
        Blockadded = False
        valid = blockchain.verifyBlockHeader(Block)
        if valid == True:
            blockchain.addBlocktoDB(Block)
            Blockadded = self.addBlocktoPublicChain(Block)
        if Blockadded == False: # If no block was added to public chain ,return
            return [], False
        if delta == 0: #Other nodes win
            self.private_chain = self.public_chain.copy()
            self.private_branch_len =0
            self.private_branch = []
            return [], True
        elif delta == 1: #Same length of public and private chain ,release and try luck
            lastblock = self.private_branch[-1]
            # del self.private_branch[-1]
            lastblockl = [lastblock]
            return lastblockl, False
        elif delta == 2: # Private chain wins due to a lead of 1
            self.private_branch_len = 0
            branch = self.private_branch.copy()
            self.private_branch =[]
            return branch, False
        elif delta > 2: #Publishing first unpublished block in private blocks
            firstblock = self.private_branch[0]
            del self.private_branch[0]
            self.private_branch_len -= 1
            firstblockl = [firstblock]
            return firstblockl, False

    def append_released_blocks(self,Blocks):
        for Block in Blocks:
            valid = blockchain.verifyBlockHeader(Block)
            if valid == True:
                blockchain.addBlocktoDB(Block)
                self.addBlocktoPublicChain(Block)

    def print_chain(self):
        print("Private chain:",self.private_chain)
        print("Public chain:", self.public_chain)
        
    def print_private_blocks(self):
        for blocks in self.private_branch:
            print(blocks.hash)  

if len(sys.argv) != 4:
    print("ERROR: Usage: python3 Client.py <IP> <port> <nodeHashPower>")
    exit(1)
# IP address and port of client node
IPAddr = sys.argv[1]
port = int(sys.argv[2])
nodeHashPower = float(sys.argv[3])
# IP address and port of seed nodes
seed_nodes = [('10.15.39.167', 10000)]
# Sockets for communication with peers
socket_list = []
# To store the hash of the messages sent from and recieved at node
msg_list = []
lock = threading.Lock()
cond = threading.Condition()

interArrivalTime = 10 #in seconds
globalLambda = 1.0/interArrivalTime
lambd = nodeHashPower*globalLambda/100

print("Welcome: ", (IPAddr+":"+str(port)))

#Listening to messages from peers and broadcasting the messages at the same time
def listen_to_connections(conn, addr, conn_port):
    global msg_list, socket_list, lock
    print("Listening to: ", addr)
    while True:
        # receive a message
        data = conn.recv(1024)  
        block = pickle.loads(data)
        print("received a block: ", block.hash)
        cond.acquire()
        blocks, changed = blockchain.block_found(block)
        blockchain.append_released_blocks(blocks)
        time.sleep(1)
        for block in blocks:
            for sock in socket_list:
                sock.sendall(pickle.dumps(block))
        blocks_hash = [block.hash for block in blocks]
        print("blocks sent: ", blocks_hash, "changed: ", changed)
        if changed == True:
            cond.notify()
        cond.release()
        

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
                # s.close()
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
    
    #waiting for "start" mining message from seed node
    data = s.recv(5)
    data = data.decode('utf-8')
    print("Got data from seed node %s:%s " % (node, data))
    s.close()

    t_end = time.time() + 60 * 10 #To run loop for ten minutes
    while time.time() < t_end:
        tow = expovariate(lambd)
        print("tow =", tow)
        cond.acquire()
        var = cond.wait(timeout=tow)
        if var == True: #a longer chain is received from peers before a block is generated
            print("private chain head has been changed, restart mining")
            cond.release()
            continue
        elif var == False: #a block is generated
            print("a block is generated in the private chain")
            block_height = len(blockchain.private_chain)
            block = Block(0, datetime.utcnow(), "merkelroot", blockchain.private_chain[block_height-1], block_height)
            private_blocks.add(block.hash)
            blocks = blockchain.block_created(block)
            blockchain.append_released_blocks(blocks)
            time.sleep(1)
            for block in blocks:
                for sock in socket_list:
                    sock.sendall(pickle.dumps(block))
            # blockchain.print_all()
            blocks_hash = [block.hash for block in blocks]
            print("blocks sent: ", blocks_hash)
            blockchain.print_chain()
        cond.release()
        print("-"*100)
    if(len(blockchain.private_branch)>0):
        firstblock = blockchain.private_branch[0]
        blockchain.addBlocktoPublicChain(firstblock)
    public_blocks = set(blockchain.public_chain)
    common_blocks = list(public_blocks&private_blocks)
    if len(list(private_blocks)) != 0: 
        fraction = len(common_blocks)/len(list(private_blocks))
    else:
        fraction = 0
    print("Attacker blocks in the public chain:", common_blocks)
    print("No. of attacker blocks in the public chain:", len(common_blocks))
    print("Fraction of blocks mined by attacker in public chain:", fraction)
    print("Fraction of attacker blocks that are there in public chain:",len(common_blocks)/len(public_blocks))
dbName = "Advclient"+str(port%10000)
blockchain = validateAndAddBlock(dbName,"Test")
private_blocks = set()

# one thread to receive connection requests from peers
t1 = threading.Thread(target=accept_connections)
t1.start()

# one thread to get peer list from seed and send messages to them
t2 = threading.Thread(target=broadcast_messages)
t2.start()

t1.join()
t2.join()
