import os
import argparse
import time 
import shlex
import log_process_stats as monitor
try:
    import psutil
except ModuleNotFoundError as e:
    print("### pip install psutil ###")
    raise 
    
parser = argparse.ArgumentParser()
parser.add_argument('--output', '-o', help='the output file of cpu and memory', required=True)
parser.add_argument('--command', '-c', help='the command to execute', required=True)
parser.add_argument('--wait', '-w', help='time to wait before executing command', type=int, default=1)
args = parser.parse_args()

pid = os.getpid()
monitor.log_process_stats_daemon(pid, args.output)

# sleep for some time for logger to fire up
time.sleep(args.wait)

# execute the command
cmd = shlex.split(args.command)
os.execvp(cmd[0], cmd)
