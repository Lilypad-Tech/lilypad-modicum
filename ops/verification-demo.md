### verification demo

You will need 5 tmux panes vertically.

Run the following commands in each pane:

**pane1**
```bash
./stack reset && ./stack start && ./stack logs solver
```

**pane2**
```bash
./stack logs mediator
```

**pane3**
```bash
./stack logs resource-provider
```

**pane4**
```bash
./stack balances
```

**pane5**
```bash
# this means mediation will happen every time
# adjust accordingly
export MEDIATION_CHANCE_PERCENT=100
./stack submitjob --template cowsay:v0.0.1 --params "hello"
```

The job should get triggered for mediation after running on the resource provider - you should see this in the mediator logs:

```
2023-07-14 18:01:10,024;Mediator;🔵🔵🔵 RUN JOB NOW
2023-07-14 18:01:11,134;Mediator;🟣🟣🟣🟣 ✅✅✅✅✅✅✅✅✅✅✅ mediation correct result
```

Now - re-run the `./stack balances` command and you should see the job-creator have 1ETH less and the resource provider 9ETH less (the resource provider has been paid 1ETH and then put a deposit of 10 for the next offer)

Now - let's make the resource provider cheat:

**pane1**
```bash
ctrl+c
export BAD_ACTOR=1
./stack reset && ./stack start && ./stack logs solver
```

Re-run all of the other log commands and the balances command then re-submit the job.

This time - the mediator should say:

```
2023-07-14 18:05:39,374;Mediator;🔵🔵🔵 RUN JOB NOW
2023-07-14 18:05:40,483;Mediator;🟣🟣🟣🟣 🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨 mediation wrong result
```

Now - re-run the `./stack balances` command and you should see the job-creator have the same (they have been refunded) and the resource provider 10TH less (which is -10 deposit)