source ../../../src/python/.env

# Setup environment
fab -R BBBs prunCommand:"touch modicum.log",True
touch modicum.log
fab -R BBBs prunCommand:"cp /home/riaps/projects/MODiCuM/src/python/.env /home/riaps/.env",True
cp /home/riaps/projects/MODiCuM/src/python/.env /home/riaps/.env

# CREATE SESSIONS
tmux new-session -d -s CM
tmux new-session -d -s DIR
tmux new-session -d -s S


tmux send -t CM 'echo $pass | sudo -S modicum runAsCM --index 0' ENTER
tmux send -t DIR 'echo $pass | sudo -S modicum runAsDir' ENTER
tmux send -t S 'echo $pass | sudo -S modicum runAsSolver --index 2' ENTER

fab -R Ms prunCommand:"tmux new -d -s M",verbose=True
fab -H 172.21.20.30 runCommand:"tmux send -t M 'cd /home/riaps/projects/MODiCuM/src/python; sudo -S modicum runAsMediator --index 3 --sim False' ENTER"


fab -R JCs prunCommand:"tmux new -d -s JC",verbose=True
fab -R RPs prunCommand:"tmux new -d -s RP",verbose=True
fab -R JCs prunCommand:"tmux new -d -s JCD",verbose=False
fab -R RPs prunCommand:"tmux new -d -s RPD",verbose=False
fab -H 172.21.20.24 runCommand:"tmux send -t JCD 'cd /home/riaps/projects/MODiCuM/src/python; sudo -S modicum startJC -p /home/riaps/projects/MODiCuM/0_experiments/100job/players/ --index 4 --sim False' ENTER"
fab -H 172.21.20.27 runCommand:"tmux send -t RPD 'cd /home/riaps/projects/MODiCuM/src/python; sudo -S modicum startRP -p /home/riaps/projects/MODiCuM/0_experiments/100job/players/ --index 7 --sim False' ENTER"
