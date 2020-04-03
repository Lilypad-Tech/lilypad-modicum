pragma solidity ^0.4.25;

contract Modicum {

    uint256 penaltyRate;
    address owner = msg.sender;
    uint256 reactionDeadline;

    modifier administrative {
        if (msg.sender == owner)
            _;
        else
            revert('You cannot call me!');
        // _;
    }

    enum Architecture {
        amd64,
        armv7
    }

    struct JobCreator {
        address[] trustedMediators;
        uint256 itShouldntBeHere; //If I don't add it, I cannot make array of JC public
    }

    struct ResourceProvider {
        address[] trustedMediators;
        address[] trustedDirectories;
        uint256[] supportedFirstLayers;
        Architecture arch;
        uint256 timePerInstruction;
    }

    struct Mediator {
        Architecture arch;

        uint256 instructionPrice;
        uint256 bandwidthPrice;
        address[] trustedDirectories;
        uint256[] supportedFirstLayers;

        uint256 availabilityValue;

        uint256 verificationCount;
    }

    struct JobOfferPartOne {
        address jobCreator;
        uint256 depositValue;

        uint256 instructionLimit;
        uint256 bandwidthLimit;

        uint256 instructionMaxPrice;
        uint256 bandwidthMaxPrice;

        uint256 completionDeadline;

        uint256 matchIncentive;
    }

    struct JobOfferPartTwo {
        address jobCreator;
        uint256 firstLayerHash;
        uint256 ramLimit;
        uint256 localStorageLimit;
        bytes32 uri;
        address directory;
        uint256 jobHash;
        Architecture arch;
    }

    struct ResourceOffer {

        address resProvider;
        uint256 depositValue;

        uint256 instructionPrice;
        uint256 instructionCap;

        uint256 memoryCap;
        uint256 localStorageCap;

        uint256 bandwidthCap;
        uint256 bandwidthPrice;

        uint256 matchIncentive;

        uint256 verificationCount;
    }

    enum ResultStatus {
        Completed,
        Declined,
        JobDescriptionError,
        JobNotFound,
        MemoryExceeded,
        StorageExceeded,
        InstructionsExceeded,
        BandwidthExceeded,
        ExceptionOccured,
        DirectoryUnavailable
//        LayerSizeExceeded,
//        ResultNotFound
    }

    struct Match {
        uint256 resourceOffer;
        uint256 jobOffer;
        address mediator;
    }

    struct JobResult {
        ResultStatus status;
        bytes32 uri;

        uint256 matchId;

        uint256 hash;

        uint256 instructionCount;
        uint256 bandwidthUsage;

        Reaction reacted;
        uint256 timestamp;
    }

    struct MediatorResult {
        ResultStatus status;
        bytes32 uri;

        uint256 matchId;

        uint256 hash;

        uint256 instructionCount;
        uint256 bandwidthUsage;

        Verdict verdict;
        Party faultyParty;
    }

    enum Party {
        ResourceProvider,
        JobCreator
    }

    enum Verdict {
        ResultNotFound,
        TooMuchCost,
        WrongResults,
        CorrectResults,
        InvalidResultStatus
    }

    enum Reaction {
        Accepted,
        Rejected,
        None
    }

    enum EtherTransferCause {
        PostJobOffer,
        PostResourceOffer,
        CancelJobOffer,
        CancelResOffer,
        Punishment,
        Mediation,
        FinishingJob,
        FinishingResource,
        PostMatch,
        MediatorAvailability
    }

    event Debug(uint64 value);
    event DebugArch(Architecture arch);
    event DebugUint(uint256 value);
    event DebugString(bytes32 str);
    event penaltyRateSet(uint256 penaltyRate);
    event reactionDeadlineSet(uint256 reactionDeadline);

    event ResultReaction(address addr, uint256 resultId, uint256 matchId, uint256 ResultReaction);
    event ResultPosted(address addr, uint256 resultId, uint256 matchId, ResultStatus status, bytes32 uri,
                       uint256 hash, uint256 instructionCount, uint256 bandwidthUsage);
    event Matched(address addr, uint256 matchId, uint256 jobOfferId, uint256 resourceOfferId, address mediator); //the same as job assigned.

    event JobOfferPostedPartOne(uint256 offerId, uint256 ijoid, address addr, uint256 instructionLimit,
                                uint256 bandwidthLimit, uint256 instructionMaxPrice, uint256 bandwidthMaxPrice, uint256 completionDeadline, uint256 deposit, uint256 matchIncentive);

    event JobOfferPostedPartTwo(uint256 offerId, address addr, uint256 hash, uint256 firstLayerHash, bytes32 uri,
                                address directory, Architecture arch, uint256 ramLimit, uint256 localStorageLimit);

    event ResourceOfferPosted(uint256 offerId, address addr, uint256 instructionPrice,
                              uint256 instructionCap, uint256 memoryCap, uint256 localStorageCap,
                              uint256 bandwidthCap, uint256 bandwidthPrice, uint256 deposit,uint256 iroid);

    event JobOfferCanceled(uint256 offerId);
    event ResourceOfferCanceled(uint256 resOfferId);
    event JobAssignedForMediation(address addr, uint256 matchId);

    event MediatorRegistered(address addr, Architecture arch, uint256 instructionPrice, uint256 bandwidthPrice,
                             uint256 availabilityValue, uint256 verificationCount);

    event MediatorAddedSupportedFirstLayer(address addr, uint256 firstLayerHash);

    event ResourceProviderRegistered(address addr, Architecture arch, uint256 timePerInstruction, uint256 penaltyRate);
    event ResourceProviderAddedTrustedMediator(address addr, address mediator);
    event JobCreatorRegistered(address addr, uint256 penaltyRate);
    event JobCreatorAddedTrustedMediator(address addr, address mediator);
    event MediatorAddedTrustedDirectory(address addr, address directory);
    event ResourceProviderAddedTrustedDirectory(address addr, address directory);
    event ResourceProviderAddedSupportedFirstLayer(address addr, uint256 firstLayer);

    event MediationResultPosted(uint256 matchId, address addr, uint256 result, Party faultyParty, Verdict verdict, ResultStatus status,
                                bytes32 uri, uint256 hash, uint256 instructionCount, uint256 mediationCost);

    event MatchClosed(uint256 matchId, uint256 cost);

    event EtherTransferred(address _from, address to, uint256 value, EtherTransferCause cause);

    mapping(address => Mediator) public mediators;
    // mapping(uint256 => address) public mediator_index;
    // uint mediator_count;
    // address[] mediator_index;

    mapping(address => ResourceProvider) resourceProviders;
    mapping(address => JobCreator) jobCreators;

    ResourceOffer[] resourceOffers;
    uint256 joIndex = 1;
    mapping(uint256 => JobOfferPartOne) jobOffersPartOne;
    mapping(uint256 => JobOfferPartTwo) jobOffersPartTwo;
    mapping(address => mapping(uint256 => uint256)) findJOIndex; // findJOIndex[addressOfJC][jcInternalOfferId]

    Match[] matches;
    JobResult[] results;
    MediatorResult[] mediatorResults;

    mapping(uint256 => bool) jobOfferPartOnePosted;
    mapping(uint256 => bool) jobOfferPartTwoPosted;

    mapping(uint256 => bool) mediationRequested;
    mapping(uint256 => bool) mediated;
    mapping(uint256 => uint256) matchToResult;
    mapping(uint256 => bool) resultAvailable;

    mapping(uint256 => bool) jobOfferMatched;
    mapping(uint256 => bool) resOfferMatched;

    mapping(uint256 => bool) isJobOfferCanceled;
    mapping(uint256 => bool) isResOfferCanceled;
    mapping(uint256 => bool) isMatchClosed;

    function () external payable {
        revert("Why are you calling me?");
    }

    function test(uint256 value) public{
      require(value > 0,
      "This should be greater than 0");
      emit DebugUint(value);
    }

    function check(Architecture arch) public{
        //Architecture arch = Architecture.amd64;
        emit Debug(5);
        emit DebugArch(arch);
        emit DebugUint(1);
    }

    function setPenaltyRate(uint256 _penaltyRate) public administrative {
        penaltyRate = _penaltyRate;
        emit penaltyRateSet(penaltyRate);
    }

    function setReactionDeadline(uint256 _reactionDeadline) public administrative {
        reactionDeadline = _reactionDeadline;
        emit reactionDeadlineSet(_reactionDeadline);
    }


    function registerMediator(
        Architecture arch,
        uint256 instructionPrice,
        uint256 bandwidthPrice,
        uint256 availabilityValue,
        uint256 verificationCount
    ) public {
        address[] memory trustedDirectories;
        uint256[] memory supportedFirstLayers;
        mediators[msg.sender] = Mediator({
            arch: arch,
            instructionPrice: instructionPrice,
            supportedFirstLayers: supportedFirstLayers,
            bandwidthPrice: bandwidthPrice,
            trustedDirectories: trustedDirectories,
            availabilityValue: availabilityValue,
            verificationCount: verificationCount
            });
        emit MediatorRegistered(msg.sender,
            arch,
            instructionPrice,
            bandwidthPrice,
            availabilityValue,
            verificationCount
        );
    }

    function mediatorAddTrustedDirectory(address directory) public {
        mediators[msg.sender].trustedDirectories.push(directory);
        emit MediatorAddedTrustedDirectory(msg.sender, directory);
    }

    function mediatorAddSupportedFirstLayer(uint256 firstLayerHash) public {
        mediators[msg.sender].supportedFirstLayers.push(firstLayerHash);
        emit MediatorAddedSupportedFirstLayer(msg.sender, firstLayerHash);
    }

    // function getMediatorTrustedDirectories(address mediator) public view returns (address[] memory) {
    //     return mediators[mediator].trustedDirectories;
    // }

    function registerResourceProvider(
        Architecture arch,
        uint256 timePerInstruction
    ) public {
        address[] memory trustedMediators;
        address[] memory trustedDirectories;
        uint256[] memory supportedFirstLayers;
        resourceProviders[msg.sender] = ResourceProvider({
            trustedMediators: trustedMediators,
            supportedFirstLayers: supportedFirstLayers,
            arch: arch,
            timePerInstruction: timePerInstruction,
            trustedDirectories: trustedDirectories
        });
        emit ResourceProviderRegistered(msg.sender,
            arch,
            timePerInstruction,
            penaltyRate
        );
    }

    function resourceProviderAddTrustedMediator(address mediator) public {
        resourceProviders[msg.sender].trustedMediators.push(mediator);
        emit ResourceProviderAddedTrustedMediator(msg.sender, mediator);
    }

    function resourceProviderAddTrustedDirectory(address directory) public {
        resourceProviders[msg.sender].trustedDirectories.push(directory);
        emit ResourceProviderAddedTrustedDirectory(msg.sender, directory);
    }

    function resourceProviderAddSupportedFirstLayer(uint256 firstLayerHash) public {
        resourceProviders[msg.sender].supportedFirstLayers.push(firstLayerHash);
        emit ResourceProviderAddedSupportedFirstLayer(msg.sender, firstLayerHash);
    }

    // function getResourceProviderTrustedMediators(address rp) public view returns (address[] memory) {
    //     return resourceProviders[rp].trustedMediators;
    // }

    // function getResourceProviderTrustedDirectories(address rp) public view returns(address[] memory) {
    //     return resourceProviders[rp].trustedDirectories;
    // }

    function registerJobCreator(
    ) public {
        address[] memory trustedMediators;
        jobCreators[msg.sender] = JobCreator({
            trustedMediators: trustedMediators,
            itShouldntBeHere: 0
        });
        emit JobCreatorRegistered(msg.sender, penaltyRate);
    }

    // function getJobCreatorTrustedMediators(address jc) public view returns (address[] memory) {
    //     return jobCreators[jc].trustedMediators;
    // }
    function jobCreatorAddTrustedMediator(address mediator) public {
        jobCreators[msg.sender].trustedMediators.push(mediator);
        emit JobCreatorAddedTrustedMediator(msg.sender, mediator);
    }

    function postResOffer(
        uint256 instructionPrice,
        uint256 instructionCap,

        uint256 memoryCap,
        uint256 localStorageCap,

        uint256 bandwidthCap,
        uint256 bandwidthPrice,

        uint256 matchIncentive,

        uint256 verificationCount,

        uint256 misc
    ) public payable {
        // require(resourceProviders[msg.sender].trustedMediators.length != 0,
        //     "You are not registered as a ResourceProvider");

        if (resourceProviders[msg.sender].trustedMediators.length == 0){
            emit DebugString("trustedMediators==0");
        }

        uint256 depositValue = (instructionPrice * instructionCap +
            bandwidthCap * bandwidthPrice) * penaltyRate;

        if (msg.value <= depositValue){
            emit DebugString("msg.value <= depositValue");
            emit DebugUint(msg.value);
            emit DebugUint(depositValue);
        }

        // require(msg.value >= depositValue,
        //    "You need to deposit more money to offer this resource");

        uint256 index = resourceOffers.push(ResourceOffer({
            resProvider: msg.sender,
            instructionPrice: instructionPrice,
            instructionCap: instructionCap,
            memoryCap: memoryCap,
            localStorageCap: localStorageCap,
            bandwidthCap: bandwidthCap,
            bandwidthPrice: bandwidthPrice,
            depositValue: msg.value,
            matchIncentive: matchIncentive,
            verificationCount: verificationCount
            })) - 1;

        uint256 iroid = misc;
        emit ResourceOfferPosted(index,

            msg.sender,

            instructionPrice,
            instructionCap,

            memoryCap,
            localStorageCap,

            bandwidthCap,
            bandwidthPrice,

            msg.value,

            iroid
        );

        emit EtherTransferred(msg.sender, address(this), msg.value, EtherTransferCause.PostResourceOffer);
    }

    function postJobOfferPartOne(
        uint256 ijoid,
        uint256 instructionLimit,
        uint256 bandwidthLimit,
        uint256 instructionMaxPrice,
        uint256 bandwidthMaxPrice,
        uint256 completionDeadline,
        uint256 matchIncentive
    ) public payable {
        // require(jobCreators[msg.sender].trustedMediators.length != 0,
        //    "You are not registered as a JobCreator");

        // require(msg.value >= (instructionLimit * instructionMaxPrice +
        //    bandwidthLimit * bandwidthMaxPrice) * penaltyRate,
        //    "You need to deposit more money to request this job.");

        uint256 index = findJOIndex[msg.sender][ijoid];
        if (index == 0) {
            index = joIndex;
            joIndex++;
            findJOIndex[msg.sender][ijoid] = index;
        }

        // require(jobOfferPartOnePosted[index] == false, "You have already posted a part one for this ijoid.");

        JobOfferPartOne memory joPOne = JobOfferPartOne({
            jobCreator: msg.sender,
            depositValue: msg.value,
            instructionLimit: instructionLimit,
            bandwidthLimit: bandwidthLimit,
            instructionMaxPrice: instructionMaxPrice,
            bandwidthMaxPrice: bandwidthMaxPrice,
            completionDeadline: completionDeadline,
            matchIncentive: matchIncentive
        });

        jobOffersPartOne[index] = joPOne;
        jobOfferPartOnePosted[index] = true;

        emit JobOfferPostedPartOne(
            index,
            ijoid,
            msg.sender,
            instructionLimit,
            bandwidthLimit,
            instructionMaxPrice,
            bandwidthMaxPrice,
            completionDeadline,
            msg.value,
            matchIncentive
        );

        emit EtherTransferred(msg.sender, address(this), msg.value, EtherTransferCause.PostJobOffer);
    }

    function postJobOfferPartTwo(
        uint256 ijoid,
        uint256 firstLayerHash,
        uint256 ramLimit,
        uint256 localStorageLimit,
        bytes32 uri,
        address directory,
        uint256 jobHash,
        Architecture arch
    ) public {

        // require(jobCreators[msg.sender].trustedMediators.length != 0,
        //    "You are not registered as a JobCreator");

        uint256 index = findJOIndex[msg.sender][ijoid];
        if (index == 0) {
            index = joIndex;
            joIndex++;
            findJOIndex[msg.sender][ijoid] = index;
        }

        // require(jobOfferPartTwoPosted[index] == false, "You have already posted a part two for this ijoid.");

        JobOfferPartTwo memory joPTwo = JobOfferPartTwo({
            jobCreator: msg.sender,
            firstLayerHash: firstLayerHash,
            ramLimit: ramLimit,
            localStorageLimit: localStorageLimit,
            uri: uri,
            directory: directory,
            jobHash: jobHash,
            arch: arch
        });

        jobOffersPartTwo[index] = joPTwo;
        jobOfferPartTwoPosted[index] = true;

        emit JobOfferPostedPartTwo(
            index,
            msg.sender,
            jobHash,
            firstLayerHash,
            uri,
            directory,
            arch,
            ramLimit,
            localStorageLimit
        );
    }

    function cancelJobOffer(uint256 offerId) public {
        // require(jobOffersPartOne[offerId].jobCreator == msg.sender, "This offer is not yours.");
        // require(jobOfferMatched[offerId] == false, "You cannot cancel a jop which is running.");

        //msg.sender.transfer(jobOffersPartOne[offerId].depositValue);
        jobOffersPartOne[offerId].depositValue = 0;

        isJobOfferCanceled[offerId] = true;

        emit JobOfferCanceled(offerId);
        emit EtherTransferred(address(this), msg.sender, jobOffersPartOne[offerId].depositValue, EtherTransferCause.CancelJobOffer);
    }

    function cancelResOffer(uint256 offerId) public {
        // require(resourceOffers[offerId].resProvider == msg.sender, "This offer is not yours.");
        // require(resOfferMatched[offerId] == false, "You cannot cancel a jop which is running.");

        //msg.sender.transfer(resourceOffers[offerId].depositValue);
        resourceOffers[offerId].depositValue = 0;

        isResOfferCanceled[offerId] = true;

        emit ResourceOfferCanceled(offerId);
        emit EtherTransferred(address(this), msg.sender, resourceOffers[offerId].depositValue, EtherTransferCause.CancelResOffer);
    }

    function postMatch(
        uint256 jobOfferId,
        uint256 resourceOfferId,
        address mediator
    ) public returns (uint256){
        // require(solvers[msg.sender] == true, "You are not a trusted solver");
        // require(isJobOfferCanceled[jobOfferId] == false,
        //     "Job offer is already canceled.");

        // require(isResOfferCanceled[resourceOfferId] == false,
        //     "Resource offer is already canceled.");

        // require(jobOfferMatched[jobOfferId] == false,
        //     "Job offer is already matched");

        // require(resOfferMatched[resourceOfferId] == false,
        //     "Resource offer is already matched");

        // require(jobOfferPartOnePosted[jobOfferId] == true,
        //     "The job offer was not completed");
        // require(jobOfferPartTwoPosted[jobOfferId] == true,
        //     "The job offer was not completed");
        // bool RPTrustM = false;
        // bool JCTrustM = false;
        // bool RPTrustD = false;
        // bool MTrustD  = false;
        // bool RPSupportFirstLayer = false;
        // bool MSupportFirstLayer = false;

        // uint i = 0;

        // for (i = 0; i < resourceProviders[resourceOffers[resourceOfferId].resProvider].trustedMediators.length; i++)
        //     if (resourceProviders[resourceOffers[resourceOfferId].resProvider].trustedMediators[i] == mediator)
        //         RPTrustM = true;

        // for (i = 0; i < jobCreators[jobOffersPartOne[jobOfferId].jobCreator].trustedMediators.length; i++)
        //     if (jobCreators[jobOffersPartOne[jobOfferId].jobCreator].trustedMediators[i] == mediator)
        //         JCTrustM = true;

        // for (i = 0; i < resourceProviders[resourceOffers[resourceOfferId].resProvider].trustedDirectories.length; i++)
        //     if (resourceProviders[resourceOffers[resourceOfferId].resProvider].trustedDirectories[i] == jobOffersPartTwo[jobOfferId].directory)
        //         RPTrustD = true;

        // for (i = 0; i < mediators[mediator].trustedDirectories.length; i++)
        //     if (mediators[mediator].trustedDirectories[i] == jobOffersPartTwo[jobOfferId].directory)
        //         RPTrustD = true;

        // for (i = 0; i < resourceProviders[resourceOffers[resourceOfferId].resProvider].supportedFirstLayers.length; i++)
        //     if (resourceProviders[resourceOffers[resourceOfferId].resProvider].supportedFirstLayers[i] == jobOffersPartTwo[jobOfferId].firstLayerHash)
        //         RPSupportFirstLayer = true;

        // for (i = 0; i < mediators[mediator].supportedFirstLayers.length; i++)
        //     if (mediators[mediator].supportedFirstLayers[i] == jobOffersPartTwo[jobOfferId].firstLayerHash)
        //         MSupportFirstLayer = true;


        // require(
        //     resourceOffers[resourceOfferId].instructionCap >= jobOffersPartOne[jobOfferId].instructionLimit &&
        //     resourceOffers[resourceOfferId].memoryCap >= jobOffersPartTwo[jobOfferId].ramLimit &&
        //     resourceOffers[resourceOfferId].localStorageCap >= jobOffersPartTwo[jobOfferId].localStorageLimit &&
        //     resourceOffers[resourceOfferId].instructionPrice <= jobOffersPartOne[jobOfferId].instructionMaxPrice &&
        //     resourceProviders[resourceOffers[resourceOfferId].resProvider].arch == jobOffersPartTwo[jobOfferId].arch && mediators[mediator].arch == resourceProviders[resourceOffers[resourceOfferId].resProvider].arch &&
        //     resourceOffers[resourceOfferId].verificationCount <= mediators[mediator].verificationCount &&
        //     now + resourceProviders[resourceOffers[resourceOfferId].resProvider].timePerInstruction * jobOffersPartOne[jobOfferId].instructionLimit <= jobOffersPartOne[jobOfferId].completionDeadline &&
        //     RPTrustD && RPTrustM && JCTrustM && MTrustD && RPSupportFirstLayer && MSupportFirstLayer,
        //     "The offers cannot be matched"
        // );


        uint256 index = matches.push(Match({
            resourceOffer: resourceOfferId,
            jobOffer: jobOfferId,
            mediator: mediator
        })) - 1;

        jobOfferMatched[jobOfferId] = true;
        resOfferMatched[resourceOfferId] = true;

        uint256 matchIncentive = jobOffersPartOne[jobOfferId].matchIncentive +
                resourceOffers[resourceOfferId].matchIncentive;

        //msg.sender.transfer(matchIncentive);

        emit EtherTransferred(address(this), msg.sender, matchIncentive, EtherTransferCause.PostMatch);

        emit Matched(msg.sender, index, jobOfferId, resourceOfferId, mediator);

        return index;
    }

    function postResult(
        uint256 matchId,
        uint256 jobOfferId,
        ResultStatus status,
        bytes32 uri,
        uint256 hash,
        uint256 instructionCount,
        uint256 bandwidthUsage
    ) public returns (uint256) {
        // require (resourceOffers[matches[matchId].resourceOffer].resProvider == msg.sender,
        //     "You are not supposed to publish result for this match.");

        // require(isMatchClosed[matchId] == false,
        //     "This match is already closed.");

        uint256 index = results.push(JobResult({
            status: status,
            matchId: matchId,
            uri: uri,
            instructionCount: instructionCount,
            bandwidthUsage: bandwidthUsage,
            hash: hash,
            reacted: Reaction.None,
            timestamp: now
            })) - 1;

        matchToResult[matchId] = index;
        resultAvailable[matchId] = true;

        emit ResultPosted(
            msg.sender,
            index,
            matchId,
            status,
            uri,
            hash,
            instructionCount,
            bandwidthUsage
        );

        return index;
    }

    function rejectResult(uint256 resultId, uint256 jobOfferId) public {
        // require(jobOffersPartOne[matches[results[resultId].matchId].jobOffer].jobCreator == msg.sender,
        //     "You cannot reject a result which is not yours.");
        // require(results[resultId].reacted == Reaction.None,
        //     "You have already reacted to this result");
        // require(isMatchClosed[results[resultId].matchId] == false,
        //     "This match is already closed.");

        results[resultId].reacted = Reaction.Rejected;
        mediationRequested[results[resultId].matchId] = true;

        emit ResultReaction(msg.sender, resultId,results[resultId].matchId,  1);

        emit DebugString("result rejected");

        emit JobAssignedForMediation(msg.sender, results[resultId].matchId);
    }

    function acceptResult(uint256 resultId, uint256 jobOfferId) public returns (uint256) {
        //require(jobOffers[matches[results[resultId].matchId].jobOffer].jobCreator == msg.sender ||
        //    (resourceOffers[matches[results[resultId].matchId].resourceOffer].resProvider == msg.sender && results[resultId].timestamp + reactionDeadline > now),
        //    "You cannot reject a result which is not yours or deadline has not been missed yet.");
        //require(results[resultId].reacted == Reaction.None,
        //    "You have already reacted to this result");
        //require(isMatchClosed[results[resultId].matchId] == false,
        //    "This match is already closed.");

        results[resultId].reacted = Reaction.Accepted;

        emit ResultReaction(msg.sender, resultId,results[resultId].matchId,  0);

        emit DebugString("result accepted");

        return close(results[resultId].matchId);

    }


    function postMediationResult(
        uint256 matchId,
        uint256 jobOfferId,
        ResultStatus status,
        bytes32 uri,

        uint256 hash,

        uint256 instructionCount,
        uint256 bandwidthUsage,

        Verdict verdict,
        Party faultyParty
    ) public returns (Party) {
        // require(matches[matchId].mediator == msg.sender, "You are not this job's mediator");
        // require(mediationRequested[matchId] == true, "JC did not request mediation for this match.");
        // require(mediated[matchId] == false, "You have already mediated this match.");

        mediated[matchId] = true;

        uint256 index = mediatorResults.push(MediatorResult({
            status: status,
            uri: uri,
            matchId: matchId,
            hash: hash,
            instructionCount: instructionCount,
            bandwidthUsage: bandwidthUsage,
            verdict: verdict,
            faultyParty: faultyParty
        })) - 1;

        uint256 cost = (instructionCount * mediators[msg.sender].instructionPrice +
                        bandwidthUsage * mediators[msg.sender].bandwidthPrice) *
                        resourceOffers[matches[matchId].resourceOffer].verificationCount;

        // emit MediationResultPosted( index, faultyParty, verdict, matchId,
        //                             status, uri, hash, instructionCount, bandwidthUsage, cost);

        emit MediationResultPosted(matchId, msg.sender, index, faultyParty, verdict, status, uri, hash, instructionCount, cost);

        punish(matchId, faultyParty);
        //msg.sender.transfer(cost);
        emit EtherTransferred(address(this), msg.sender, cost, EtherTransferCause.Mediation);
        emit MatchClosed(matchId, cost);
        return faultyParty;
    }

    function punish(uint256 matchId, Party faultyParty) private {
        // require(isMatchClosed[matchId] == false, "This match is already closed.");
        isMatchClosed[matchId] = true;

        ResourceOffer memory ro = resourceOffers[matches[matchId].resourceOffer];
        JobOfferPartOne memory jo = jobOffersPartOne[matches[matchId].jobOffer];

        uint256 roDeposit = ro.depositValue;
        uint256 joDeposit = jo.depositValue;

        jo.depositValue = 0;
        ro.depositValue = 0;

        uint256 joValue = jo.bandwidthLimit * jo.bandwidthMaxPrice + jo.instructionLimit * jo.instructionMaxPrice;
        uint256 roValue = ro.bandwidthCap * ro.bandwidthPrice + ro.instructionCap * ro.instructionPrice;

        if (faultyParty == Party.JobCreator) {

            //address(uint160(ro.resProvider)).transfer(roDeposit + roValue);
            emit EtherTransferred(address(this), ro.resProvider, roDeposit + roValue, EtherTransferCause.Punishment);

        } else if (faultyParty == Party.ResourceProvider) {

            //address(uint160(jo.jobCreator)).transfer(joDeposit + joValue);
            emit EtherTransferred(address(this), jo.jobCreator, joDeposit + joValue, EtherTransferCause.Punishment);
        }
    }

    function close(uint256 matchId) private returns (uint256) {
        //require(results[matchToResult[matchId]].reacted == Reaction.Accepted,
        //    "The job is not done yet.");

        JobResult memory r = results[matchToResult[matchId]];
        ResourceOffer memory ro = resourceOffers[matches[matchId].resourceOffer];
        JobOfferPartOne memory jo = jobOffersPartOne[matches[matchId].jobOffer];
        address m = matches[matchId].mediator;

        //require(isMatchClosed[matchId] == false, "This match is already closed.");
        isMatchClosed[matchId] = true;

        uint256 cost = r.instructionCount * ro.instructionPrice +
            r.bandwidthUsage * ro.bandwidthPrice;

        uint256 mediatorAvailabilityIncentive = mediators[m].availabilityValue;

        uint256 jo_deposit = jo.depositValue;
        uint256 ro_deposit = ro.depositValue;

        jo.depositValue = 0;
        ro.depositValue = 0;

        //address(uint160(jo.jobCreator)).transfer(jo_deposit - cost - jo.matchIncentive - mediatorAvailabilityIncentive);
        //address(uint160(ro.resProvider)).transfer(jo_deposit + cost - ro.matchIncentive - mediatorAvailabilityIncentive);
        //address(uint160(m)).transfer(2 * mediatorAvailabilityIncentive);


        emit MatchClosed(matchId, cost);
        emit EtherTransferred(address(this), jo.jobCreator, jo_deposit - cost, EtherTransferCause.FinishingJob);
        emit EtherTransferred(address(this), ro.resProvider, ro_deposit + cost, EtherTransferCause.FinishingResource);
        emit EtherTransferred(address(this), m, 2 * mediatorAvailabilityIncentive, EtherTransferCause.MediatorAvailability);

        return cost;
    }

    function timeout(uint256 matchId, uint256 jobOfferId) public {
        // require(jobOffersPartOne[matches[matchId].jobOffer].jobCreator == msg.sender,
        //     "You cannot make a timeout on this offer");
        // require(jobOffersPartOne[matches[matchId].jobOffer].completionDeadline < now,
        //     "RP has more time to finish this job");
        // require(isMatchClosed[matchId] == false,
        //     "This match is closed.");

        punish(matchId, Party.ResourceProvider);
    }

    function receiveValues(address toAccount, uint256 amount) public administrative {
        address(uint160(toAccount)).transfer(amount);
    }

}
