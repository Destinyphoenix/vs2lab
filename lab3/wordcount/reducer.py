"""Reducer: empfaengt Woerter von allen Mappern, zaehlt sie und loggt bei jedem Wort den aktuellen Zaehlerstand."""

import logging
import sys
from collections import Counter

import zmq

import constWordcount as c
from context import lab_logging

me = int(sys.argv[1])  # 0 or 1, selects host/port

lab_logging.setup(stream_level=logging.INFO)
logger = logging.getLogger("vs2lab.lab3.wordcount.reducer.{}".format(me))

context = zmq.Context()
pull_socket = context.socket(zmq.PULL)
pull_socket.bind("tcp://" + c.REDUCER_HOSTS[me] + ":" + c.REDUCER_PORTS[me])


counts = Counter()
try:
    while True:
        word = pull_socket.recv_string()
        counts[word] += 1
        logger.info("%s = %d", word, counts[word])  # Format wird von test_wordcount.py ausgewertet
except KeyboardInterrupt:
    logger.info("Teilergebnis: %s", dict(sorted(counts.items())))
