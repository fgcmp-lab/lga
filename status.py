import json


class Status:
    def __init__(self, obj):
        if obj is not None:
            self.id = obj['id']
            self.rssi = obj['rssi']
            self.q_len = obj['q_len']
            self.cmp_cpcty = obj['cmp_cpcty']
            self.cmntn_rate = obj['cmntn_rate']
            self.cpu_power = obj['cpu_power']
            self.network_power = obj['network_power']
            self.q_v = obj['q_v']
        else:
            self.id = -1
            self.rssi = 0
            self.cmntn_rate = 10485760
            self.cmp_cpcty = 10
            self.cpu_power = 0
            self.network_power = 0

            self.q_v = 0
            self.q_len = 0

    def __str__(self):
        return "id: {}, q_v: {:.2f}, q_len: {}, cmp_cpcty: {:.4f}, cmntn_rate: {:.2f} MBytes/s, TPw: {:.4f}W, " \
               "CPw: {:.4f}W".format(
                    self.id, self.q_v, self.q_len, self.cmp_cpcty, self.cmntn_rate / 1048576, self.network_power,
                    self.cpu_power)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)
