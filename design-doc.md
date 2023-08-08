# lilypad design doc

Services:

 * smart contract
 * resource provider
 * job creator
 * solver
 * mediator
 * directory

## smart contract

#### types

 * `type CID` - bytes32

 * `type ServiceType` - enum
    * resourceProvider
    * jobCreator
    * mediator
    * directory

#### service provider discovery

 * `registerServiceProvider(serviceType, url, metadata)`
    * serviceType `ServiceType`
    * ID = msg._sender
    * url `string`
      * this is the advertised network URL, used by directory and solver
    * metadata `CID`

 * `unregisterServiceProvider(serviceType)`
    * serviceType `ServiceType`
    * ID = msg._sender

 * `listServiceProviders(serviceType) returns []address`
    * serviceType `ServiceType`
    * returns an array of IDs for the given service type
   
 * `getServiceProvider(serviceType, ID) returns (url, metadata)`
    * serviceType `ServiceType`
    * ID `address`
    * url `string`
    * metadata `CID`
    * return the URL and metadata CID for the given service provider

#### deals

 * `agreeDeal(party, dealID, jobOfferID, resourceOfferID, timeout, timeoutDeposit)`
   * party ServiceType
     * this should be resourceProvider that owns the resourceOfferID or jobCreator that owns the jobOfferID
   * dealID `CID`
   * jobOfferID `CID`
   * resourceOfferID `CID`
   * timeout `uint`
     * the upper bounds of time this job can take - TODO: is this in seconds or blocks?
   * timeoutDeposit `uint`
     * the amount of deposit that will be lost if the job takes longer than timeout
     * this must equal msg._value
   
 * `submitResults`
  

 * `cancelDeal`

## solver

The solver will eventually be removed in favour of point to point communication.

For that reason - the solver has 2 distinct sides to it's api, the resource provider side and job creator side.

#### resource provider

 * `broadcastResourceOffer(resourceOfferID)`
   * resourceOfferID `CID`
   * tell everyone connected to this solver about the resource offer

 * `communicateResourceOffer(resourceOfferID, jobCreatorID)`
   * resourceOfferID `CID`
   * jobCreatorID `address`
   * tell one specific job creator about the resource offer

 * `cancelResourceOffer(resourceOfferID)`
   * resourceOfferID `CID`
   * cancel the resource offer


#### job creator

 * `broadcastJobOffer(jobOfferID)`
   * resourceOfferID `CID`

 * `communicateJobOffer(resourceOfferID, jobCreatorID)`
   * resourceOfferID `CID`
   * jobCreatorID `address`




### resource provider

 * register -> smart contract
 * create resource offer -> solver
 * update resource offer -> solver
 * cancel resource offer -> solver
 * hear about match <- solver
 * agree match -> smart contract

### job creator

 * register (*)
 * create job offer
 * update job offer
 * cancel job offer
 * hear about match
 * agree match (*)