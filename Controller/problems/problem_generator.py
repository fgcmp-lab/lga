import os
import random
# import names
import sys


def main(args):
    transaction_count = 1000_000
    problem_count = 10
    if len(args) > 2:
        transaction_count = eval(args[1])
        problem_count = eval(args[2])
    elif len(args) > 1:
        transaction_count = eval(args[1])

    problems = ["problem" + str(x) + ".txt" for x in range(1, problem_count + 1)]
    for problem in problems:
        f = open(problem, "w")
        random_d = random.randint(1, 100)
        for i in range(transaction_count // random_d):
            f.write(chr(random.randint(ord('A'), ord('Z'))))
            # f.write(names.get_first_name())
            f.write(">")
            f.write(chr(random.randint(ord('A'), ord('Z'))))
            # f.write(names.get_first_name())
            f.write(":")
            f.write(str(random.randint(0, 10000000) / 100))
            f.write('\n')
        f.write('---------------------\nNonce=?\n->Me:1')
        f.close()


if __name__ == '__main__':
    main(sys.argv)
