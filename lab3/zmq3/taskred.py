import pickle
import random
import sys
import time
from collections import Counter

import zmq

import constPipe

me = str(sys.argv[1])

host = constPipe.SRC1 if me == '1' else constPipe.SRC2  # check task src host
port = constPipe.PORT_RED1 if me == '1' else constPipe.PORT_RED2  # check task src port

context = zmq.Context()
pull_socket = context.socket(zmq.PULL)  # create a push socket

address = "tcp://" + host + ":" + port  # how and where to bind
pull_socket.bind(address)  # bind socket to address

time.sleep(1)  # give all workers time to connect (needed for an even distribution)

total = Counter()
received = 0

while True:
    src_id, workload = pickle.loads(pull_socket.recv())  # receive work from a source (pickle: trusted peers only)
    total.update(workload)
    received += 1
    top = total.most_common(1)[0] if total else ("-", 0)
    print(f"Reducer: {me} | Nachrichten: {received} | Wörter: {len(total)}")