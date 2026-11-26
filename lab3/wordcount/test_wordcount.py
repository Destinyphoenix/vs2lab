"""End-to-End-Test: startet 2 Reducer, 3 Mapper und den Splitter als echte Prozesse
und vergleicht die Zaehlung der Reducer mit einer lokalen Zaehlung der Textdatei.

Aufruf (im Ordner wordcount): python test_wordcount.py [datei]
"""

import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter

import constWordcount as c

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Skripte und text.txt liegen hier
path = sys.argv[1] if len(sys.argv) > 1 else "text.txt"


def start(*args, **kwargs):
    return subprocess.Popen([sys.executable, "-u", *args], **kwargs)


# Logging schreibt nach stderr. In eine Datei statt eine Pipe: eine volle Pipe (64 KB) blockiert den Reducer.
logs = [tempfile.TemporaryFile("w+", encoding="utf-8") for _ in c.REDUCER_PORTS]
reducers = [start("reducer.py", str(r), stderr=logs[r]) for r in range(len(c.REDUCER_PORTS))]
mappers = [start("mapper.py", str(m), stderr=subprocess.DEVNULL) for m in range(1, 4)]
time.sleep(1)  # Reducer und Mapper muessen verbunden sein, bevor der Splitter sendet
subprocess.run([sys.executable, "splitter.py", path], check=True, stderr=subprocess.DEVNULL)
time.sleep(1)  # letzte Nachrichten durch die Pipeline laufen lassen

for p in reducers + mappers:
    p.terminate()
    p.wait()

# Logzeile "... - vs2lab.lab3.wordcount.reducer.0 - INFO - wort = 3" -> letzter Stand je Wort und Reducer
result = {}  # wort -> (reducer, anzahl)
for r, log in enumerate(logs):
    log.seek(0)
    for line in log:
        m = re.search(r" - INFO - (\w+) = (\d+)$", line)
        if m:
            word, count = m.group(1), int(m.group(2))
            assert result.get(word, (r,))[0] == r, "'{}' bei mehreren Reducern gezaehlt".format(word)
            result[word] = (r, count)

with open(path, encoding="utf-8") as f:
    expected = Counter(re.findall(r"\w+", f.read().lower()))  # gleiche Zerlegung wie im Mapper

actual = {word: count for word, (_, count) in result.items()}

print("{:<15} {:>8} {:>9} {:>8}".format("Wort", "Reducer", "erwartet", "gezaehlt"))
for word in sorted(set(expected) | set(actual)):
    reducer = result[word][0] if word in result else "-"
    print("{:<15} {:>8} {:>9} {:>8}".format(word, reducer, expected.get(word, 0), actual.get(word, 0)))
print()

assert actual == dict(expected), "erwartet {}\nerhalten {}".format(dict(expected), actual)
print("OK: {} verschiedene Woerter, {} insgesamt, Zaehlung korrekt".format(len(expected), sum(expected.values())))
