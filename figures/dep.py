# parsers
from typing import *
import re
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import pandas as pd
import numpy as np

class Mutilate:
    read_mean: float
    read_min: float
    read_p99: float
    update_mean: float
    update_min: float
    update_p99: float
    qps: float
    queries: int
    duration: float
    misses: int
    skipped_txs: int
    rx_bytes: int
    tx_bytes: int

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def parse(cls, filepath: str) -> Self:
        with open(filepath, "r") as f:
            lines = f.read().splitlines()

            line_read = lines[1].split()
            line_update = lines[2].split()
            line_qps = lines[5].split()
            line_misses = lines[7].split()
            line_skipped_txs = lines[8].split()
            line_rx = lines[10].split()
            line_tx = lines[11].split()

            return cls(**{
                "read_mean": float(line_read[1]),
                "read_min": float(line_read[3]),
                "read_p99": float(line_read[8]),
                "update_mean": float(line_update[1]),
                "update_min": float(line_update[3]),
                "update_p99": float(line_update[8]),
                "qps": float(line_qps[3]),
                "queries": int(line_qps[4][1:]),
                "duration": float(line_qps[6][:-2]),
                "misses": int(line_misses[2]),
                "skipped_txs": int(line_skipped_txs[3]),
                "rx_bytes": int(line_rx[1]),
                "tx_bytes": int(line_tx[1]),
            })
    
    def dump(self):
        print(vars(self))

class SeastarMemcachedSamples:
    samples: list[tuple[float, float]]  # List of (Timestamp, RTT [us])

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def parse(cls, filepath: str) -> Self:
        with open(filepath, "r") as f:
            samples = []
            for line in f.read().splitlines():
                samples.append(tuple(map(float, line.split())))

            return cls(**{
                "samples": samples,
            })
    
    def dump(self):
        print(vars(self))

class Sysbench:
    threads: int
    limit: int
    throughputs: list[float]

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def parse(cls, filepath: str) -> Self:
        with open(filepath, "r") as f:
            lines = f.read().splitlines()

            i = 0

            while "Number of threads" not in lines[i]:
                i += 1
            threads = int(lines[i].split()[3])

            while "Prime numbers limit" not in lines[i]:
                i += 1
            prime_limit = int(lines[i].split()[3])

            while "thds" not in lines[i]:
                i += 1
            
            throughputs = []
            while "thds" in lines[i]:
                throughputs.append(float(lines[i].split()[6]))
                i += 1
            
            return cls(**{
                "threads": threads,
                "prime_limit": prime_limit,
                "throughputs": throughputs,
            })

class SysbenchSimple:
    overall_eps: float
    events: int

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def parse(cls, filepath: str) -> Self:
        with open(filepath, "r") as f:
            lines = f.read().splitlines()

            i = 0

            while "events per second" not in lines[i]:
                i += 1
            overall_eps = float(lines[i].split()[3])

            while "total number of events" not in lines[i]:
                i += 1
            events = int(lines[i].split()[4])

            return cls(**{
                "overall_eps": overall_eps,
                "events": events,
            })

# summary = SysbenchSimple.parse("/home/jovyan/log/pvcc-memcached/mutilate/1ls_2nls/100us_20000qps_to1server_sysbench0")
# print(summary.overall_eps)

