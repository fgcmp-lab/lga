import random
from time import sleep
from twisted.internet import reactor, protocol
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.protocol import ServerFactory as SrFactory, connectionDone
from computation import diff2dmnd

from status import *
from controller_client import ControllerClientFactory

VERBOSE_MODE = True


class ControllerServer(protocol.Protocol):
    def __init__(self, clients: dict, my_id, status: Status, check_interval_ms, difficulty_level_range
                 , request, add_new_info):
        self.my_id = my_id
        self.status = status
        self.clients = clients
        self.another_client = None
        self.CHECK_INTERVAL_MS = check_interval_ms
        self.difficulty_level_range = difficulty_level_range
        self.chosen_task = None
        self.request = request
        self.initialized = False
        self.fg_cld = None
        self.add_new_info = add_new_info

        reactor.callInThread(self.ping_clients)

    def ping_clients(self):
        while True:
            sleep(self.CHECK_INTERVAL_MS / 1000)
            self.send_message(type="ping", value="")

    def connectionMade(self):
        print("new connection from id={}".format(self.my_id))
        self.clients[self.my_id] = self

    @staticmethod
    def __encode_json(**kwargs):
        return json.dumps(kwargs)

    def send_message(self, **kwargs):
        if kwargs.get('where'):
            where = kwargs['where']
            del kwargs['where']
            where.transport.write(self.__encode_json(**kwargs).encode("utf-8"))
        else:
            mes = self.__encode_json(**kwargs)
            self.transport.write(mes.encode("utf-8"))

    def broadcast_message(self, **kwargs):
        for u in self.clients:
            self.clients[u].transport.write(self.__encode_json(**kwargs).encode("utf-8"))

    def broadcast_message_except_me(self, **kwargs):
        for u in self.clients:
            if u != self:
                self.clients[u].transport.write(self.__encode_json(**kwargs).encode("utf-8"))

    def parse_single_command(self, data):
        try:
            data = json.loads(data)
        except UnicodeDecodeError:
            self.send_message(value="Cannot decode, use utf-8", type='error')
            return
        except json.JSONDecodeError:
            self.send_message(value="Cannot decode, use json", type='error')
            return

        if not data.get('type') or not data.get('value'):
            self.send_message(value=f"Wrong data", type='error')
            return

        if data['type'] == "user_choose":
            try:
                another_client = int(data['value'])
                if another_client in self.clients.keys():
                    self.another_client = another_client
                else:
                    raise KeyError

            except ValueError:
                self.send_message(value="Write another id as int", type='error')
            except KeyError:
                self.send_message(value="Can't find that client", type='error')
            else:
                self.send_message(value=f"Talk to {self.another_client}", type='user_chosen')

        elif data['type'] == "new_message":
            if not self.another_client:
                self.send_message(value=f"Don't have a client to send your message to", type='error')
            try:
                self.send_message(value=data['value'], where=self.clients[self.another_client], type='new_message')
            except KeyError:
                self.send_message(value="Something wrong happened, try another client", type='error')
                self.another_client = None
        elif data['type'] == "id_req":
            self.fg_cld = data['value']
            object_dict = dict({"self": self.my_id, "all": list(self.clients.keys())})
            self.send_message(value=object_dict, type='id_res')
        elif data['type'] == "cl_status":
            self.status = Status(json.loads(data['value']))
            if VERBOSE_MODE:
                print("status received: {}".format(self.status))
        elif data['type'] == "comp_res":
            fog_server_port, task_id, fog_server_ip = [x if '.' in x else eval(x) for x in
                                                       str(data['value']).split("/")]

            endpoint2 = TCP4ClientEndpoint(reactor, fog_server_ip, fog_server_port)
            difficulty_level = random.randint(self.difficulty_level_range[0], self.difficulty_level_range[1])
            self.request['cmp_dmnd'] = diff2dmnd(difficulty_level)
            endpoint2.connect(
                ControllerClientFactory(self.chosen_task, task_id, difficulty_level, self.set_communication_demand,
                                        self.my_id, self.add_new_info_server, self.request['deadlineTime'])
            )
            self.chosen_task = None
        else:
            pass

    def add_new_info_server(self, client_object):
        server_object = {"cpu_power": self.status.cpu_power,
                         "network_power": self.status.network_power,
                         "backLock": self.status.q_v}
        self.add_new_info(client_object, server_object, self.my_id, self)

    def dataReceived(self, data):
        data = data.decode("utf-8")
        data = data[1:-1].split("}{")
        for dt in data:
            self.parse_single_command("{" + dt + "}")

    def connectionLost(self, reason=connectionDone):
        self.disconnect()

    def disconnect(self):
        del self.clients[self.my_id]

    def set_communication_demand(self, demand):
        self.request['cmntn_dmnd']=demand


class ControllerServerFactory(SrFactory):
    def __init__(self, check_interval_ms, difficulty_level_range, manage_task, request, add_new_info):
        self.clients = {}
        self.last_id = 0
        self.status = Status(None)
        self.check_interval_ms = check_interval_ms
        self.difficulty_level_range = difficulty_level_range
        self.request = request
        # self.request['cmp_dmnd'] = diff2dmnd(self.difficulty_level)
        self.add_new_info = add_new_info
        reactor.callInThread(manage_task, self, self.request)

    def buildProtocol(self, addr):
        self.last_id += 1
        return ControllerServer(self.clients, self.last_id, self.status, self.check_interval_ms,
                                self.difficulty_level_range,
                                self.request, self.add_new_info)
