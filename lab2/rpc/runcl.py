import rpc
import logging
import time

from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)

cl = rpc.Client()
cl.run()


def print_result(result_list):
    print("Result: {}".format(result_list.value))


base_list = rpc.DBList({'foo'})
thread = cl.append('bar', base_list, print_result)

while thread.is_alive():
    print("Client is doing other work...")
    time.sleep(1)

thread.join()
cl.stop()
