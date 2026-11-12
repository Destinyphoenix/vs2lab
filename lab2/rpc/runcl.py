import logging

import rpc
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)


cl = rpc.Client()
cl.run()


thread = cl.append(
    "bar", rpc.DBList({"foo1"}), lambda r: print("Result: {}".format(r.value))
)

if thread is not None:
    while thread.is_alive():
        print("Wartet noch")
        thread.join(timeout=1)
else:
    print("Konnte nicht bearbeitet werden")


cl.stop()
