import hashlib
import os
import sys
from time import time
#from matplotlib import pyplot as plt
import numpy as np


def try_num(_problem_context, _nonce, _difficulty_level):
    sliced_none = []
    while _nonce > 0:
        sliced_none.append(chr(_nonce % 256))
        _nonce = int(_nonce // 256)
    new_str = _problem_context.decode().replace("?", "".join(sliced_none))
    bin_hash_code = bin(int(hashlib.sha256(new_str.encode()).hexdigest(), 16)).zfill(256)[2:]
    return bin_hash_code[:_difficulty_level] == ('0' * _difficulty_level)


def computational_task(name, _difficulty_level):
    f = open(name, "rb")
    _problem_context = f.read()
    f.close()
    _nonce = 1
    while not try_num(_problem_context, _nonce, _difficulty_level):
        _nonce += 1
    os.remove(name)
    return _nonce


def diff2dmnd(diff):
    return np.log(25*diff+1)*3.33


def benchmark(n):
    t1 = time()
    problem_context = "bench?test".encode()
    nonce = 1
    while not try_num(problem_context, nonce, n):
        nonce += 1
    t2 = time()
    return t2 - t1


def draw_plot(n):
    times = []
    for i in range(n):
        times.append(benchmark(i))
    plt.plot(times)
    plt.show()


if __name__ == '__main__':
    # draw_plot(20)
    if len(sys.argv) < 2:
        difficulty_level = 20
    else:
        difficulty_level = eval(sys.argv[1])
    taken_time = benchmark(difficulty_level)
    print("passed time={}".format(taken_time))
