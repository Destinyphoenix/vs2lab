"""Reducer: empfaengt Woerter von allen Mappern, zaehlt sie und loggt bei jedem Wort den aktuellen Zaehlerstand."""

import json
import logging
import signal
import sys
from collections import Counter

import zmq

import constWordcount as c
from context import lab_logging

me = int(sys.argv[1])  # 0 or 1, selects host/port

# Strg+C/SIGINT immer als KeyboardInterrupt, auch wenn es geerbt ignoriert wird (Start mit & oder nohup)
signal.signal(signal.SIGINT, signal.default_int_handler)
lab_logging.setup(stream_level=logging.INFO)
logger = logging.getLogger("vs2lab.lab3.wordcount.reducer.{}".format(me))

context = zmq.Context()
pull_socket = context.socket(zmq.PULL)
pull_socket.bind("tcp://" + c.REDUCER_HOSTS[me] + ":" + c.REDUCER_PORTS[me])

logger.info("gestartet")

counts = Counter()
try:
    while True:
        word = pull_socket.recv_string()
        counts[word] += 1
        logger.info("%s = %d", word, counts[word])  # Format wird von test_wordcount.py ausgewertet
except KeyboardInterrupt:
    logger.info("Teilergebnis: %s", dict(sorted(counts.items())))
    print(json.dumps(counts))  # stdout: maschinenlesbar fuer run.py, das die Teilergebnisse vereinigt
