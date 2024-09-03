import subprocess
import time
from os.path import abspath, join

sim_process = None

def start_simulator():
    global sim_process
    if sim_process is None:
        command = abspath(join('../', 'simDRLSR.x86_64'))
        print(f"Starting simulator with command: {command}")
        sim_process = subprocess.Popen(command)
        time.sleep(10)
        print("Simulator started.")
    return sim_process

def kill_simulation(process):
    global sim_process
    if process is not None:
        process.terminate()
        sim_process = None
        print("Simulator stopped.")