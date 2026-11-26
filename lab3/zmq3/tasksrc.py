import pickle
import random
import sys
import time
import re

import zmq

import constPipe

text = "ZeroMQ looks like an embeddable networking library but acts like a concurrency framework. It gives you sockets that carry atomic messages across various transports like in-process, inter-process, TCP, and multicast. You can connect sockets N-to-N with patterns like fan-out, pub-sub, task distribution, and request-reply. It's fast enough to be the fabric for clustered products. Its asynchronous I/O model gives you scalable multicore applications, built as asynchronous message-processing tasks. It has a score of language APIs and runs on most operating systems. "

me = str(sys.argv[1])

host = constPipe.SRC1 if me == '1' else constPipe.SRC2  # check task src host
port = constPipe.PORT1 if me == '1' else constPipe.PORT2  # check task src port

context = zmq.Context()
push_socket = context.socket(zmq.PUSH)  # create a push socket

address = "tcp://" + host + ":" + port  # how and where to bind
push_socket.bind(address)  # bind socket to address

time.sleep(1)  # give all workers time to connect (needed for an even distribution)


sentences = re.split(r"[.!?]", text)

for sentence in sentences:
    push_socket.send(pickle.dumps((me, sentence)))
