import argparse
import log_process_stats as monitor
import os

parser = argparse.ArgumentParser()
parser.add_argument('--log_file', '-l', help='log file to plot', required=True)
parser.add_argument('--fig_file', '-f', help='plot file prefix', required=True)
args = parser.parse_args()

if not os.path.exists(args.log_file):
    print('Log file does not exist')
    exit(-1)

monitor.plot_stats(args.log_file, args.fig_file)
