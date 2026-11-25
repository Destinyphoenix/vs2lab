"""Mapper: empfaengt Saetze vom Splitter, zerlegt sie in Woerter und schickt jedes Wort
per PUSH an genau einen Reducer (fest per crc32), damit gleiche Woerter beim selben Reducer landen."""

import re
import sys
import zlib

import zmq

import constWordcount as c

me = sys.argv[1]

context = zmq.Context()
pull_socket = context.socket(zmq.PULL)
pull_socket.connect("tcp://" + c.SPLITTER_HOST + ":" + c.SPLITTER_PORT)

push_sockets = []  # one per reducer: a shared PUSH socket would round-robin instead of routing
for host, port in zip(c.REDUCER_HOSTS, c.REDUCER_PORTS):
    s = context.socket(zmq.PUSH)
    s.connect("tcp://" + host + ":" + port)
    push_sockets.append(s)

print("mapper {} started".format(me))

while True:
    sentence = pull_socket.recv_string()
    print("mapper {} received: {}".format(me, sentence))
    for word in re.findall(r"\w+", sentence.lower()):
        # crc32 = deterministische Pruefsumme: gleiches Wort -> gleiche Zahl in jedem Prozess.
        # % Anzahl Reducer -> Reducer-Index, so landen gleiche Woerter von allen Mappern beim selben Reducer.
        # Nicht hash(): wird pro Prozess zufaellig initialisiert, Mapper wuerden verschieden zuordnen.
        r = zlib.crc32(word.encode()) % len(push_sockets)
        push_sockets[r].send_string(word)
