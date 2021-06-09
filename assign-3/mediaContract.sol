pragma solidity ^0.4.24;
pragma experimental ABIEncoderV2;

contract mediaContract {

    /*Data structure for user-consumer(individual or company) or creator*/
	struct userInfo {
	    uint userId;
		address addr;
	  	bool isConsumer;
	  	bool isCompany;
		// purchased media's IDs and their corresponding URLs
		mapping(uint => bytes32) medias;
		uint[] mediaIds;
	}
	mapping(uint => userInfo) public users;
	uint[] public userIds;

    /*Data structure for Media*/
	struct mediaInfo {
	    uint mediaId;
		bytes32 mediaDesc;
		address owner;
		uint ownerId;
		uint costIndividual;
		uint costCompany;
		address[] stakeholders;
		uint[] percentages;
	}
	mapping(uint => mediaInfo) mediaLicenses;
	uint[] public mediaIds;

	uint userlen;
	uint medialen;

	// event produced after a user with address addr is registered with ID id
	event UserRegistered(address addr, uint id);

	// event produced to notify a creator with ID creatorId that a media with media ID mediaId is purchased by consumer with ID userId and address userAddr
	event MediaPurchased(uint creatorId, uint mediaId, uint userId, address userAddr);

	// event to notify a consumer with ID userId that media link for media with ID mediaId is ready
	event MediaLinkCreated(uint userId, uint mediaId);

	/*Register the user in the smart contract (DAPP). This function is accessible to
    both creator and consumer*/
	function registerUser(bool isConsumer, bool isCompany) public returns(uint){
		uint id = userlen;
        userInfo storage newUser = users[id];
		newUser.userId = id;
		newUser.addr = msg.sender;
        newUser.isConsumer = isConsumer;
        newUser.isCompany = isCompany;
		userlen = userlen+1;
		emit UserRegistered(msg.sender, id);
		return id;
    }
	// returns true if addr is a creator
	function isCreator(address addr) public returns (bool){
		uint len = userlen;
		uint i;
		bool ret = false;
		for(i = 0; i<len; i++){
			if(users[i].addr == addr && users[i].isConsumer == false){
				ret = true;
				break;
			}
		}
		return ret;
	}

	// returns true if addr is a individual consumer
	function isIndividual(address addr) public returns (bool){
		uint len = userlen;
		uint i;
		bool ret = false;
		for(i = 0; i<len; i++){
			if(users[i].addr == addr && users[i].isConsumer == true && users[i].isCompany == false){
				ret = true;
				break;
			}
		}
		return ret;
	}

	// returns true if addr is a company consumer
	function isCompany(address addr) public returns (bool){
		uint len = userlen;
		uint i;
		bool ret = false;
		for(i = 0; i<len; i++){
			if(users[i].addr == addr && users[i].isConsumer == true && users[i].isCompany == true){
				ret = true;
				break;
			}
		}
		return ret;
	}

	// function to get a user details with ID id
	function getUser(uint id) public returns(uint _userId, address addr, bool _isConsumer, bool _isCompany){
		return (users[id].userId, users[id].addr, users[id].isConsumer, users[id].isCompany);
	}

    /*Add the media to smart contracts with the list of stakeholders, the owner(creator)
    info, stakeholder shares, the price they are offering for an individual and a company, etc. This function should be accessible to the creator only*/
    function addMedia(uint userId, bytes32 mediaDesc, uint costCompany, uint costIndividual, address[] stakeholders, uint[] percentages) public returns(uint){
		require(isCreator(msg.sender) == true, "addMedia is only accessible by creators");
		uint id1 = medialen;
        mediaInfo storage newMedia = mediaLicenses[id1];
		newMedia.mediaId = id1;
		newMedia.mediaDesc = mediaDesc;
		newMedia.owner = msg.sender;
		newMedia.ownerId = userId;
        newMedia.costCompany = costCompany;
        newMedia.costIndividual = costIndividual;
		newMedia.stakeholders = stakeholders;
		newMedia.percentages = percentages;
		medialen = id1+1;
    }

	// function to get media details of media with ID id
	function getMediaDetails(uint id) public returns(uint _id, bytes32 desc, address owner, uint costCompany, uint costIndividual, address[] stakeholders, uint[] percentages){
		return (mediaLicenses[id].mediaId, mediaLicenses[id].mediaDesc, mediaLicenses[id].owner, mediaLicenses[id].costCompany, mediaLicenses[id].costIndividual, mediaLicenses[id].stakeholders, mediaLicenses[id].percentages);
	}

    /*It transfers the purchase amount from the consumer to the creator account.
    Please make sure to distinguish between the individual consumer and the company while charging the amount. Also, this function should ensure the availability of balance in the consumer’s account. This function should be exposed to the consumer only*/
    // purchase request of mediaId by userId
	function purchaseMedia(uint mediaId, uint userId) public payable{
		if(users[userId].isCompany == true){
			require(msg.value == mediaLicenses[mediaId].costCompany, "amount of ether insufficient or more(individual)");
		} else if(users[userId].isCompany == false && users[userId].isConsumer == true){
			require(msg.value == mediaLicenses[mediaId].costIndividual, "amount of ether insufficient or more(company)");
		} else{
			//user is not registered as a consumer
			revert("not a registered user");
		}
		uint len = mediaLicenses[mediaId].stakeholders.length;
		uint i;
		uint percent;
		uint owner_share = 100;
		for(i = 0; i<len; i++){
			percent = mediaLicenses[mediaId].percentages[i];
			mediaLicenses[mediaId].stakeholders[i].transfer((msg.value*percent)/100);
			owner_share = owner_share - percent;
		}
		mediaLicenses[mediaId].owner.transfer((msg.value*owner_share)/100);
		emit MediaPurchased(mediaLicenses[mediaId].ownerId, mediaId, userId, users[userId].addr);
    }


    /*Randomly generate the url here and send it to the consumer after encrypting it with the consumer’s public key. Before sending the url to the consumer,you should ensure that the payment made by him is confirmed (payment transaction is encapsulated in some block). This function should be accessible to the creator only*/
    function sendMediaLink(bytes32 url, uint userId, uint mediaId) public {
    	require(isCreator(msg.sender) == true, "sendMediaLink is accessible by creators only.");
		users[userId].medias[mediaId] = url;
		users[userId].mediaIds.push(mediaId);
		emit MediaLinkCreated(userId, mediaId);
    }

	function getMediaLink(uint mediaId, uint userId) public returns(bytes32) {
		require(users[userId].addr == msg.sender, "url to be accessed by the rightful owner only");
		return users[userId].medias[mediaId];
	}

	/*Get all consumer details */
    function getConsumer() public returns (uint[],address[],bool[]){
        require(isCreator(msg.sender) == true, "getConsumer is only accessible by creators");
        uint conslen = 0;
        for(uint i = 0; i<userlen; i++)
		{
			userInfo storage userin = users[i];
			if(userin.isConsumer == true )
			{
				conslen++;
			}
		}
        if (conslen == 0)
            return ( new uint[](1),new address[](1),new bool[](1));
        uint[] memory consumerids = new uint[](conslen);
        address[] memory addresses = new address[](conslen);
        bool[] memory iscompany = new bool[](conslen);
        uint j = 0;
        for( i = 0; i<userlen; i++)
		{
			userInfo storage userinfo = users[i];
			if(userinfo.isConsumer == true )
			{
				consumerids[j] = userinfo.userId;
				addresses[j] = userinfo.addr;
				iscompany[j] = userinfo.isCompany;
				j++;
			}
		}
        return (consumerids,addresses,iscompany) ;
    }
	function getCreator() public returns (uint[],address[],bool[]){
		require(isCompany(msg.sender) == true || isIndividual(msg.sender) == true, "getCreator is only accessible by consumers");
		uint conslen = 0;
		for( uint i = 0; i<userlen; i++)
		{
			userInfo storage userin = users[i];
			if(userin.isConsumer == false )
			{
				conslen++;
			}
		}
		if (conslen == 0)
			return ( new uint[](1),new address[](1),new bool[](1));
		uint[] memory consumerids = new uint[](conslen);
		address[] memory addresses = new address[](conslen);
		bool[] memory iscompany = new bool[](conslen);
		uint j = 0;
		for( i = 0; i<userlen; i++)
		{
			userInfo storage userinfo = users[i];
			if(userinfo.isConsumer == false )
			{
				consumerids[j] = userinfo.userId;
				addresses[j] = userinfo.addr;
				iscompany[j] = userinfo.isCompany;
				j++;
			}
		}
		return (consumerids,addresses,iscompany);
    }


	function bytes32ToString(bytes32 x) public view returns (string) {
		bytes memory bytesString = new bytes(32);
		uint charCount = 0;
		for (uint j = 0; j < 32; j++) {
			byte char = byte(bytes32(uint(x) * 2 ** (8 * j)));
			if (char != 0) {
				bytesString[charCount] = char;
				charCount++;
			}
		}
		bytes memory bytesStringTrimmed = new bytes(charCount);
		for (j = 0; j < charCount; j++) {
			bytesStringTrimmed[j] = bytesString[j];
		}
		return string(bytesStringTrimmed);
    }

	 /**getter to fetch the available media details for sell*/
     function getMedia(uint userid) public returns (uint[],string[]){
		require(isCompany(msg.sender) == true || isIndividual(msg.sender) == true, "getMedia is only accessible by consumers");
        uint i;
		uint j;
		uint len = 0;
		for(i = 0;i < medialen;i++)
		{
			userInfo storage userin = users[userid];
			bool present = false;
			for(j = 0; j < userin.mediaIds.length; j++)
			{
				if(userin.mediaIds[j] == mediaLicenses[i].mediaId){
					present = true;
					break;
				}
			}
			if(present == false){
				len++;
			}
		}
		uint[] memory mediaids = new uint[](len);
        bytes32[] memory descriptions = new bytes32[](len); //mediaIds.length
        string[] memory descstring = new string[](len);
		uint k = 0;
		for(i = 0;i < medialen;i++)
		{
			userin = users[userid];
			present = false;
			for(j = 0; j < userin.mediaIds.length; j++)
			{
				if(userin.mediaIds[j] == mediaLicenses[i].mediaId){
					present = true;
					break;
				}
			}
			if(present == false){
				mediaInfo storage media1 = mediaLicenses[i];
				mediaids[k] = media1.mediaId;
				descriptions[k] = media1.mediaDesc;
				descstring[k] = bytes32ToString(descriptions[k]);
				k = k+1;
			}
		}
      return (mediaids,descstring);
    }
}