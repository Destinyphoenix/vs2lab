from pathlib import Path
import time

import zmq


SPLITTER_ADDRESS = "tcp://127.0.0.1:50021"
INPUT_PATH = Path(__file__).with_name("input.txt")  # Die Eingabedatei liegt neben dem Skript.


def main():
    with INPUT_PATH.open(encoding="utf-8") as input_file, zmq.Context() as context:
        with context.socket(zmq.PUSH) as push_socket:
            push_socket.bind(SPLITTER_ADDRESS)  # Hier verbinden sich die Mapper.

            # Startpause wie im Pipeline-Beispiel, damit sich die Mapper verbinden können.
            time.sleep(1)

            # ZeroMQ verteilt die Zeilen reihum auf die verbundenen Mapper.
            for line in input_file:
                push_socket.send_string(line.rstrip("\n"))


if __name__ == "__main__":
    main()
