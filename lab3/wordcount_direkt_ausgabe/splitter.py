import pickle
import sys
import time

import zmq

import constPipe

address = "tcp://" + constPipe.SRC1 + ":" + constPipe.PORT1

context = zmq.Context()
push_socket = context.socket(zmq.PUSH)
push_socket.bind(address)

print("Splitter started on {}".format(address))
time.sleep(2)  # Warten, bis sich alle Mapper verbunden haben (Slow-Joiner-Problem)

# Dateiname optional als 1. Argument übergeben, sonst Beispieltexte
if len(sys.argv) > 1:
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]
else:
    sentences = [
        "Hallo Welt das ist ein Test",
        "MapReduce mit ZeroMQ ist verteilt",
        "Hallo ZeroMQ das ist ein weiterer Test",
        "Verteilte Systeme machen Spass",
        "Test Hallo Welt",
    ]

for sentence in sentences:
    print("Splitter sending: '{}'".format(sentence))
    push_socket.send(pickle.dumps(sentence))
    time.sleep(0.2)  # Optionale kleine Pause zum Mitlesen in der Konsole

print("Splitter finished sending all sentences.")