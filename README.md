# Fog-schedule repository

A prototype to benchmark different scheduling tasks(sjq, random, AFC, LGA, ...).

![Controller](images/controller_demo.png)
![fog1](images/fog1_demo.png)
![fog2](images/fog2_demo.png)
![fog3](images/fog3_demo.png)
![cloud](images/cloud_demo.png)

## Install reqiurements

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install reqirements.txt.

```bash
git clone https://github.com/aalaei/fog-schedule.git
cd fog-schedule
pip3 install -r requrements.txt
```

## Controller
### Config
```python
# timing config
CHECK_INTERVAL_MS = 1000 # time interval of checking clients'(fog/cloud) status 
SCHEDULE_INTERVAL_MS = 1000 # time interval of scheduling

# problem generation config
PROBLEM_GENERATION_INTERVAL_MS = 2_000 # simple feeder problem generation interval
PROBLEM_GENERATION_POISSON_LAMBDA = 0.5 # poisson problem feeder problem generation LAMBDA
PROBLEM_GENERATION_POISSON_OBSERVATION_TIME = 10 # poisson problem feeder problem generation time

# network config
CONTROLLER_SERVER_PORT = 12345

difficulty_level_range = (4, 7) # range of difficulty level(smaple from discrete uniform distribution)

# here we can choose desired problem feeder
# problem_feeder = poisson_problem_feeder
problem_feeder = simple_problem_feeder

# target task scheduler is chosen here
# schedule_task = schedule.schedule_task_random
schedule_task = schedule.schedule_task_tmlns
# schedule_task = schedule.schedule_task_sjq
# schedule_task = schedule.schedule_task_service_time
# schedule_task = schedule.schedule_task_AFC

```
### Server(controller) usage
if `all_tasks_count` and `termination_type` is not given controller will run forever.
```bash
python3 controller.py [all_tasks_count] [termination_type]
    all_tasks_count: number of tasks or seconds that controller should run 
    termination_type: must be either 't'(task count) or 's'(seconds)

```

## Fog/Cloud
### Environment variable
There are some environment variables that must be set before running `fog.py` on each host.
* **FOG_SERVER_IP:** host IP of this host(on desired network interface) [default:`'127.0.0.1'`]
* **my_cpu_power:** cpu power of the system(demand/s)[default:`0`]
    - **Note:** Demand is a compensated-linearized form of difficulty, which means if a task with demnad=D is done in t seconds a task with demand=2D is done about 2t seconds.
* **my_network_power:** network throuput of the system(bits/s)[default:`0`]
* **fg_cld:** choose weather host should be a `fog` or `cloud` [default:`'fog'`]

### Client(fog/cloud) usage

```bash
python3 fog.py [server IP] [server port]
    server IP: default value is '172.21.48.59'
    server port: default value is 12345
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
