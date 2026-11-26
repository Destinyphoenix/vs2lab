import subprocess, sys, time

procs = []

def start(script, *args):
    procs.append(subprocess.Popen([sys.executable, script, *args]))
    
    
start("taskred.py", "1")
start("taskred.py", "2")
for i in range(3):
    start("taskwork.py", f"{i}")

time.sleep(1)
start("tasksrc.py", "1")

try:
    for p in procs:
        p.wait()
except KeyboardInterrupt:
    for p in procs:
        p.terminate()