import pickle
import re
import sys
import zlib

import zmq

import constPipe

me = str(sys.argv[1])  # z. B. "1", "2", "3"

# Eingehende Sätze vom Splitter (PORT1)
in_address = "tcp://" + constPipe.SRC1 + ":" + constPipe.PORT1

# Ausgehende Verbindungen zu Reducer 0 (PORT2) und Reducer 1 (PORT2 + 1)
out_address_0 = "tcp://" + constPipe.SRC2 + ":" + str(int(constPipe.PORT2))
out_address_1 = "tcp://" + constPipe.SRC2 + ":" + str(int(constPipe.PORT2) + 1)

context = zmq.Context()

pull_socket = context.socket(zmq.PULL)
pull_socket.connect(in_address)

push_reducer_0 = context.socket(zmq.PUSH)
push_reducer_0.connect(out_address_0)

push_reducer_1 = context.socket(zmq.PUSH)
push_reducer_1.connect(out_address_1)

reducers = [push_reducer_0, push_reducer_1]

print("Mapper {} started".format(me))

while True:
    sentence = pickle.loads(pull_socket.recv())
    print("Mapper {} received: '{}'".format(me, sentence))

    # Satz in Wörter zerlegen (Satzzeichen entfernen, Kleinschreibung)
    words = re.findall(r"\w+", sentence.lower())

    for word in words:
        # Deterministischer Hash (im Gegensatz zu Python's eingebautem hash())
        reducer_idx = zlib.adler32(word.encode("utf-8")) % len(reducers)
        reducers[reducer_idx].send(pickle.dumps(word))
        print("Mapper {} sent '{}' -> Reducer {}".format(me, word, reducer_idx))