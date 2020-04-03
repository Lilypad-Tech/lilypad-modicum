
#END SESSSION
fab -R BBBs prunCommand:"sudo pkill tmux",True
sudo pkill tmux


#FETCH LOGS
stamp=$(date -d "today" +"%Y_%m_%d_%H_%M")

rsync --remove-source-files -v -e "ssh -p222 -i /home/riaps/.ssh/cluster_2018_9_10" riaps@172.21.20.24:~/modicum.log ./logs/
cp ./logs/modicum.log ~/projects/MODiCuM/logs/"$stamp"_node24.log

rsync --remove-source-files -v -e "ssh -p222 -i /home/riaps/.ssh/cluster_2018_9_10" riaps@172.21.20.27:~/modicum.log ./logs/
cp ./logs/modicum.log ~/projects/MODiCuM/logs/"$stamp"_node27.log

rsync --remove-source-files -v -e "ssh -p222 -i /home/riaps/.ssh/cluster_2018_9_10" riaps@172.21.20.30:~/modicum.log ./logs/
cp ./logs/modicum.log ~/projects/MODiCuM/logs/"$stamp"_node30.log


cp /home/riaps/modicum.log ~/projects/MODiCuM/logs/"$stamp"_node1.log

sudo rm contract.json
rm ./logs/modicum.log