class Wrk2:
    duration: int
    threads: int
    connections: int
    p50: float
    p90: float
    p99: float
    p999: float
    p50_corrected: float
    p90_corrected: float
    p99_corrected: float
    p999_corrected: float
    throughput: float
    spectrum_percent: list[float]
    spectrum_percent_reverse: list[float]
    spectrum_latency: list[float]

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def parse(cls, filepath: str) -> Self:
        # print(filepath)
        with open(filepath, "r") as f:
            lines = f.read().splitlines()

            i = 0

            while "s test @ " not in lines[i]:
                i += 1
            duration = int(lines[i].split()[1][:-1])

            while "threads and" not in lines[i]:
                i += 1
            threads, _, _, connections, _ = lines[i].split()
            
            def get_latency_us(latency_str) -> float:
                if latency_str[-2:] == "us": return float(latency_str[:-2])
                elif latency_str[-2:] == "ms": return float(latency_str[:-2]) * 1000
                elif latency_str[-1:] == "s": return float(latency_str[:-1]) * 1000000
                else: assert(False)

            while "Latency Distribution (HdrHistogram - Recorded Latency)" not in lines[i]:
                i += 1
            i += 1

            while "50.000%" not in lines[i]:
                i += 1
            p50_corrected = get_latency_us(lines[i].split()[1])

            while "90.000%" not in lines[i]:
                i += 1
            p90_corrected = get_latency_us(lines[i].split()[1])
            
            while "99.000%" not in lines[i]:
                i += 1
            p99_corrected = get_latency_us(lines[i].split()[1])
            
            while "99.900%" not in lines[i]:
                i += 1
            p999_corrected = get_latency_us(lines[i].split()[1])

            while "HdrHistogram - Uncorrected Latency" not in lines[i]:
                i += 1

            while "50.000%" not in lines[i]:
                i += 1
            # latency_str = lines[i].split()[1]
            # assert(latency_str[-2:] == "us")
            # p50 = float(latency_str[:-2])
            p50 = get_latency_us(lines[i].split()[1])

            while "90.000%" not in lines[i]:
                i += 1
            # latency_str = lines[i].split()[1]
            # assert(latency_str[-2:] == "us")
            # p90 = float(latency_str[:-2])
            p90 = get_latency_us(lines[i].split()[1])
            
            while "99.000%" not in lines[i]:
                i += 1
            # latency_str = lines[i].split()[1]
            # assert(latency_str[-2:] == "us")
            # p99 = float(latency_str[:-2])
            p99 = get_latency_us(lines[i].split()[1])
            
            while "99.900%" not in lines[i]:
                i += 1
            # latency_str = lines[i].split()[1]
            # assert(latency_str[-2:] == "us")
            # p999 = float(latency_str[:-2])
            p999 = get_latency_us(lines[i].split()[1])

            while "Value   Percentile   TotalCount 1/(1-Percentile)" not in lines[i]:
                i += 1
            i += 2

            spectrum_percent = []
            spectrum_percent_reverse = []
            spectrum_latency = []
            while "#[Mean" not in lines[i]:
                # latency ... [ms]
                latency, percentile, _, _ = map(float, lines[i].split())
                spectrum_percent.append(percentile)
                spectrum_percent_reverse.append(1 - percentile)
                spectrum_latency.append(latency * 1000)
                i += 1
            
            assert(len(spectrum_latency) == len(spectrum_percent))
            assert(len(spectrum_latency) == len(spectrum_percent_reverse))

            while "Requests/sec:" not in lines[i]:
                i += 1
            throughput = float(lines[i].split()[1])
            
            return cls(**{
                "duration": duration,
                "threads": threads,
                "connections": connections,
                "p50": p50,
                "p90": p90,
                "p99": p99,
                "p999": p999,
                "p50_corrected": p50_corrected,
                "p90_corrected": p90_corrected,
                "p99_corrected": p99_corrected,
                "p999_corrected": p999_corrected,
                "throughput": throughput,
                "spectrum_percent": spectrum_percent,
                "spectrum_percent_reverse": spectrum_percent_reverse,
                "spectrum_latency": spectrum_latency,
            })
            
# summary = Wrk2.parse("/home/jovyan/log/berlin/log/fstack-nginx/wrk2/50000")
# print(summary.spectrum_percent)
# print(summary.spectrum_percent_reverse)
# print(summary.spectrum_latency)
# summary = Wrk2.parse("/home/jovyan/log/berlin/log/fstack-nginx/wrk2/4vm/credit2_0_10000rps")
# print(summary.spectrum_percent)
# print(summary.spectrum_percent_reverse)
# print(summary.spectrum_latency)
# print(summary.p50)
# print(summary.p90)
# print(summary.p99)
# print(summary.p999)
# summary = Wrk2.parse("/home/jovyan/log/berlin/log/fstack-nginx/wrk2/cap-4vm/credit_1000_2000rps")
# print(summary.__dict__)
# summary = Wrk2.parse("/home/jovyan/log/berlin/log/fstack-nginx/wrk2/cap-4vm/credit_100_40000rps")
# print(summary.__dict__)
class RedisBenchmarkCsvRecord:
    test: str
    rps: float
    avg_latency_ms: float
    min_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
