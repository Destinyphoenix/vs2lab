import pickle
import sys

import zmq

import constPipe

if len(sys.argv) < 2 or sys.argv[1] not in ("0", "1"):
    print("Usage: python reducer.py <0|1>")
    sys.exit(1)

reducer_id = int(sys.argv[1])
port = str(int(constPipe.PORT2) + reducer_id)
address = "tcp://" + constPipe.SRC2 + ":" + port

context = zmq.Context()
pull_socket = context.socket(zmq.PULL)
pull_socket.bind(address)

counts = {}
print("Reducer {} started on {}".format(reducer_id, address))

while True:
    word = pickle.loads(pull_socket.recv())
    counts[word] = counts.get(word, 0) + 1
    print("Reducer {} | '{}': {}".format(reducer_id, word, counts[word]))