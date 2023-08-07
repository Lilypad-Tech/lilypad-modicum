# lilypad design doc

Decentralized, two sided market place for compute jobs.

## services

Services in the system:

 * smart contract
 * resource provider
 * job creator
 * solver
 * mediator
 * directory

### smart contract

Written in solidity, we will primaily use IPC to reduce latency and gas costs but any other blockchain that is EVM compatible will work.

The aim is to reduce the number of transactions without compromising the game theory of our anti-cheating mechanism.

Aspects handled by the smart contract:

 * deal confirmation and timeouts
 * dispute resolution
 * payouts

#### api

 * `type CID` - bytes32

 * `type ServiceType` - enum
    * resourceProvider
    * jobCreator
    * mediator
    * directory

 * `registerServiceProvider`
    * serviceType ServiceType
    * metadata CID
   
 * `agreeToDeal`
   * dealID CID
   * jobOfferID CID
   * resourceOfferID CID
   * timeout uint (the upper bounds of time this job can take)
   * 
   
 * `submitResults`

 * `cancelDeal`


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