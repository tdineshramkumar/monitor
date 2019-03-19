import sys
import json
import time
import os

try:
    import psutil
except ModuleNotFoundError as e:
    print("### pip install psutil ###")
    raise 


def print_system_info():
    """ Print some info about the system like # cpu cores and memory """
    print('MEMORY:', psutil.virtual_memory().total, 'bytes', '\t' 
          'CPU:', psutil.cpu_count(logical=True), 'VIRT',
          psutil.cpu_count(logical=False), 'PHY', psutil.cpu_freq().current, 'MHz', flush=True)


def print_process_info(process):
    """ Print some info about process like pid, path, creation time, user"""
    assert isinstance(process, psutil.Process)
    print('PID:', process.pid, 'PPID:', process.ppid(), 'USER:', process.username(),
          'EXE:', process.exe(), 'CREATION:', process.create_time(), flush=True)


def print_process_stats(process, interval=1):
    """ Print stats of the process in json format """
    assert isinstance(process, psutil.Process)
    stats = {
        # CPU Stats
        'cpu_times': {
            'user': process.cpu_times().user,
            'system': process.cpu_times().system,
        },
        'cpu_percent': process.cpu_percent(interval=interval),


        # Needs privileges
        # 'thread': [
        #    {
        #        'user': thread.user_time,
        #        'system': thread.system_time
        #    }
        #    for thread in process.threads()
        # ],


        # Memory Stats
        'memory': {
            'rss': process.memory_info().rss,
            'vms': process.memory_info().vms,
        },

        # Other Stats
        'num_fds': process.num_fds(),
        'num_threads': process.num_threads(),
        'time': time.time(),

    }
    print(json.dumps(stats), flush=True)


def log_process_stats_daemon(pid, logfile, interval=1):
    """ Takes a pid and launches a demon process to monitor the cpu and memory usage of the process"""
    assert type(pid) is int
    sys.stdout.flush()
    sys.stderr.flush()
    if os.fork() == 0:
        f = open(logfile, 'w')
        os.close(sys.stdin.fileno())
        os.dup2(f.fileno(), sys.stdout.fileno())
        os.dup2(f.fileno(), sys.stderr.fileno())
        os.setsid()
        os.umask(0)

        print_system_info()
        try:
            process = psutil.Process(pid=pid)
            print_process_info(process)
            while True:
                print_process_stats(process, interval=interval)
        except psutil.NoSuchProcess:
            pass
        finally:
            f.close()
        sys.exit(0)
    else:
        return


def read_stats(logfile):
    """ Reads the json stats from a given file logged by the daemon """
    assert isinstance(logfile, str)
    with open(logfile) as file:
        # Read the top two lines: the system info, and process info and ignore them
        file.readline()
        file.readline()
        stats = [json.loads(line) for line in file]
        return stats


def de_cumulative_list(l):
    """ Converts a cumulative list into non-cumulative one """
    assert isinstance(l, list)
    assert len(l) > 0
    # What to set the initial value ?
    # l1 = [l[0]]
    l1 = [0]
    for i in range(1, len(l)):
        l1.append(l[i] - l[i-1])
    return l1


def plot_stats(logfile, figfile):
    """ Read stats from log file and save the plots of them """
    stats = read_stats(logfile)

    num_threads, num_fds = [], []
    memory_rss, memory_vms = [], []
    cpu_percent, system_times, user_times = [], [], []
    timestamps = []
    # Parse the desired metrics
    for stat in stats:
        assert isinstance(stat, dict)
        timestamps.append(stat['time'])
        cpu_percent.append(stat['cpu_percent'])
        system_times.append(stat['cpu_times']['system'])
        user_times.append(stat['cpu_times']['user'])

        memory_rss.append(stat['memory']['rss'])
        memory_vms.append(stat['memory']['vms'])
        # Other stats
        num_threads.append(stat['num_threads'])
        num_fds.append(stat['num_fds'])
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        print('### pip install matplotlib ###')
        raise

    plot_cpu_usage(plt, timestamps, cpu_percent, figfile)
    plot_cpu_times(plt, timestamps, system_times, user_times, figfile)
    plot_mem_usage(plt, timestamps, memory_rss, memory_vms, figfile)
    plot_other_metrics(plt, timestamps, num_threads, num_fds, figfile)


def plot_cpu_usage(plt, timestamps, cpu_percent, figfile):
    timestamps = [t - timestamps[0] for t in timestamps]
    plt.figure(figsize=(15, 15))
    plt.plot(timestamps, cpu_percent)
    plt.title('CPU Usage')
    plt.xlabel('time (s)')
    plt.ylabel('%CPU')
    plt.savefig('cpu_usage_{}'.format(figfile), dpi=120)
    plt.clf()


def plot_cpu_times(plt, timestamps, system_times, user_times, figfile):
    timestamps = [t - timestamps[0] for t in timestamps]
    plt.figure(figsize=(15, 15))
    ax = plt.subplot(2, 1, 1)
    plt.plot(timestamps, de_cumulative_list(system_times))
    plt.title('System Time')
    plt.xlabel('time (s)')
    plt.ylabel('time (s)')
    plt.subplot(2, 1, 2, sharex=ax)
    plt.plot(timestamps, de_cumulative_list(user_times))
    plt.title('User Time')
    plt.xlabel('time (s)')
    plt.ylabel('time (s)')
    plt.suptitle('CPU Times')
    plt.savefig('cpu_times_{}'.format(figfile), dpi=120)
    plt.clf()


def plot_mem_usage(plt, timestamps, memory_rss, memory_vms, figfile):
    timestamps = [t - timestamps[0] for t in timestamps]
    memory_rss = [m/1e6 for m in memory_rss]
    memory_vms = [m/1e6 for m in memory_vms]
    plt.figure(figsize=(15, 15))
    ax = plt.subplot(2, 1, 1)
    plt.plot(timestamps, memory_rss)
    plt.title('Memory RSS/ RES')
    plt.xlabel('time (s)')
    plt.ylabel('Memory Size (MB)')
    plt.subplot(2, 1, 2, sharex=ax)
    plt.plot(timestamps, memory_vms)
    plt.title('Memory VMS/ VIRT')
    plt.xlabel('time (s)')
    plt.ylabel('Memory Size (MB)')
    plt.suptitle('Memory Usage')
    plt.savefig('memory_usage_{}'.format(figfile), dpi=120)
    plt.clf()


def plot_other_metrics(plt, timestamps, num_threads, num_fds, figfile):
    timestamps = [t - timestamps[0] for t in timestamps]
    plt.figure(figsize=(15, 15))
    ax = plt.subplot(2, 1, 1)
    plt.plot(timestamps, num_threads)
    plt.title('Number of threads')
    plt.xlabel('time (s)')
    plt.ylabel('#threads')
    plt.subplot(2, 1, 2, sharex=ax)
    plt.plot(timestamps, num_fds)
    plt.title('Number of file descriptors')
    plt.xlabel('time (s)')
    plt.ylabel('#fd')
    plt.suptitle('Other metrics')
    plt.savefig('other_metrics_{}'.format(figfile), dpi=120)
    plt.clf()

