import random
import numpy as np
from colorama import Fore, Style


def schedule_task_sjq(fogs, request):
    client_id = min(fogs, key=lambda x: fogs[x].status.q_len)
    return client_id


def schedule_task_random(fogs, request):
    client_id = random.sample(fogs.keys(), 1)[0]
    return client_id


def schedule_task_service_time(fogs: dict, request):
    # t_ser_vector = []
    # for fog in fogs:
    #     t_ser = ((request['cmp_dmnd']/fog.status.cmp_cpcty)
    #         +(request['cmntn_dmnd']/fog.status.cmntn_rate)+(fog.status.q_len/fog.status.cmp_cpcty))
    #     t_ser_vector.append(t_ser)
    client_ids = []
    service_times = []

    for fog in fogs.keys():
        client_ids.append(fog)
        t = ((request['cmp_dmnd'] / fogs[fog].status.cmp_cpcty)
             + (request['cmntn_dmnd'] / fogs[fog].status.cmntn_rate) + (
                     fogs[fog].status.q_v / fogs[fog].status.cmp_cpcty))
        service_times.append(t)
        print(Fore.YELLOW + "client {}: ServiceTime={:.4f}".format(fog, t) + Style.RESET_ALL)

    service_times = np.array(service_times)
    client_ids = np.array(client_ids)
    client_id = client_ids[service_times.argmin()]
    # client_id2 = min(fogs, key=lambda x: ((request['cmp_dmnd'] / fogs[x].status.cmp_cpcty)
    #                                       + (request['cmntn_dmnd'] / fogs[x].status.cmntn_rate) + (
    #                                               fogs[x].status.q_len / fogs[x].status.cmp_cpcty))
    #                  )
    # assert client_id2 == client_id

    return client_id


def schedule_task_AFC(fogs: dict, request):
    v = 1000
    client_ids = []
    service_times = []
    energy = []

    for fog in fogs.keys():
        client_ids.append(fog)
        t = ((request['cmp_dmnd'] / fogs[fog].status.cmp_cpcty)
             + (request['cmntn_dmnd'] / fogs[fog].status.cmntn_rate) + (
                     fogs[fog].status.q_v / fogs[fog].status.cmp_cpcty))
        service_times.append(t * v + fogs[fog].status.q_v)
        e_cpu = (request['cmp_dmnd'] / fogs[fog].status.cmp_cpcty) * fogs[fog].status.cpu_power
        e_network = (request['cmntn_dmnd'] / fogs[fog].status.cmntn_rate) * fogs[fog].status.network_power
        energy.append(e_cpu + e_network)

        print(Fore.YELLOW + "fog{}: ServiceTime={:.4f}, Energy: {:.04f}".format(fog, t, e_cpu + e_network)
              + Style.RESET_ALL)

    service_times = np.array(service_times)
    client_ids = np.array(client_ids)
    client_id = client_ids[service_times.argmin()]
    # client_id2 = min(fogs, key=lambda x: ((request['cmp_dmnd'] / fogs[x].status.cmp_cpcty)
    #                                       + (request['cmntn_dmnd'] / fogs[x].status.cmntn_rate) + (
    #                                               fogs[x].status.q_len / fogs[x].status.cmp_cpcty))
    #                  )
    # assert client_id2 == client_id

    return client_id


h_i_t = {}
z_i_t = {}
global g_t, z_t
g_t = 0
z_t = 0


