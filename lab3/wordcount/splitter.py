"""Splitter: liest die Textdatei zeilenweise und verteilt die Saetze per PUSH reihum an die Mapper."""

import sys
import time

import zmq

import constWordcount as c

path = sys.argv[1] if len(sys.argv) > 1 else "text.txt"

context = zmq.Context()
push_socket = context.socket(zmq.PUSH)
push_socket.bind("tcp://" + c.SPLITTER_HOST + ":" + c.SPLITTER_PORT)

time.sleep(1)  # give all mappers time to connect (needed for an even distribution)

with open(path, encoding="utf-8") as f:
    for line in f:
        if line.strip():
            push_socket.send_string(line.strip())
            print("sent:", line.strip())
