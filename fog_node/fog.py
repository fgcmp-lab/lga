import os.path
import random
import shutil
import struct
import sys
from time import time, sleep
import os

from colorama import Fore, Style
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, TCP4ServerEndpoint

sys.path.insert(0, '..')

'''user defined imports'''
from computation import computational_task, diff2dmnd
from fog_client import FogClientFactory
from fog_server import FogServerFactory

problem_prefix = "pr{}/".format(random.randint(1, 99999999))
tasks_queue = []
cmp_dmnd_vector = []

cmp_alpha = 0.4
cmntn_alpha = 0.4

global cmntn_rate, cmp_cpcty
cmntn_rate = 10485760
cmp_cpcty = 10


def manage_tasks(connections):
    while True:
        sleep(0.001)
        if len(tasks_queue) > 0:
            name = tasks_queue.pop(0)
            cmp_dmnd_vector.pop(0)
            print("task {} is chosen".format(name))
            related_connections = [x for x in connections.clients.values() if str(x.task_id) == name]
            if len(related_connections) < 1:
                return
            assert len(related_connections) == 1
            print("task {} is running".format(name))
            fog_server_obj = related_connections[0]
            fog_server_obj.start_job_time = time()
            file_name = problem_prefix + name + ".txt"
            res = computational_task(file_name, fog_server_obj.difficulty_level)
            fog_server_obj.task_done_time = time()
            ref_time = int(fog_server_obj.start_download_time)
            global cmntn_rate, cmp_cpcty

            cmntn_rate = cmntn_rate * (1 - cmntn_alpha) + cmntn_alpha * fog_server_obj.problem_transfer_throughput
            cmp_cpcty = cmp_cpcty * (1 - cmp_alpha) + cmp_alpha * \
                        (diff2dmnd(fog_server_obj.difficulty_level) / (
                                fog_server_obj.task_done_time - fog_server_obj.start_job_time))

            fog_server_obj.send_message(struct.pack('ddddQQ', fog_server_obj.start_download_time - ref_time,
                                                    fog_server_obj.end_download_time - ref_time,
                                                    fog_server_obj.start_job_time - ref_time,
                                                    fog_server_obj.task_done_time - ref_time,
                                                    int(fog_server_obj.problem_transfer_throughput),
                                                    int(res)), is_binary=True)
            print(Fore.GREEN + "task {} is done completely".format(name) + Style.RESET_ALL)
            # fog_server_obj.transport.loseConnection()


def enqueue_task(name, cmp_dmnd):
    tasks_queue.append(name)
    cmp_dmnd_vector.append(cmp_dmnd)


def update_status(conn):
    global cmntn_rate, cmp_cpcty
    while True:
        conn.status.rssi = random.random()
        conn.status.q_len = len(tasks_queue)
        conn.status.q_v = sum(cmp_dmnd_vector)
        conn.status.cmp_cpcty = cmp_cpcty
        conn.status.cmntn_rate = cmntn_rate
        conn.status.cpu_power = my_cpu_power
        conn.status.network_power = my_network_power
        sleep(0.1)


if __name__ == '__main__':
    if os.path.exists(problem_prefix) and os.path.isdir(problem_prefix):
        shutil.rmtree(problem_prefix)
    os.mkdir(problem_prefix)

    CONTROLLER_SERVER_IP = "172.21.48.59"
    CONTROLLER_SERVER_PORT = 12345
    if len(sys.argv) > 2:
        CONTROLLER_SERVER_IP = sys.argv[1]
        CONTROLLER_SERVER_PORT = eval(sys.argv[2])
    elif len(sys.argv) > 1:
        CONTROLLER_SERVER_IP = sys.argv[1]

    FOG_SERVER_IP = os.getenv("MY_IP", "127.0.0.1")
    my_cpu_power = eval(os.getenv("MY_CPU_POWER", "0"))
    my_network_power = eval(os.getenv("MY_NETWORK_POWER", "0"))
    fg_cld = os.getenv("fg_cld", "fog")

    FOG_SERVER_PORT = random.randint(10000, 65535)

    endpoint = TCP4ClientEndpoint(reactor, CONTROLLER_SERVER_IP, CONTROLLER_SERVER_PORT)
    endpoint.connect(FogClientFactory(fog_server_ip=FOG_SERVER_IP, fog_server_port=FOG_SERVER_PORT
                                      , update_status_func=update_status, fg_cld=fg_cld))

    endpoint2 = TCP4ServerEndpoint(reactor, FOG_SERVER_PORT)
    endpoint2.listen(FogServerFactory(problem_prefix, manage_tasks, enqueue_task))
    reactor.run()
