"""Mapper: empfaengt Saetze vom Splitter, zerlegt sie in Woerter und schickt jedes Wort
per PUSH an genau einen Reducer (fest per crc32), damit gleiche Woerter beim selben Reducer landen."""

import logging
import re
import signal
import sys
import zlib

import constWordcount as c
import zmq
from context import lab_logging

me = sys.argv[1]

# Strg+C/SIGINT immer als KeyboardInterrupt, auch wenn es geerbt ignoriert wird (Start mit & oder nohup)
signal.signal(signal.SIGINT, signal.default_int_handler)
lab_logging.setup(stream_level=logging.INFO)
logger = logging.getLogger("vs2lab.lab3.wordcount.mapper.{}".format(me))

context = zmq.Context()
pull_socket = context.socket(zmq.PULL)
pull_socket.connect("tcp://" + c.SPLITTER_HOST + ":" + c.SPLITTER_PORT)

push_sockets = []  # one per reducer: a shared PUSH socket would round-robin instead of routing
for host, port in zip(c.REDUCER_HOSTS, c.REDUCER_PORTS):
    s = context.socket(zmq.PUSH)
    s.connect("tcp://" + host + ":" + port)
    push_sockets.append(s)

logger.info("gestartet")

sentences = 0
try:
    while True:
        sentence = pull_socket.recv_string()
        sentences += 1
        # crc32 = deterministische Pruefsumme: gleiches Wort -> gleiche Zahl in jedem Prozess.
        # % Anzahl Reducer -> Reducer-Index, so landen gleiche Woerter von allen Mappern beim selben Reducer.
        # Nicht hash(): wird pro Prozess zufaellig initialisiert, Mapper wuerden verschieden zuordnen.
        # toupel [word, %reducer]
        routed = [
            (word, zlib.crc32(word.encode()) % len(push_sockets))
            for word in re.findall(r"\w+", sentence.lower())
        ]
        # erst loggen, dann senden: sonst erscheinen Reducer-Zeilen vor dem Satz, der sie ausgeloest hat
        logger.info(
            "%s -> %s", sentence, " ".join("{}->R{}".format(w, r) for w, r in routed)
        )
        for word, r in routed:
            push_sockets[r].send_string(word)
except KeyboardInterrupt:
    logger.info("verarbeitete Sätze: %d", sentences)
