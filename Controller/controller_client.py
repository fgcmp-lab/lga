import os
from colorama import Fore, Style
from twisted.internet import protocol
from twisted.internet.protocol import ReconnectingClientFactory as ClFactory
from computation import try_num
import struct
from time import time


def verify_ans(chosen_task, ans, _difficulty_level):
    f = open(os.path.join("problems", "problem" + str(chosen_task) + ".txt"), "rb")
    problem_context = f.read()
    f.close()
    return try_num(problem_context, ans, _difficulty_level)


class ControllerClient(protocol.Protocol):
    def __init__(self, chosen_task, task_id, _difficulty_level, set_communication_demand, fog_id, add_new_info,
                 deadline_time):
        self.is_info_known = False
        self.file_content = ""
        self.chosen_task = chosen_task
        self.task_id = task_id
        self._difficulty_level = _difficulty_level
        self.start_transmission_time = None
        self.start_download_time = None
        self.end_download_time = None
        self.start_job_time = None
        self.task_done_time = None
        self.all_done_time = None
        self.problem_transfer_throughput = None
        self.set_communication_demand = set_communication_demand
        self.fog_id = fog_id
        self.add_new_info = add_new_info
        self.deadline_time = deadline_time

    def send_message(self, mes, is_binary=False):
        if is_binary:
            self.transport.write(mes)
        else:
            self.transport.write(mes.encode("utf-8"))

    def connectionMade(self):
        self.start_transmission_time = time()
        f = open(os.path.join("problems", "problem" + str(self.chosen_task) + ".txt"), "rb")
        self.file_content = f.read()
        self.set_communication_demand(len(self.file_content))
        f.close()
        info = "{}/{}/{}".format(self.task_id, len(self.file_content), self._difficulty_level)
        self.send_message(info)

    def dataReceived(self, data):
        if self.is_info_known is False:
            self.send_message(self.file_content, is_binary=True)
            self.is_info_known = True
        else:

            decoded_tuple = struct.unpack('ddddQQ', data)
            (self.start_download_time, self.end_download_time, self.start_job_time, self.task_done_time, self.problem_transfer_throughput,
             data) = decoded_tuple
            print("ans: {} is received from fog server".format(data))
            self.all_done_time = time()
            if verify_ans(self.chosen_task, data, self._difficulty_level):
                service_time = self.all_done_time - self.start_transmission_time
                print(Fore.GREEN +
                      "ans is verified from {}/ Time={:.4f}+{:.4f}+{:.4f}={:.4f}s,  R={:.2f} MBytes/s, Service Time={:.4f}s".format(
                          self.fog_id,
                          self.end_download_time - self.start_download_time,
                          self.start_job_time - self.end_download_time,
                          self.task_done_time - self.start_job_time,
                          self.task_done_time - self.start_download_time,
                          self.problem_transfer_throughput / 1048576,
                          service_time)
                      + Style.RESET_ALL)

                statistics_obj = {"serviceTime": service_time,
                                  "deadline": service_time > self.deadline_time,
                                  "cpu_time": self.task_done_time - self.start_job_time,
                                  "network_time": self.end_download_time - self.start_download_time,
                                  }

                self.add_new_info(statistics_obj)

            else:
                print(Fore.RED + "ans is not verified" + Style.RESET_ALL)
            self.transport.loseConnection()


class ControllerClientFactory(ClFactory):

    def __init__(self, chosen_task, task_id, _difficulty_level, set_communication_demand, fog_id, add_new_info,
                 deadline_time):
        self.chosen_task = chosen_task
        self.task_id = task_id
        self._difficulty_level = _difficulty_level
        self.set_communication_demand = set_communication_demand
        self.fog_id = fog_id
        self.add_new_info = add_new_info
        self.deadline_time = deadline_time

    def clientConnectionLost(self, connector, unused_reason):
        self.retry(connector)

    def clientConnectionFailed(self, connector, reason):
        print(reason)
        self.retry(connector)

    def buildProtocol(self, addr):
        return ControllerClient(self.chosen_task, self.task_id, self._difficulty_level, self.set_communication_demand,
                                self.fog_id, self.add_new_info, self.deadline_time)
