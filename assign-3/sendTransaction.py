import sys
import time
import pprint
from threading import Thread
from web3 import *
from solc import compile_source
import secrets, string
from Crypto.Cipher import AES

def compile_source_file(file_path):
   with open(file_path, 'r') as f:
      source = f.read()
   return compile_source(source)

w3 = Web3(IPCProvider('/home/nikhila/Desktop/CS620-assign3/Assignment3Setup/test-eth1/geth.ipc', timeout=100000))
w3_1 = Web3(IPCProvider('/home/nikhila/Desktop/CS620-assign3/Assignment3Setup/test-eth2/geth.ipc', timeout=100000))

contract_source_path = '/home/nikhila/Desktop/CS620-assign3/Assignment3/mediaContract.sol'

compiled_sol = compile_source_file(contract_source_path)

contract_id, contract_interface = compiled_sol.popitem()

with open('/home/nikhila/Desktop/CS620-assign3/Assignment3/contractAddressList1') as fp:
    for line in fp: 
        a,b = line.rstrip().split(':', 1)
        if a=="media":
            address=b
            
sort_contract = w3.eth.contract(
address=address,
abi=contract_interface['abi'])

sort_contract1 = w3_1.eth.contract(
address=address,
abi=contract_interface['abi'])

def handle_event(event):
    #printing type of events and data passed in those events
    print(event.event)
    print(event.args)
    print("-"*100)
    if event.event == "MediaPurchased":
        publicKey = event.args.userAddr
        N = 32
        url = str(''.join(secrets.choice(string.ascii_uppercase + string.digits) for i in range(N)))
        print("Generated url:", url)
        obj = AES.new(publicKey[0:-10].encode("utf8"), AES.MODE_CFB, 'This is an IV456'.encode("utf8"))
        ciphertext = obj.encrypt(url.encode("utf8"))
        tx_hash1 = sendSendMediaLinkTransaction(ciphertext)
        waitForTransaction(tx_hash1)
        print("Generated ciphertext:", ciphertext)
    elif event.event == "MediaLinkCreated":
        toDecrypt = sort_contract1.functions.getMediaLink(0, 1).call()
        obj2 = AES.new(w3_1.eth.accounts[0][0:-10].encode("utf8"), AES.MODE_CFB, 'This is an IV456'.encode("utf8"))
        print("Link received after decrpytion:", obj2.decrypt(toDecrypt).decode("utf8"))
        print("Available media for user 1: ")
        print(sort_contract1.functions.getMedia(1).call())
        print("Available media for user 2: ")
        print(sort_contract1.functions.getMedia(2).call())
    # and whatever

def log_loop(event_filters, poll_interval):
    while True:
        for event_filter in event_filters:
            for event in event_filter.get_new_entries():
                handle_event(event)
        time.sleep(poll_interval)

# creating filters for events and a thread to continuously poll events of those types
event_filter1 = sort_contract.events.UserRegistered.createFilter(fromBlock="latest")
event_filter2 = sort_contract.events.MediaPurchased.createFilter(fromBlock="latest")
event_filter3 = sort_contract.events.MediaLinkCreated.createFilter(fromBlock="latest")
worker = Thread(target=log_loop, args=([event_filter1, event_filter2, event_filter3], 5), daemon=True)
worker.start()

# send transaction for the user registration
def sendRegisterTransaction(isConsumer, isCompany, w3, sort_contract):
    tx_hash = sort_contract.functions.registerUser(isConsumer, isCompany).transact({'txType':"0x1", 'from':w3.eth.accounts[0], 'gas':2409638})
    return tx_hash

# send transaction for adding media
def sendAddMediaTransaction():
    tx_hash = sort_contract.functions.addMedia(0, "bad guy mp3".encode('utf-8'), w3.toWei(5, 'ether'), w3.toWei(1, 'ether'), [w3.toChecksumAddress('0x8363aff7e76153408eae7b0ca4957db8d60634ef'), w3.toChecksumAddress('0x3c03c1044b73170f2e18b5a57d1dd95ec260aaaa')], [40, 20]).transact({'txType':"0x1", 'from':w3.eth.accounts[0], 'gas':2409638})
    return tx_hash

# send transaction for purchsing media
def sendPurchaseMediaTransaction():
    tx_hash = sort_contract1.functions.purchaseMedia(0, 1).transact({'txType':"0x1", 'from':w3_1.eth.accounts[0], 'gas':2409638, 'value': w3.toWei(1, 'ether')})
    return tx_hash

# send transaction for sending media link
def sendSendMediaLinkTransaction(url):
    tx_hash = sort_contract.functions.sendMediaLink(url, 1, 0).transact({'txType':"0x1", 'from':w3.eth.accounts[0], 'gas':2409638})
    return tx_hash

#send getcall to fetch the media details and user registration details
def printSendGetTransactions():
    print("-"*50, "Users", "-"*50)
    print(sort_contract.functions.getUser(0).call())
    print(sort_contract.functions.getUser(1).call())
    print(sort_contract.functions.getUser(2).call())
    print("-"*50, "Consumers", "-"*50)
    print(sort_contract.functions.getConsumer().call())
    print("-"*50, "Creators", "-"*50)
    print(sort_contract1.functions.getCreator().call())
    print("-"*50, "Medias", "-"*50)
    print(sort_contract.functions.getMediaDetails(0).call())
    print(sort_contract.functions.getMediaDetails(1).call())

# function to wait for a transaction to be part of a block
def waitForTransaction(tx_hash1):
    receipt1 = w3.eth.getTransactionReceipt(tx_hash1)
    while ((receipt1 is None)) : 
        print(receipt1)
        time.sleep(1)
        receipt1 = w3.eth.getTransactionReceipt(tx_hash1)
    print(receipt1)
    if receipt1 is not None:
        print("media:{0}".format(receipt1['gasUsed']))

print("Starting Transaction Submission")
# registering a user as Creator
tx_hash1 = sendRegisterTransaction(False, False, w3, sort_contract)
waitForTransaction(tx_hash1)

# registering a user as Consumer(Individual)
tx_hash1 = sendRegisterTransaction(True, False, w3_1, sort_contract1)
waitForTransaction(tx_hash1)

# registering a user as Consumer(Company)
tx_hash1 = sendRegisterTransaction(True, True, w3_1, sort_contract1)
waitForTransaction(tx_hash1)

#adding a media by the registered user
tx_hash1 = sendAddMediaTransaction()
waitForTransaction(tx_hash1)

tx_hash1 = sendAddMediaTransaction()
waitForTransaction(tx_hash1)

printSendGetTransactions()

# purchasing a media 
tx_hash1 = sendPurchaseMediaTransaction()
waitForTransaction(tx_hash1)

worker.join()