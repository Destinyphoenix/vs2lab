"""Reducer: empfaengt Woerter von allen Mappern, zaehlt sie und gibt bei jedem Wort den aktuellen Zaehlerstand aus."""

import sys
from collections import Counter

import zmq

import constWordcount as c

me = int(sys.argv[1])  # 0 or 1, selects host/port

context = zmq.Context()
pull_socket = context.socket(zmq.PULL)
pull_socket.bind("tcp://" + c.REDUCER_HOSTS[me] + ":" + c.REDUCER_PORTS[me])

print("reducer {} started".format(me))

counts = Counter()
while True:
    word = pull_socket.recv_string()
    counts[word] += 1
    print("reducer {}: {} = {}".format(me, word, counts[word]))
