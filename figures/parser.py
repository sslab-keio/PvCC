from typing import *
import re

class Iip:  # latency ... [ns]
    bps_rx: int
    pps_rx: int
    bps_tx: int
    pps_tx: int
    p50: int
    p90: int
    p99: int
    p999: int

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    @classmethod
    def parse(cls, filepath: str) -> Self:
        with open(filepath, "r") as f:
            lines = f.read().splitlines()

            i = 0
            while "throughput rx" not in lines[i]:
                i += 1

            cols = lines[i].split()

            return cls(**{
                "bps_rx": int(cols[2]),
                "pps_rx": int(cols[4]),
                "bps_tx": int(cols[7]),
                "pps_tx": int(cols[9]),
                "p50": int(cols[13]),
                "p90": int(cols[16]),
                "p99": int(cols[19]),
                "p999": int(cols[22]),
            })


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

class Wrk2: # Latency ... [us]
    duration: int
    thds: int
    conns: int
    p50: float
    p90: float
    p99: float
    p999: float
    rps: float
    pcts: list[float]
    pcts_rev: list[float]
    lats: list[float]
    uc_p50: float
    uc_p90: float
    uc_p99: float
    uc_p999: float
    uc_pcts: list[float]
    uc_pcts_rev: list[float]
    uc_lats: list[float]

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
            thds, _, _, conns, _ = lines[i].split()
            
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
            p50 = get_latency_us(lines[i].split()[1])
            while "90.000%" not in lines[i]:
                i += 1
            p90 = get_latency_us(lines[i].split()[1])
            while "99.000%" not in lines[i]:
                i += 1
            p99 = get_latency_us(lines[i].split()[1])
            while "99.900%" not in lines[i]:
                i += 1
            p999 = get_latency_us(lines[i].split()[1])

            while "Value   Percentile   TotalCount 1/(1-Percentile)" not in lines[i]:
                i += 1
            i += 2

            pcts = []
            pcts_rev = []
            lats = []
            while "#[Mean" not in lines[i]:
                # latency ... [ms]
                latency, percentile, _, _ = map(float, lines[i].split())
                pcts.append(percentile)
                pcts_rev.append(1 - percentile)
                lats.append(latency * 1000)
                i += 1
            assert(len(lats) == len(pcts))
            assert(len(lats) == len(pcts_rev))

            while "HdrHistogram - Uncorrected Latency" not in lines[i]:
                i += 1

            while "50.000%" not in lines[i]:
                i += 1
            uc_p50 = get_latency_us(lines[i].split()[1])
            while "90.000%" not in lines[i]:
                i += 1
            uc_p90 = get_latency_us(lines[i].split()[1])
            while "99.000%" not in lines[i]:
                i += 1
            uc_p99 = get_latency_us(lines[i].split()[1])
            while "99.900%" not in lines[i]:
                i += 1
            uc_p999 = get_latency_us(lines[i].split()[1])

            while "Value   Percentile   TotalCount 1/(1-Percentile)" not in lines[i]:
                i += 1
            i += 2

            uc_pcts = []
            uc_pcts_rev = []
            uc_lats = []
            while "#[Mean" not in lines[i]:
                # latency ... [ms]
                latency, percentile, _, _ = map(float, lines[i].split())
                uc_pcts.append(percentile)
                uc_pcts_rev.append(1 - percentile)
                uc_lats.append(latency * 1000)
                i += 1
            assert(len(uc_lats) == len(uc_pcts))
            assert(len(uc_lats) == len(uc_pcts_rev))

            while "Requests/sec:" not in lines[i]:
                i += 1
            rps = float(lines[i].split()[1])
            
            return cls(**{
                "duration": duration,
                "thds": thds,
                "conns": conns,
                "p50": p50,
                "p90": p90,
                "p99": p99,
                "p999": p999,
                "rps": rps,
                "pcts": pcts,
                "pcts_rev": pcts_rev,
                "lats": lats,
                "uc_p50": uc_p50,
                "uc_p90": uc_p90,
                "uc_p99": uc_p99,
                "uc_p999": uc_p999,
                "uc_pcts": uc_pcts,
                "uc_pcts_rev": uc_pcts_rev,
                "uc_lats": uc_lats,
            })
            
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
