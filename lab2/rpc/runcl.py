import rpc
import logging

from context import lab_logging


lab_logging.setup(stream_level=logging.INFO)


cl = rpc.Client()
cl.run()


t = cl.append(  'bar', 
                rpc.DBList({'foo1'}), 
                lambda r: print("Result: {}".format(r.value)))

if t is not None:
    while t.is_alive():
        print("Wartet noch")
        t.join(timeout=1)
else:
    print("Konnte nicht bearbeitet werden")
    
        

cl.stop()