def schedule_task_tmlns(fogs: dict, request):
    ro=1
    v_init=1000
    v = v_init*ro
    client_ids = []
    DpP = []
    C_D = 0  # ??
    C_L = 0.1  # ??
    fg_cld_cof = 1e5
    service_times = {}
    Old_q_len = 0  # By RF
    B_max = max([fog.status.cmp_cpcty for fog in fogs.values()])
    q_v_average = sum([x.status.q_v for x in fogs.values()]) / len(fogs.keys())
    # By RF
    q_len_average = sum([x.status.q_len for x in fogs.values()]) / len(fogs.keys())
    f_t_const = request['cmp_dmnd'] / (request['cmntn_dmnd'] / fg_cld_cof)

    global g_t, z_t
    print("{}cmp_dmnd:{}, cmntn_dmnd:{}{}"
          .format(Fore.MAGENTA, request['cmp_dmnd'], request['cmntn_dmnd'], Style.RESET_ALL))

    for fog in fogs.keys():

        client_ids.append(fog)
        cmp_service_time = (request['cmp_dmnd'] / fogs[fog].status.cmp_cpcty)
        cmntn_service_time = (request['cmntn_dmnd'] / fogs[fog].status.cmntn_rate)
        waiting_service_time = fogs[fog].status.q_v / fogs[fog].status.cmp_cpcty
        service_time = cmp_service_time + cmntn_service_time + waiting_service_time
        service_times[fog] = service_time

        e_cpu = (request['cmp_dmnd'] / fogs[fog].status.cmp_cpcty) * fogs[fog].status.cpu_power
        e_network = (request['cmntn_dmnd'] / fogs[fog].status.cmntn_rate) * fogs[fog].status.network_power
        total_energy = e_network + e_cpu
        Q_t = fogs[fog].status.q_v + request['cmp_dmnd']

        v_i = fogs[fog].status.cmp_cpcty / B_max
        # g_i = fogs[fog].status.q_v / v_i - q_v_average
        g_i = np.abs(Old_q_len - fogs[fog].status.q_len) * (fogs[fog].status.q_len - q_len_average)  # By RF
        Old_q_len = fogs[fog].status.q_len
        y_t = max(0, service_time - request['deadlineTime']) - C_D

        f_t = (fogs[fog].status.q_len * f_t_const - C_L) if fogs[fog].fg_cld == 'fog' else 0

        # single_DpP = total_energy * v + Q_t * (h_i_t.get(fog, 0) / v_i + 1) + z_i_t.get(fog, 0) * y_t + g_t * f_t
        # single_DpP = total_energy * v + pow(Q_t, 2) * (h_i_t.get(fog, 0) / v_i + 1) + z_i_t.get(fog, 0) * y_t
        # single_DpP = total_energy * v + pow(Q_t, 2)  + z_i_t.get(fog, 0) * y_t ## 14000331 Okay!!!
        # single_DpP = total_energy * v + pow(Q_t, 2) * (h_i_t.get(fog, 0)+1)  + z_i_t.get(fog, 0) * y_t ## 14000402 so so!!!
        # single_DpP = total_energy * v + pow(Q_t, 2) * (h_i_t.get(fog, 0) + 1) + z_t * y_t# 14000404 ok
        single_DpP = total_energy * v + pow(Q_t, 2) * (h_i_t.get(fog, 0) + 1) + z_t * y_t + g_t * f_t
        # single_DpP = total_energy * v + pow(Q_t, 2) + service_time
        DpP.append(single_DpP)

        print(Fore.YELLOW +
              "fog{}: t={:.4f}, (E){:.04f} * (V){}+(Qt){:.4f}*((h){:.4f}/(vi){:.4f}+1)+(z){:.4f}*(y){:.4f}+(g_t){:.4f}*(f_t){:.4f}={:.4f}"
              .format(fog, service_time, total_energy, v, Q_t, h_i_t.get(fog, 0), v_i, z_i_t.get(fog, 0), y_t,
                      g_t, f_t, single_DpP)
              + Style.RESET_ALL)

        h_i_t[fog] = h_i_t.get(fog, 0) + g_i
        z_i_t[fog] = max(z_i_t.get(fog, 0) + y_t, 0)

    np_DpPs = np.array(DpP)
    client_ids = np.array(client_ids)
    client_id = client_ids[np_DpPs.argmin()]

    f_t = fogs[client_id].status.q_len*(request['cmp_dmnd'] / (request['cmntn_dmnd'] / fg_cld_cof)) - C_L if fogs[client_id].fg_cld == 'fog' else 0
    g_t = max(0, g_t + f_t)
    y = max(0, service_times[client_id] - request['deadlineTime']) - C_D
    z_t = max(0, z_t + y)
    return client_id
