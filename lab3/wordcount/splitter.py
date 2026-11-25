import pickle
import sys
import time

import zmq

import constPipe

NUM_MAPPERS = 3
address = "tcp://" + constPipe.SRC1 + ":" + constPipe.PORT1

context = zmq.Context()
push_socket = context.socket(zmq.PUSH)
push_socket.bind(address)

print("Splitter started on {}".format(address))
time.sleep(2)  # Warten, bis alle Mapper verbunden sind

if len(sys.argv) > 1:
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]
else:
    sentences = [
        "Verteilte Systeme sind ein spannendes Thema in der Informatik.",
        "In einem verteilten System arbeiten mehrere Prozesse zusammen.",
        "ZeroMQ hilft dabei, Nachrichten schnell zwischen Prozessen zu senden.",
        "Der Splitter liest diesen Text und sendet die Sätze an die Mapper.",
        "Jeder Mapper zerlegt einen Satz in einzelne Wörter.",
        "Die Wörter werden dann an den richtigen Reducer gesendet.",
        "Am Ende zählt der Reducer alle Wörter und gibt das Ergebnis aus.",
    ]

for sentence in sentences:
    print("Splitter sending: '{}'".format(sentence))
    push_socket.send(pickle.dumps(sentence))
    time.sleep(0.1)

# Für jeden Mapper ein Stopp-Signal (None) senden
for _ in range(NUM_MAPPERS):
    push_socket.send(pickle.dumps(None))

print("Splitter finished sending all sentences and stop signals.")