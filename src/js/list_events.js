const fs = require('fs')
const Web3 = require('web3');
const ABIText = fs.readFileSync('../solidity/output/Modicum.abi', 'utf8')
const ABI = JSON.parse(ABIText)
const contractAddress = '0x97e188e7b333a31f6d9131d1ce8d32642d7a54e8'

const web3 = new Web3('http://localhost:10000'); // Change to your geth instance's RPC URL if different
const contract = new web3.eth.Contract(ABI, contractAddress);

contract.getPastEvents('allEvents', {
    fromBlock: 0,
    toBlock: 'latest'
}).then(events => console.log(events));