

## CODE DETAILS :

The code consists of two scripts: 

1. seed.py : It contains only one function accept_connections() which accepts connection requests from peers and adds them to the peer list and sends them the previous peer list. We can have more than one seed nodes in this network

2. client.py : The seed nodes have been hardcoded in the script.
               It contains three functions 
		(i)listen_to_connections() : It listens to the incoming messages from peers and broadcasts the messages to them(except from the one recieved).
		(ii)accept_connections() : Accepts the connection request from peers and appends them to the socket list also starting a thread to listen to them
		(iii) broadcast_messages() :Logic for getting initial peer list from seeds and broadcasting the messages to them. The peers will get the messages generated after it joins.




## RUNNING THE CODE:
(i) Hard code the seed IP and port number in the "client.py" file
. We can take one or more seed nodes
(ii) Run seed.py in the format :
     python3 seed.py <IP> <PORT>
(iii) Run client.py in the format
     python3 client.py <IP> <PORT>
