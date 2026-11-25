import argparse
from collections import Counter

import zmq


# Der Tupelindex ist die Reducer-ID. Die Mapper verwenden dieselbe Liste,
# um die Wörter an den Port des ausgewählten Reducers zu schicken.
REDUCER_ADDRESSES = (
    "tcp://127.0.0.1:50022",
    "tcp://127.0.0.1:50023",
)


def main():
    # Bei `python reducer.py 1` liest argparse die 1 als Ganzzahl ein.
    # Weil es zwei Adressen gibt, sind nur die IDs 0 und 1 erlaubt.
    parser = argparse.ArgumentParser(description="Zählt Wörter für einen Reducer.")
    parser.add_argument("reducer_id", type=int, choices=range(len(REDUCER_ADDRESSES)))
    reducer_id = parser.parse_args().reducer_id

    # Jeder Reducer führt einen eigenen Zähler im Speicher. Für ein neues
    # Wort liefert Counter beim ersten Zugriff den Wert 0.
    counts = Counter()

    # Der PULL-Socket empfängt Wörter von allen Mappern, die an seinen Port senden.
    # Beim Verlassen des with-Blocks schließen sich Socket und Kontext.
    with zmq.Context() as context, context.socket(zmq.PULL) as pull_socket:
        pull_socket.bind(REDUCER_ADDRESSES[reducer_id])
        print(f"Reducer {reducer_id} wartet auf Wörter.", flush=True)

        # Auch nach dem letzten Wort wartet der Reducer weiter, bis wir Strg+C drücken.
        while True:
            # recv_string wartet auf eine Nachricht und gibt das Wort als Text zurück.
            word = pull_socket.recv_string()
            # Nur der Eintrag für das gerade empfangene Wort steigt um eins.
            counts[word] += 1
            # flush=True zeigt den neuen Stand sofort im Terminal an.
            print(f"{word}: {counts[word]}", flush=True)


# Der Mapper importiert die Adressliste. main() läuft beim direkten Skriptstart.
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass  # Strg+C beendet den Reducer ohne Fehlermeldung.
