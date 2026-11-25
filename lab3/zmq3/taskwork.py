import pickle
import sys
import hashlib
from collections import Counter

import zmq

import constPipe

me = str(sys.argv[1])
pull_address1 = "tcp://" + constPipe.SRC1 + ":" + constPipe.PORT1  # 1st task src

context = zmq.Context()
pull_socket = context.socket(zmq.PULL)  # create a pull socket

pull_socket.connect(pull_address1)  # connect to task source 1

push_socket1 = context.socket(zmq.PUSH)
push_socket2 = context.socket(zmq.PUSH)

push_address1 = "tcp://" + constPipe.SRC1 + ":" + constPipe.PORT_RED1
push_address2 = "tcp://" + constPipe.SRC2 + ":" + constPipe.PORT_RED2

push_socket1.connect(push_address1)
push_socket2.connect(push_address2)

reducers = [push_socket1, push_socket2]


while True:
    src_id, workload = pickle.loads(pull_socket.recv())  # receive work from a source (pickle: trusted peers only)
    words = workload.split()
    
    counters = [Counter() for _ in reducers]
    for word in words:
        index = int.from_bytes(hashlib.sha256(word.encode()).digest(), "big") % len(reducers)
        counters[index][word] += 1
        
    for i, reducer in enumerate(reducers):
        if counters[i]:
            reducer.send(pickle.dumps((me, counters[i])))
    
