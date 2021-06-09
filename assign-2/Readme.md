## CODE DETAILS :

The code consists of the following scripts : 

1. Seed.py : It contains only one function accept_connections() which accepts connection requests from peers and adds them to the peer list and sends them the previous peer list. We can have more than one seed nodes in this network.
			 Seed waits for 1 min to send peer list to partipating nodes. Then broadcasts a "start mining" message to them to indicate the start of mining process.

2. Client.py : The seed nodes have been hardcoded in the script.
               It contains three functions 
		(i) listen_to_connections() : It listens to the incoming blocks from peers and broadcasts the blocks to them(except from the one recieved).
		(ii) accept_connections() : Accepts the connection request from peers and appends them to the socket list and also starts a thread to listen to them.
		(iii) broadcast_messages() : Logic for getting initial peer list from seeds and connecting to atmost 4 peers. Waits for "start" message from seed to start mining blocks and broadcasting them to its peers.

3. AdvClient.py : In addition to performing similar to Client.py, it has logic for selfish mining, i.e., it reveals its found blocks selectively so that honest miners end up wasting hashing power mining on a stale branch.

4. draw_tree.py : To visualize the blockchain tree at any client at any time.


## RUNNING THE CODE :

1. Hard code the seed IP and port number in the "Client.py" and "AdvClient.py" files.
2. Run Seed.py in the format :
	python3 Seed.py <IP> <PORT> 
3. Run Client.py in the format
    python3 Client.py <IP> <PORT> <nodeHashPower in %>
4. Run AdvClient.py in the format
    python3 AdvClient.py <IP> <PORT> <nodeHashPower in %>
5. draw_tree.py has the following dependencies :

Python packages:

```
 sudo python3 -m pip install networkx
 sudo python3 -m pip install pydot
 sudo python3 -m pip install graphviz
 sudo apt-get install graphviz libgraphviz-dev pkg-config
 sudo python3 -m pip install pygraphviz
```

``` python3 draw_tree.py <clientdbname> ```

- Client Db name= "client"+str(port_number%10000)
- AdvClient Db name= "Advclient"+str(port_number%10000)
