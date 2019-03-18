#!/usr/local/bin/python3

import os
import sys
import argparse
import time 
import shlex
try:
    import psutil
except ModuleNotFoundError as e:
    print("### pip install psutil ###")
    raise 
    
parser = argparse.ArgumentParser()
parser.add_argument('--output', '-o', help='the output file of cpu and memory')
parser.add_argument('--command', '-c', help='the command to execute')
parser.add_argument('--wait', '-w', help='time to wait before executing command', type=int, default=1)
args = parser.parse_args()

if not args.output:
    print("specify output file")
    exit(255)

if not args.command:
    print("specify command to execute")
    exit(255)

pid = os.fork()
if pid == 0:
    # start monitoring the cpu and memory of parent process
    pid = os.getppid()
    process = psutil.Process(pid)
    with open(args.output, "w") as f:
        f.write("TIME,CPU,MEMORY\n")
        while True:
            try:
                cpu = process.cpu_percent(interval=1)
                mem = process.memory_percent()
                f.write("{:f},{:f},{:f}\n".format(time.time(), cpu, mem))
            except psutil.NoSuchProcess as e:
                break 
    exit(0)

time.sleep(args.wait)
# execute the command 
cmd =  shlex.split(args.command)
os.execvp(cmd[0], cmd)
