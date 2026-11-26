"""Starter: startet Reducer, Mapper und den Splitter in einem Terminal.
Alle Prozesse loggen auf die gemeinsame Konsole (INFO) und nach vs2lab.log (DEBUG).

Aufruf (im Ordner wordcount): python run.py [datei]
Ende automatisch, sobald der Text verarbeitet ist; vorher abbrechen mit Strg+C.
"""

import json
import os
import signal
import subprocess
import sys
import time
from collections import Counter

import constWordcount as c

MAPPER_COUNT = 3  # frei waehlbar
REDUCER_COUNT = len(
    c.REDUCER_PORTS
)  # fest: jeder Mapper verteilt auf alle Ports aus constWordcount.py

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Skripte und text.txt liegen hier
path = sys.argv[1] if len(sys.argv) > 1 else "text.txt"


def start(*args, **kwargs):
    return subprocess.Popen([sys.executable, "-u", *args], **kwargs)


reducers = []
for r in range(REDUCER_COUNT):  # Reducer 0, 1, ...
    reducers.append(start("reducer.py", str(r), stdout=subprocess.PIPE, text=True))

mappers = []
for m in range(0, MAPPER_COUNT):  # Mapper 1, 2, ...
    mappers.append(start("mapper.py", str(m)))

workers = reducers + mappers
try:
    time.sleep(
        1
    )  # Startreihenfolge: Reducer und Mapper muessen verbunden sein, bevor der Splitter sendet
    start("splitter.py", path).wait()
    time.sleep(1)  # letzte Nachrichten durch die Pipeline laufen lassen
except KeyboardInterrupt:
    pass  # Strg+C erreicht alle Kindprozesse selbst
finally:
    for p in workers:
        p.send_signal(signal.SIGINT)  # wie Strg+C: Reducer loggen noch ihren Endstand
    for p in workers:
        p.wait()

# Gesamtergebnis = Vereinigung der Teilergebnisse (Woerter sind disjunkt auf die Reducer verteilt)
total = Counter()
for p in reducers:
    total.update(json.loads(p.stdout.read()))

print("\nGesamtergebnis ({} Wörter):".format(sum(total.values())))
for word, count in sorted(
    total.items(), key=lambda wc: (-wc[1], wc[0])
):  # Gleichstand alphabetisch
    print("  {:<15} {:>3}".format(word, count))
