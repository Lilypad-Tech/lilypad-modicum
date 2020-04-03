import sys
import os
import fabric.api as fabi

fabi.env.password="riaps"
fabi.env.user="riaps"

fabi.env.key_filename = '~/.ssh/cluster_2018_9_10'
#fabi.env.key_filename = '~/.ssh/blockchain'
fabi.env.port = 222

fabi.env.skip_bad_hosts = True
fabi.env.warn_only = True
fabi.env.abort_on_prompts=True

# JCs = ['172.21.20.24','172.21.20.25','172.21.20.26']
# RPs = ['172.21.20.27','172.21.20.28','172.21.20.29']
hosts ={
"bbb-8014": "172.21.20.1", "bbb-6302": "172.21.20.2",
"bbb-4c23": "172.21.20.3", "bbb-7d6a": "172.21.20.4",
"bbb-c473": "172.21.20.5", "bbb-235d": "172.21.20.6",
"bbb-95f9": "172.21.20.7", "bbb-b957": "172.21.20.8",
"bbb-bcf6": "172.21.20.9",
"bbb-c189": "172.21.20.12", "bbb-b4bc": "172.21.20.16",
"bbb-99b4": "172.21.20.17", "bbb-a702": "172.21.20.18",
"bbb-1b70": "172.21.20.19", "bbb-c452": "172.21.20.21",
"bbb-cb60": "172.21.20.22", "bbb-ede8": "172.21.20.24",
"bbb-e1ec": "172.21.20.25", "bbb-c434": "172.21.20.26",
"bbb-41b1": "172.21.20.27", "bbb-50c9": "172.21.20.28",
"bbb-a327": "172.21.20.29", "bbb-2592": "172.21.20.30",
"bbb-e4ff": "172.21.20.31", "bbb-29a6": "172.21.20.32",
}

CLUSTER = list(hosts.values())


JCs = ['172.21.20.24']
RPs = ['172.21.20.27']
Ms = ['172.21.20.30']
BBBs = JCs + RPs + Ms
VM = ['172.21.20.40']
HORIZON = ['10.4.209.25']
ALL = BBBs + VM

# ALL = BBBs + VM

fabi.env.roledefs = {
    'ALL' : ALL,
	'VM' : VM,
	'HORIZON' : HORIZON,
	'BBBs': BBBs,
	'Ms' : Ms,
	'JCs' : JCs,
	'RPs' : RPs,
	'CLUSTER' : CLUSTER
}

@fabi.task
def update():
	cmd = "rsync -ruv  \
	--exclude='*.pyc*' \
	--exclude='*egg*' \
	--include='0_experiments/'\
	--include='0_experiments/**'\
    --include='src/' \
    --include='src/python/' \
    --include='src/python/**' \
    --exclude='*' \
    -e 'ssh -oStrictHostKeyChecking=no -p 222 -i ~/.ssh/blockchain' \
    riaps@172.21.20.40:~/projects/MODiCuM/ ~/projects/MODiCuM/"
	fabi.run(cmd)

@fabi.task
def updateAll():
	cmd = "rsync -ruv  \
	--exclude='*.pyc*' \
	--exclude='*egg*' \
	--include='players/'\
	--include='players/*'\
    --include='src/' \
    --include='src/python/' \
    --include='src/python/**' \
    --include='workloads/' \
    --include='workloads/stress-ng/' \
    --include='workloads/stress-ng/**' \
    --include='workloads/bodytrack/' \
    --include='workloads/bodytrack/**'\
    --exclude='*' \
    -e 'ssh -oStrictHostKeyChecking=no -p 222 -i ~/.ssh/cluster_2018_9_10 ' \
    riaps@172.21.20.40:~/projects/MODiCuM/ ~/projects/MODiCuM/"
	fabi.run(cmd)

#@fabi.parallel
@fabi.task
#http://docs.fabfile.org/en/2.3/cli.html#executing-arbitrary-ad-hoc-commands
def runCommand(command,verbose=False):
	"""run with fab -R '<role to run command on, e.g c2_1>' runCommand:<command to run>
		or to run on a specific host: fab -H '10.0.2.194:2222' runCommand:'hostname'"""
	results = ''
	print(verbose)
	# with fabi.hide('status','aborts','warnings','running','stdout','stderr'), fabi.settings(warn_only=True):
	with fabi.hide('warnings','output'), fabi.settings(warn_only=True):
		results = fabi.run(command)
	if verbose:
		print(results)
	return(results)


@fabi.task
@fabi.parallel
#http://docs.fabfile.org/en/2.3/cli.html#executing-arbitrary-ad-hoc-commands
def prunCommand(command,verbose=False):
	"""run with fab -R '<role to run command on, e.g c2_1>' runCommand:<command to run>
		or to run on a specific host: fab -H '10.0.2.194:2222' runCommand:'hostname'"""
	results = ''
	print(verbose)

	if verbose:
		with fabi.hide(), fabi.settings(warn_only=True):
		# with fabi.hide('warnings','output'), fabi.settings(warn_only=True):
			results = fabi.run(command)
		print(results)
	else:
		with fabi.hide('status','aborts','warnings','running','stdout','stderr','output'), fabi.settings(warn_only=True):
			results = fabi.run(command)

	return(results)
