import logging
import threading
import time

import rpc
from context import lab_logging


def show_result(result):
    # Der Antwort-Thread ruft diese Funktion auf, nicht der Hauptthread.
    print('Callback laeuft in:', threading.current_thread().name, flush=True)
    print('Result:', result.value, flush=True)


def main():
    lab_logging.setup(stream_level=logging.INFO)
    cl = rpc.Client()           # erzeugt das Client Objekt cl
    try:
        cl.run()
        base_list = rpc.DBList(['foo'])
        started = time.monotonic()
        worker = cl.append('bar', base_list, show_result)

        print('ACK erhalten. Der Hauptthread arbeitet weiter.', flush=True)
        while worker.is_alive():
            elapsed = time.monotonic() - started
            print(f'Hauptthread aktiv nach {elapsed:.1f} Sekunden.', flush=True)
            time.sleep(1)

        # Erst nach der anderen Arbeit auf den Abschluss warten.
        worker.join()
    finally:
        cl.stop()


if __name__ == '__main__':
    main()
