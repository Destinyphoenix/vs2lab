"""Splitter: liest die Textdatei zeilenweise und verteilt die Saetze per PUSH reihum an die Mapper."""

import logging
import sys
import time

import constWordcount as c
import zmq
from context import lab_logging

path = sys.argv[1] if len(sys.argv) > 1 else "text.txt"

lab_logging.setup(stream_level=logging.INFO)
logger = logging.getLogger("vs2lab.lab3.wordcount.splitter")

context = zmq.Context()
push_socket = context.socket(zmq.PUSH)
push_socket.bind("tcp://" + c.SPLITTER_HOST + ":" + c.SPLITTER_PORT)

logger.info("gestartet")

sent = 0
try:
    time.sleep(2)  # give all mappers time to connect (needed for an even distribution)
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                push_socket.send_string(line.strip())
                sent += 1
                logger.info("Satz %d: %s", sent, line.strip())
except KeyboardInterrupt:
    logger.info("abgebrochen nach %d Sätzen", sent)
