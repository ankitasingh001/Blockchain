## OBJECTIVE

Building a solidity smart contract for distribution of licensed media on Ethereum private
network with at least 3 different geth instance, each acting as a user.

## RUNNING THE CODE


**Note:** Replace all hardcoded values in the following scripts before use.
mediaContract.sol is the smart contract

1) run the 3 geth nodes using the following commands

	sh openhelper{n}.sh
	n=1,2,3

2) deploy the contract using:

	``` python3 deployContract.py ```

3) hardcode the media url in:

	``` vi contractAddressList1 ```

4) send the transactions using:

	``` python3 sendTransaction.py ```

*PS: start the miners to accept transactions.*


