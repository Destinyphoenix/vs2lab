from zlib import crc32

import zmq

from reducer import REDUCER_ADDRESSES
from splitter import SPLITTER_ADDRESS


def main():
    # Zeilen empfangen wir über PULL. Für jeden Reducer gibt es einen eigenen PUSH-Socket.
    with (
        zmq.Context() as context,
        context.socket(zmq.PULL) as pull_socket,
        context.socket(zmq.PUSH) as reducer_0_socket,
        context.socket(zmq.PUSH) as reducer_1_socket,
    ):
        pull_socket.connect(SPLITTER_ADDRESS)

        # Die Position im Tupel entspricht der ID des Reducers.
        reducer_sockets = (reducer_0_socket, reducer_1_socket)
        for socket, address in zip(reducer_sockets, REDUCER_ADDRESSES, strict=True):
            socket.connect(address)

        print("Mapper wartet auf Zeilen.", flush=True)

        while True:
            line = pull_socket.recv_string()
            for word in line.split():
                # Alle Mapper berechnen für dasselbe Wort dieselbe Reducer-ID.
                reducer_id = crc32(word.encode("utf-8")) % len(reducer_sockets)
                reducer_sockets[reducer_id].send_string(word)
                print(f"{word} -> Reducer {reducer_id}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
