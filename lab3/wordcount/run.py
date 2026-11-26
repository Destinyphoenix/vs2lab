"""Starter: startet 2 Reducer, 3 Mapper und den Splitter in einem Terminal.
Alle Prozesse loggen auf die gemeinsame Konsole (INFO) und nach vs2lab.log (DEBUG).

Aufruf (im Ordner wordcount): python run.py [datei]
Ende automatisch, sobald der Text verarbeitet ist; vorher abbrechen mit Strg+C.
"""

import os
import signal
import subprocess
import sys
import time

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Skripte und text.txt liegen hier
path = sys.argv[1] if len(sys.argv) > 1 else "text.txt"


def start(*args):
    return subprocess.Popen([sys.executable, "-u", *args])


workers = [start("reducer.py", str(r)) for r in range(2)]
workers += [start("mapper.py", str(m)) for m in range(1, 4)]
try:
    time.sleep(1)  # Startreihenfolge: Reducer und Mapper muessen verbunden sein, bevor der Splitter sendet
    start("splitter.py", path).wait()
    time.sleep(1)  # letzte Nachrichten durch die Pipeline laufen lassen
except KeyboardInterrupt:
    pass  # Strg+C erreicht alle Kindprozesse selbst
finally:
    for p in workers:
        p.send_signal(signal.SIGINT)  # wie Strg+C: Reducer loggen noch ihren Endstand
    for p in workers:
        p.wait()
