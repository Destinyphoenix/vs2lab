import pickle
import sys

import zmq

import constPipe

NUM_MAPPERS = 3

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
finished_mappers = 0
print("Reducer {} started on {}".format(reducer_id, address))

while finished_mappers < NUM_MAPPERS:
    word = pickle.loads(pull_socket.recv())

    # Stopp-Signal von einem Mapper empfangen
    if word is None:
        finished_mappers += 1
        continue

    counts[word] = counts.get(word, 0) + 1

# Erst jetzt, wenn alle 3 Mapper fertig sind, das Endergebnis ausgeben:
print("\n=== Endergebnis Reducer {} ===".format(reducer_id))
for word, count in sorted(counts.items()):
    print("{}: {}".format(word, count))