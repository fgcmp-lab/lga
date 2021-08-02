import json
import random, os
import sys

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from time import sleep
import numpy as np
from colorama import Fore, Style

sys.path.insert(0, '..')

'''user defined imports'''
from controller_server import ControllerServerFactory
import schedule
from time import time
from matplotlib import pyplot as plt

# timing config
CHECK_INTERVAL_MS = 1000
SCHEDULE_INTERVAL_MS = 1000

# problem generation config
PROBLEM_GENERATION_INTERVAL_MS = 2_000
PROBLEM_GENERATION_POISSON_LAMBDA = 0.5
PROBLEM_GENERATION_POISSON_OBSERVATION_TIME = 10

# network config
CONTROLLER_SERVER_PORT = 12345

difficulty_level_range = (4, 7)
all_tasks_queue = []

timing = []

base_time = time()


def simple_problem_feeder():
    while True:
        all_tasks_queue.append(str(random.randint(1, 10)))
        sleep(PROBLEM_GENERATION_INTERVAL_MS / 1000)


def poisson_problem_feeder():
    while True:
        dt = np.random.default_rng().exponential(1 / PROBLEM_GENERATION_POISSON_LAMBDA)
        all_tasks_queue.append(str(random.randint(1, 10)))
        timing.append(time() - base_time)
        sleep(dt)
        # if len(timing) > 10:
        #     plt.plot(timing, [0 for _ in range(len(timing))], 'o')
        #     plt.show()
        #     return


# problem_feeder = poisson_problem_feeder
problem_feeder = simple_problem_feeder

# schedule_task = schedule.schedule_task_random
schedule_task = schedule.schedule_task_tmlns


# schedule_task = schedule.schedule_task_sjq


def manage_task(con, request):
    while True:
        if len(all_tasks_queue) > 0 and len(con.clients) > 0:
            client_id = None
            # for con_name in con.clients.keys():
            #     if not con.clients[con_name].initilized:
            #         client_id = con_name
            #         con.clients[con_name].initilized =True
            #         break

            if client_id is None:
                client_id = schedule_task(con.clients, request=request)
            con.clients[client_id].chosen_task = eval(all_tasks_queue.pop(0))
            con.clients[client_id].send_message(value=1, type="comp_req")
            print("client #{} is chosen".format(client_id))
        sleep(SCHEDULE_INTERVAL_MS / 1000)


statistics_vector = {}

global base_time2
base_time2 = None


def add_new_info(client_obj, server_obj, fog_id, obj):
    client_obj.update(server_obj)
    global base_time2
    if base_time2 is None:
        base_time2 = time()

    cpu_energy = client_obj['cpu_time'] * obj.status.cpu_power
    network_energy = client_obj['network_time'] * obj.status.network_power
    client_obj['energy'] = cpu_energy + network_energy

    statistics_list = statistics_vector.get(fog_id, list())
    statistics_list.append(client_obj)
    statistics_vector[fog_id] = statistics_list
    if len(sys.argv) > 2:
        all_tasks_cnt = eval(sys.argv[1])
        termination_type = sys.argv[2]
        if termination_type.lower() == 's':
            done_task_cnt = time() - base_time2
        else:
            done_task_cnt = sum([len(x) for x in statistics_vector.values()])
        print(Fore.CYAN + "done tasks({:.1f}%) {}/{}{}"
              .format(done_task_cnt / all_tasks_cnt * 100, int(10000*done_task_cnt)/10000,
                      all_tasks_cnt, termination_type)
              + Style.RESET_ALL)
        if done_task_cnt >= all_tasks_cnt:
            f = open("result.json", "w")
            file_content = {"backLock": {x: statistics_vector.get(x)[-1]['backLock'] for x in statistics_vector.keys()},
                            "power": {
                                x: sum([y['network_power'] + y['cpu_power'] for y in statistics_vector.get(x)]) / len(
                                    statistics_vector.get(x))
                                for x in statistics_vector.keys()},
                            "energy": {
                                x: sum([y['energy'] for y in statistics_vector.get(x)])
                                for x in statistics_vector.keys()},
                            "serviceTime": {
                                x: sum([y['serviceTime'] for y in statistics_vector.get(x)]) / len(
                                    statistics_vector.get(x))
                                for x in statistics_vector.keys()},
                            "deadline": {
                                x: len([y for y in statistics_vector.get(x) if y['deadline'] is True])
                                for x in statistics_vector.keys()
                            }}

            backlock_sum = sum([x[-1]['backLock'] for x in statistics_vector.values()])
            power_sum = sum([sum([y['network_power'] + y['cpu_power'] for y in x]) for x in statistics_vector.values()])
            energy_sum = sum([sum([y['energy'] for y in x]) for x in statistics_vector.values()])
            service_time = sum([sum([y['serviceTime'] for y in x]) for x in statistics_vector.values()])
            deadline_cnt = sum([len([y['deadline'] for y in x if y['deadline'] is True]) for x in statistics_vector.values()])
            file_content["total"] = {"total backLock": backlock_sum,
                                     "Average power": power_sum/done_task_cnt,
                                     "Average serviceTime": service_time/done_task_cnt,
                                     "total deadline": deadline_cnt,
                                     "total energy": energy_sum
                                     }

            f.write(json.dumps(file_content, indent=4))
            f.close()
            reactor.stop()
            print("result.json file saved!")
            for cl in obj.clients.values():
                cl.transport.loseConnection()


if __name__ == '__main__':
    req = {"cmp_dmnd": 100, "cmntn_dmnd": 150_000, "deadlineTime": 20}

    endpoint = TCP4ServerEndpoint(reactor, CONTROLLER_SERVER_PORT)
    port = endpoint.listen(ControllerServerFactory(check_interval_ms=CHECK_INTERVAL_MS,
                                                   difficulty_level_range=difficulty_level_range, manage_task=manage_task,
                                                   request=req,
                                                   add_new_info=add_new_info))

    reactor.callInThread(problem_feeder)
    reactor.run()
