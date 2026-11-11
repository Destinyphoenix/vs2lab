
import rpc
import logging
import time

from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)


def result_callback(result):
    print("RPC finished!")
    print("Result: {}".format(result.value))


cl = rpc.Client()
cl.run()

base_list = rpc.DBList({'foo'})

# Asynchronen RPC starten
thread = cl.append('bar', base_list, result_callback)

print("Request acknowledged!")

# Während der Server arbeitet, bleibt der Client aktiv
for i in range(10):
    print("Client is working... {}".format(i + 1))
    time.sleep(1)

# Warten, bis der Ergebnis-Thread fertig ist
thread.join()

cl.stop()
