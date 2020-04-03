class Mediator():
  def __init__(self, arch, instructionPrice, bandwidthPrice):
    self.arch = arch
    self.instructionPrice = instructionPrice
    self.bandwidthPrice = bandwidthPrice
    #self.supportedDirectories = supportedDirectories
    #self.layers = layers
  def __eq__(self, other):
    """Overrides the default implementation"""
    if isinstance(other, Mediator):
        return (self.arch == other.arch and self.instructionPrice == other.instructionPrice and self.bandwidthPrice == other.bandwidthPrice and self.dockerBandwidthPrice == other.dockerBandwidthPrice)
    return False

class ResourceProvider():
  def __init__(self, arch, timePerInstruction):
    self.arch = arch
    #timePerInstruction must be in microseconds
    self.timePerInstruction = timePerInstruction
    self.trustedMediators = []

class JobCreator():
 def __init__(self):
    self.trustedMediators=[]


class JobOffer():
    #JobOfferPosted(uint offerId, address jobCreator, uint size, Architecture arch, uint instructionLimit, uint ramLimit, uint localStorageLimit, uint bandwidthLimit, uint instructionMaxPrice, uint bandwidthMaxPrice, uint dockerBandwidthMaxPrice, uint256 completionDeadline);
  def __init__(self,offerId=0,ijoid=0,jobCreator="",instructionLimit=0,bandwidthLimit=0,instructionMaxPrice=0,
                    bandwidthMaxPrice=0,completionDeadline=0,deposit=0,matchIncentive=0, hash=0,firstLayerHash=0,
                    uri="",directory="",arch="",ramLimit=0,localStorageLimit=0):

    self.offerId = offerId 
    self.ijoid = ijoid 
    self.jobCreator = jobCreator 
    self.instructionLimit = instructionLimit 
    self.bandwidthLimit = bandwidthLimit 
    self.instructionMaxPrice = instructionMaxPrice 
    self.bandwidthMaxPrice = bandwidthMaxPrice 
    self.completionDeadline = completionDeadline 
    self.deposit = deposit 
    self.matchIncentive = matchIncentive 

    self.hash = hash
    self.firstLayerHash = firstLayerHash
    self.uri = uri
    self.directory = directory
    self.arch = arch
    self.ramLimit = ramLimit
    self.localStorageLimit = localStorageLimit

    

class ResourceOffer():
    #ResourceOfferPosted(uint offerId, address resourceProvider, uint instructionPrice, uint instructionCap, uint memoryCap, uint localStorageCap, uint bandwidthCap, uint bandwidthPrice, uint dockerBandwidthCap, uint dockerBandwidthPrice);
  def __init__(self, offerId, resourceProvider, instructionPrice, instructionCap, memoryCap, localStorageCap, bandwidthCap, bandwidthPrice, deposit, iroid):
    self.offerId = offerId
    self.resourceProvider =resourceProvider
    self.instructionPrice = instructionPrice
    self.instructionCap = instructionCap
    self.memoryCap = memoryCap
    self.localStorageCap = localStorageCap
    self.bandwidthCap = bandwidthCap
    self.bandwidthPrice = bandwidthPrice
    self.deposit = deposit
    self.iroid = iroid

class Match():
  def __init__(self,   jobOfferId, resourceOfferId, mediator):
    self.jobOfferId = jobOfferId
    self.resourceOfferId = resourceOfferId
    self.mediator = mediator
