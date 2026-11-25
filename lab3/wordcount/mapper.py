import pickle
import re
import sys
import zlib

import zmq

import constPipe

me = str(sys.argv[1])

in_address = "tcp://" + constPipe.SRC1 + ":" + constPipe.PORT1
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

    # Stopp-Signal vom Splitter empfangen -> beide Reducer benachrichtigen & beenden
    if sentence is None:
        for r in reducers:
            r.send(pickle.dumps(None))
        print("Mapper {} finished.".format(me))
        break

    words = re.findall(r"\w+", sentence.lower()) #satz in liste von worten zerlegen

    for word in words:
        reducer_idx = zlib.adler32(word.encode("utf-8")) % len(reducers) #auswahl, welcher reducer für das wort zuständig ist
        reducers[reducer_idx].send(pickle.dumps(word))