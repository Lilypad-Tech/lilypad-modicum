var fs = require("fs")
var keythereum = require("keythereum")
var argv = require('minimist')(process.argv.slice(2))

if(!argv.file) {
  console.error(`no --file given`)
  process.exit(1)
}

if(!argv.password) {
  console.error(`no --password given`)
  process.exit(1)
}

if(!fs.existsSync(argv.file)) {
  console.error(`file ${argv.file} does not exist`)
  process.exit(1)
}

const data = JSON.parse(fs.readFileSync(argv.file, 'utf8'))

var privateKey = keythereum.recover(argv.password, data)
console.log(privateKey.toString('hex'));