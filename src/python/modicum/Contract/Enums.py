from enum import Enum


class Architecture(Enum):
	amd64 = 0
	armv7 = 1


class ResultStatus(Enum):
	Completed = 0
	Declined = 1
	JobDescriptionError = 2
	JobNotFound = 3
	MemoryExceeded = 4
	StorageExceeded = 5
	InstructionsExceeded = 6
	BandwidthExceeded = 7
	ExceptionOccured = 8
	DirectoryUnavailable = 9


class Party(Enum):
	ResourceProvider = 0
	JobCreator = 1


class Verdict(Enum):
	ResultNotFound = 0
	TooMuchCost = 1
	WrongResults = 2
	CorrectResults = 3
	InvalidResultStatus = 4


class Reaction(Enum):
	Accepted = 0
	Rejected = 1
	_None = 2


class EtherTransferCause(Enum):
	PostJobOffer = 0
	PostResourceOffer = 1
	CancelJobOffer = 2
	CancelResOffer = 3
	Punishment = 4
	Mediation = 5
	FinishingJob = 6
	FinishingResource = 7
	PostMatch = 8
	MediatorAvailability = 9