class RedisBenchmarkCsv:

    GET: RedisBenchmarkCsvRecord
    SET: RedisBenchmarkCsvRecord

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def parse(cls, filepath: str) -> Self:
        with open(filepath, "r") as f:
            lines = f.read().splitlines()[1:]
            records = {}
            for line in lines:
                columns = list(filter(lambda x: len(x) > 0, re.split('\"|,', line)))
                records[columns[0]] = RedisBenchmarkCsvRecord(**{
                    "test": columns[0],
                    "rps": float(columns[1]),
                    "avg_latency_ms": float(columns[2]),
                    "min_latency_ms": float(columns[3]),
                    "p50_latency_ms": float(columns[4]),
                    "p95_latency_ms": float(columns[5]),
                    "p99_latency_ms": float(columns[6]),
                    "max_latency_ms": float(columns[7]),
                })

            return cls(**records)

# ins = RedisBenchmarkCsv.parse("/home/jovyan/log/berlin/log/fstack-redis/redis-benchmark/1vm_1Mreqs_1thread_50conn_32pipeline")
# print(ins.SET.__dict__)
# print(ins.GET.__dict__)
# print(ins.GET.p99_latency_ms)

class Memtier:
    get_rps: float
    get_p50: float
    get_p99: float

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def parse(cls, filepath: str) -> Self:
        with open(filepath, "r") as f:
            lines = f.read().splitlines()[1:]
            
            i = 0

            while "Gets " not in lines[i]: i += 1
            _, rps, _, _, _, p50, p99, _, _ = lines[i].split()

            return cls(**{
                "get_rps": float(rps),
                "get_p50": float(p50),
                "get_p99": float(p99),
            })

# ins = Memtier.parse(f"/home/jovyan/log/berlin/log/fstack-redis/memtier/schedulers/credit_100_4000rps")
# print(ins.__dict__)

# styles
rcParams_halfwidth = plt.rcParamsDefault | {
    "font.size": 10,
    # "figure.figsize": [4.8, 3.6],
    "figure.figsize": [4.8, 3.0],
    "legend.fontsize": 10,
    "lines.markersize": 5,
    # "axes.titley": -0.36,
    "axes.titlesize": 10,
    "figure.titlesize": 10,
}
params_legend_upper_center = {
    "loc": "upper center",
    "bbox_to_anchor": (0.5, 1.13),
    # "ncol": 3,
    "frameon": False,
    "handlelength": 0,
    "handletextpad": 0.7,
    "fontsize": 10,
    "columnspacing": 1.3,
}

def get_data_of_sb(target):
    ret = {}
    report_dict = {}
    report_cols = ['throughput', 'latency']
    with open(target, 'r') as f:
        for line in f:
            if (get_element_from_line(line, 0) == 'events' 
                and get_element_from_line(line, 1) == 'per'
                and get_element_from_line(line, 2) == 'second:'):
                ret['eps'] = float(get_element_from_line(line, 3))
            elif (get_element_from_line(line, 0) == 'Latency'):
                for i in range(5):
                    line = f.readline()
                    latency = get_element_from_line(line, 1)
                    if latency == 'percentile:':
                        latency = get_element_from_line(line, 2)
                        
                    ret[get_element_from_line(line, 0)] = float(latency)
            elif (get_element_from_line(line, 0) == '['):
                index = int(get_element_from_line(line, 1)[:-1])
                throughput = float(get_element_from_line(line, 6))
                latency = float(get_element_from_line(line, 9))
                report_dict[index] = [throughput, latency]
                
    ret['report'] = pd.DataFrame.from_dict(report_dict, orient='index', columns=report_cols)
    return ret

def get_element_from_line(line, index):
    if line:
        line = line.strip().split()
        if index < len(line):
            return line[index]
    return None
