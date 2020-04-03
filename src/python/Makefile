include .env
#include .myenv
export

#------------------------------------------------------------------------------
#    Docker compile contract
#------------------------------------------------------------------------------
solc : INPUT = $(DIR)/$(PROJECT)/src/solidity
solc:
	echo $(INPUT)
	mkdir -p $(CONTRACTSRC)/output
	sudo docker run -it --rm\
		--name solcTest \
		--mount type=bind,source="$(CONTRACTSRC)",target=/solidity/input \
		--mount type=bind,source="$(CONTRACTSRC)/output",target=/solidity/output \
		ethereum/solc:0.4.25 \
		--optimize --overwrite --bin --bin-runtime --ast --asm --abi -o /solidity/output /solidity/input/Modicum.sol
#------------------------------------------------------------------------------
#    Start Private Blockchain
#------------------------------------------------------------------------------
# https://ethereum.stackexchange.com/questions/392/how-can-i-get-a-geth-node-to-download-the-blockchain-quickly/4210
startBC:
	cd $(GETHPATH); ./geth --datadir eth/ --rpc --rpcport 10000 --rpcaddr $(GETHIP) --nodiscover --rpcapi 'eth,web3,admin,miner,net,db' --password password.txt --unlock 0,1,2,3,4,5,6,7,8,9 --networkid 15 --mine --minerthreads=1 --etherbase=0 --targetgaslimit 200000000000000000 console

initBC:
	tmux new -d -s geth
	tmux send -t geth "cd $(GETHPATH)" ENTER
	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
	tmux send -t geth "./geth --datadir eth/  init genesis.json" ENTER

# startBC:
# 	tmux new -d -s geth
# 	tmux send -t geth "cd $(GETHPATH)" ENTER
# 	tmux send -t geth "./geth --datadir eth/  init genesis.json" ENTER
# 	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
# 	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
# 	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
# 	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
# 	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
# 	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
# 	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
# 	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
# 	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
# 	tmux send -t geth "./geth account new --password password.txt --datadir eth/" ENTER
# # 	# tmux send -t geth "./geth --datadir eth/ --rpc --rpcport $(GETHPORT) --rpcaddr $(GETHIP) --nodiscover --rpcapi 'eth,web3,admin,miner,net,db' --password password.txt --unlock 0,1,2,3,4,5,6,7,8,9 --networkid 15 --mine --targetgaslimit 200000000000000000 console |& tee miner.out" ENTER

stopBC:
	pkill tmux
	# pkill geth

logTransactions:
	$(GETHPATH)/geth --exec 'loadScript("$(DIR)/$(PROJECT)/src/python/searchTransactions.js"); getAccountTransactions("$(ADDRESS)", 0, eth.blockNumber);' attach "http://$(GETHIP):$(GETHPORT)" |& tee transaction-log.txt


###############################################################################
#    TESTS SECTION
###############################################################################
#------------------------------------------------------------------------------
#     Profile Test
#------------------------------------------------------------------------------
Profile:
	make startcadvisor
	sleep 2


#------------------------------------------------------------------------------
#    Docker Commands
#------------------------------------------------------------------------------
build:
	sudo docker build

prune:
	sudo docker system prune -a

ls:
	sudo docker images -a

#------------------------------------------------------------------------------
#    Utilities
#------------------------------------------------------------------------------
init:
	sudo apt-get update
	sudo apt-get install -y libcurl4-openssl-dev libssl-dev

	#install docker
	sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common
	curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
	sudo add-apt-repository \
   "deb [arch=$(shell dpkg --print-architecture)] https://download.docker.com/linux/ubuntu \
   $(shell lsb_release -cs) \
   stable"
	sudo apt-get update
	sudo apt-get install -y docker-ce


cleanup:
	- sudo groupdel group_matrix_multiplication;
	- sudo userdel user_1;
	- sudo userdel user_2;
	- sudo rm -r /home/user_1;
	- sudo rm -r /home/user_2;

perf_setup:
	kernel=$(shell uname -r)
	wget https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/snapshot/linux-4.14.71.tar.gz
	tar -xvf linux-4.14.71.tar.gz
	cd linux-4.14.71
	sudo apt-get install -y bison
	make ARCH=arm -C tools/perf/

staticQEMU:
	# git clone git://git.qemu.org/qemu.git
	# apt-get install -y pkg-config
	# cd qemu; ./configure --target-list=arm-linux-user --static; make
	sudo apt update
	sudo apt install -y qemu qemu-user-static qemu-user binfmt-support


testenv:
	env

startcadvisor:
	sudo docker run \
	--volume=/:/rootfs:ro   --volume=/var/run:/var/run:rw  \
	--volume=/sys:/sys:ro 	--volume=/var/lib/docker/:/var/lib/docker:ro   \
	--publish=8080:8080   --detach=true   --name=cadvisor  \
	google/cadvisor:latest \
	--storage_driver=influxdb --storage_driver_host=$(INFLUX):8086 \
	--storage_driver_db=cadvisor --storage_duration=1m0s

startbbbcadvisor:
	sudo docker run \
	--volume=/:/rootfs:ro   --volume=/var/run:/var/run:rw  \
	--volume=/sys:/sys:ro 	--volume=/var/lib/docker/:/var/lib/docker:ro   \
	--publish=8080:8080   --detach=true   --name=cadvisor  \
	budry/cadvisor-arm:latest  \
	--storage_driver=influxdb --storage_driver_host=$(INFLUX):8086 \
	--storage_driver_db=cadvisor --storage_duration=1m0s --max_housekeeping_interval=0m10s

stopcadvisor:
	sudo docker stop cadvisor
	sudo docker rm cadvisor


install:
	sudo pip3 install -e .

setupWrapper:
	sudo pip3 install antlr4-python3-runtime

wrap:
	sudo python3 $(MODICUMPATH)/solidity-wrapper/main.py $(MODICUMPATH)/src/solidity/Modicum.sol $(MODICUMPATH)/src/python/modicum/Contract

geth:
	version=geth-linux-amd64-1.8.22-7fa3509e
	wget https://gethstore.blob.core.windows.net/builds/$(version).tar.gz
	# wget https://gethstore.blob.core.windows.net/builds/geth-linux-amd64-1.7.0-6c6c7b2a.tar.gz
	tar -xvf $(version).tar.gz
	mv $(version) ~/projects/
	rm -r geth*
	touch ~/projects/$(version)/password.txt
	echo password > ~/projects/$(version)/password.txt
	cp $(MODICUMPATH)/ethereum-init/genesis.json /home/riaps/projects/$(version)
