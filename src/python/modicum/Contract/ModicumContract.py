from .Contract import Contract
from .Enums import *
import datetime
from .. import helper


class ModicumContract(Contract):

	def test(self, from_account, getReceipt, value):
		event = "test"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint256", value
		)

	def check(self, from_account, getReceipt, arch):
		event = "check"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"Architecture", arch
		)

	def setPenaltyRate(self, from_account, getReceipt, _penaltyRate):
		event = "setPenaltyRate"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint256", _penaltyRate
		)

	def setReactionDeadline(self, from_account, getReceipt, _reactionDeadline):
		event = "setReactionDeadline"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint256", _reactionDeadline
		)

	def registerMediator(self, from_account, getReceipt, arch, instructionPrice, bandwidthPrice, availabilityValue, verificationCount):
		event = "registerMediator"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"Architecture", arch,
			"uint256", instructionPrice,
			"uint256", bandwidthPrice,
			"uint256", availabilityValue,
			"uint256", verificationCount
		)

	def mediatorAddTrustedDirectory(self, from_account, getReceipt, directory):
		event = "mediatorAddTrustedDirectory"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"address", directory
		)

	def mediatorAddSupportedFirstLayer(self, from_account, getReceipt, firstLayerHash):
		event = "mediatorAddSupportedFirstLayer"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint256", firstLayerHash
		)

	def registerResourceProvider(self, from_account, getReceipt, arch, timePerInstruction):
		event = "registerResourceProvider"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"Architecture", arch,
			"uint256", timePerInstruction
		)

	def resourceProviderAddTrustedMediator(self, from_account, getReceipt, mediator):
		event = "resourceProviderAddTrustedMediator"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"address", mediator
		)

	def resourceProviderAddTrustedDirectory(self, from_account, getReceipt, directory):
		event = "resourceProviderAddTrustedDirectory"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"address", directory
		)

	def resourceProviderAddSupportedFirstLayer(self, from_account, getReceipt, firstLayerHash):
		event = "resourceProviderAddSupportedFirstLayer"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint256", firstLayerHash
		)

	def registerJobCreator(self, from_account, getReceipt):
		event = "registerJobCreator"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event
			
		)

	def jobCreatorAddTrustedMediator(self, from_account, getReceipt, mediator):
		event = "jobCreatorAddTrustedMediator"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"address", mediator
		)

	def postResOffer(self, from_account, getReceipt, price, instructionPrice, instructionCap, memoryCap, localStorageCap, bandwidthCap, bandwidthPrice, matchIncentive, verificationCount, misc):
		event = "postResOffer"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, price, event, 
			"uint256", instructionPrice,
			"uint256", instructionCap,
			"uint256", memoryCap,
			"uint256", localStorageCap,
			"uint256", bandwidthCap,
			"uint256", bandwidthPrice,
			"uint256", matchIncentive,
			"uint256", verificationCount,
			"uint256", misc
		)

	def postJobOfferPartOne(self, from_account, getReceipt, price, ijoid, instructionLimit, bandwidthLimit, instructionMaxPrice, bandwidthMaxPrice, completionDeadline, matchIncentive):
		event = "postJobOfferPartOne"
		self.helper.logTxn(self.aix, event, ijoid=ijoid)
		return self.call_func(from_account, getReceipt, price, event, 
			"uint256", ijoid,
			"uint256", instructionLimit,
			"uint256", bandwidthLimit,
			"uint256", instructionMaxPrice,
			"uint256", bandwidthMaxPrice,
			"uint256", completionDeadline,
			"uint256", matchIncentive
		)

	def postJobOfferPartTwo(self, from_account, getReceipt, ijoid, firstLayerHash, ramLimit, localStorageLimit, uri, directory, jobHash, arch):
		event = "postJobOfferPartTwo"
		self.helper.logTxn(self.aix, event, ijoid=ijoid)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint256", ijoid,
			"uint256", firstLayerHash,
			"uint256", ramLimit,
			"uint256", localStorageLimit,
			"bytes32", uri,
			"address", directory,
			"uint256", jobHash,
			"Architecture", arch
		)

	def cancelJobOffer(self, from_account, getReceipt, offerId):
		event = "cancelJobOffer"
		self.helper.logTxn(self.aix, event, joid=offerId)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint256", offerId
		)

	def cancelResOffer(self, from_account, getReceipt, offerId):
		event = "cancelResOffer"
		self.helper.logTxn(self.aix, event, joid=offerId)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint256", offerId
		)

	def postMatch(self, from_account, getReceipt, jobOfferId, resourceOfferId, mediator):
		event = "postMatch"
		self.helper.logTxn(self.aix, event, joid=jobOfferId)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint256", jobOfferId,
			"uint256", resourceOfferId,
			"address", mediator
		)

	def postResult(self, from_account, getReceipt, matchId, jobOfferId, status, uri, hash, instructionCount, bandwidthUsage):
		event = "postResult"
		self.helper.logTxn(self.aix, event, joid=jobOfferId)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint256", matchId,
			"uint256", jobOfferId,
			"ResultStatus", status,
			"bytes32", uri,
			"uint256", hash,
			"uint256", instructionCount,
			"uint256", bandwidthUsage
		)

	def rejectResult(self, from_account, getReceipt, resultId, jobOfferId):
		event = "rejectResult"
		self.helper.logTxn(self.aix, event, joid=jobOfferId)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint256", resultId,
			"uint256", jobOfferId
		)

	def acceptResult(self, from_account, getReceipt, resultId, jobOfferId):
		event = "acceptResult"
		self.helper.logTxn(self.aix, event, joid=jobOfferId)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint256", resultId,
			"uint256", jobOfferId
		)

	def postMediationResult(self, from_account, getReceipt, matchId, jobOfferId, status, uri, hash, instructionCount, bandwidthUsage, verdict, faultyParty):
		event = "postMediationResult"
		self.helper.logTxn(self.aix, event, joid=jobOfferId)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint256", matchId,
			"uint256", jobOfferId,
			"ResultStatus", status,
			"bytes32", uri,
			"uint256", hash,
			"uint256", instructionCount,
			"uint256", bandwidthUsage,
			"Verdict", verdict,
			"Party", faultyParty
		)

	def punish(self, from_account, getReceipt, matchId, faultyParty):
		event = "punish"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint256", matchId,
			"Party", faultyParty
		)

	def close(self, from_account, getReceipt, matchId):
		event = "close"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint256", matchId
		)

	def timeout(self, from_account, getReceipt, matchId, jobOfferId):
		event = "timeout"
		self.helper.logTxn(self.aix, event, joid=jobOfferId)
		return self.call_func(from_account, getReceipt, 0, event, 
			"uint256", matchId,
			"uint256", jobOfferId
		)

	def receiveValues(self, from_account, getReceipt, toAccount, amount):
		event = "receiveValues"
		self.helper.logTxn(self.aix, event)
		return self.call_func(from_account, getReceipt, 0, event, 
			"address", toAccount,
			"uint256", amount
		)

	def __init__(self, aix, client, address):
		self.aix = aix 
		self.helper=helper.helper()
		super().__init__(client, address, {'Debug': [('value', 'uint64')], 'DebugArch': [('arch', 'Architecture')], 'DebugUint': [('value', 'uint256')], 'DebugString': [('str', 'bytes32')], 'penaltyRateSet': [('penaltyRate', 'uint256')], 'reactionDeadlineSet': [('reactionDeadline', 'uint256')], 'ResultReaction': [('addr', 'address'), ('resultId', 'uint256'), ('matchId', 'uint256'), ('ResultReaction', 'uint256')], 'ResultPosted': [('addr', 'address'), ('resultId', 'uint256'), ('matchId', 'uint256'), ('status', 'ResultStatus'), ('uri', 'bytes32'), ('hash', 'uint256'), ('instructionCount', 'uint256'), ('bandwidthUsage', 'uint256')], 'Matched': [('addr', 'address'), ('matchId', 'uint256'), ('jobOfferId', 'uint256'), ('resourceOfferId', 'uint256'), ('mediator', 'address')], 'JobOfferPostedPartOne': [('offerId', 'uint256'), ('ijoid', 'uint256'), ('addr', 'address'), ('instructionLimit', 'uint256'), ('bandwidthLimit', 'uint256'), ('instructionMaxPrice', 'uint256'), ('bandwidthMaxPrice', 'uint256'), ('completionDeadline', 'uint256'), ('deposit', 'uint256'), ('matchIncentive', 'uint256')], 'JobOfferPostedPartTwo': [('offerId', 'uint256'), ('addr', 'address'), ('hash', 'uint256'), ('firstLayerHash', 'uint256'), ('uri', 'bytes32'), ('directory', 'address'), ('arch', 'Architecture'), ('ramLimit', 'uint256'), ('localStorageLimit', 'uint256')], 'ResourceOfferPosted': [('offerId', 'uint256'), ('addr', 'address'), ('instructionPrice', 'uint256'), ('instructionCap', 'uint256'), ('memoryCap', 'uint256'), ('localStorageCap', 'uint256'), ('bandwidthCap', 'uint256'), ('bandwidthPrice', 'uint256'), ('deposit', 'uint256'), ('iroid', 'uint256')], 'JobOfferCanceled': [('offerId', 'uint256')], 'ResourceOfferCanceled': [('resOfferId', 'uint256')], 'JobAssignedForMediation': [('addr', 'address'), ('matchId', 'uint256')], 'MediatorRegistered': [('addr', 'address'), ('arch', 'Architecture'), ('instructionPrice', 'uint256'), ('bandwidthPrice', 'uint256'), ('availabilityValue', 'uint256'), ('verificationCount', 'uint256')], 'MediatorAddedSupportedFirstLayer': [('addr', 'address'), ('firstLayerHash', 'uint256')], 'ResourceProviderRegistered': [('addr', 'address'), ('arch', 'Architecture'), ('timePerInstruction', 'uint256'), ('penaltyRate', 'uint256')], 'ResourceProviderAddedTrustedMediator': [('addr', 'address'), ('mediator', 'address')], 'JobCreatorRegistered': [('addr', 'address'), ('penaltyRate', 'uint256')], 'JobCreatorAddedTrustedMediator': [('addr', 'address'), ('mediator', 'address')], 'MediatorAddedTrustedDirectory': [('addr', 'address'), ('directory', 'address')], 'ResourceProviderAddedTrustedDirectory': [('addr', 'address'), ('directory', 'address')], 'ResourceProviderAddedSupportedFirstLayer': [('addr', 'address'), ('firstLayer', 'uint256')], 'MediationResultPosted': [('matchId', 'uint256'), ('addr', 'address'), ('result', 'uint256'), ('faultyParty', 'Party'), ('verdict', 'Verdict'), ('status', 'ResultStatus'), ('uri', 'bytes32'), ('hash', 'uint256'), ('instructionCount', 'uint256'), ('mediationCost', 'uint256')], 'MatchClosed': [('matchId', 'uint256'), ('cost', 'uint256')], 'EtherTransferred': [('_from', 'address'), ('to', 'address'), ('value', 'uint256'), ('cause', 'EtherTransferCause')]})
