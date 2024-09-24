import pool_pvcc
from xlutil import *
import time
import argparse

def memcached(preset_rates, dataroot):
    pool_pvcc.credit(tslice_us=100, ratelimit_us=100, cpus=[0])

    for i in range(1, 4+1):
        xl_create(f"seastar{i}")
    for i in range(1, 4+1):
        host = f"192.168.70.{i}"
        wait_domain(host)
        vfiobind(host)
        ssh_popen(host, f"taskset -c 0 /root/seastar/build/release/apps/memcached/memcached --network-stack native --dpdk-pmd --dhcp 0 --host-ipv4-addr 10.0.0.{i} --netmask-ipv4-addr 255.255.255.0 --smp 1 --port 12345")

    time.sleep(5)

    for i in range(1, 4+1):
        while client_popen(f"ping -c 3 -W 1 10.0.0.{i}").wait(): time.sleep(1)
        assert(client_popen(f"taskset -c 0 ~/mutilate/mutilate -s 10.0.0.{i}:12345 -T 1 --loadonly").wait() == 0)
        xl_cpupool_migrate(f"seastar{i}", "credit")

    time.sleep(1)

    logdir = f"{dataroot}/memcached/pvcc"
    subprocess.run(f"mkdir -p {logdir}", shell=True, check=True)

    rates = [i for i in range(5000, 100000 + 1, 5000)]
    if preset_rates:
        rates = preset_rates

    for qps in rates:
        assert(client_popen(f"taskset -c 0-3 ~/mutilate/mutilate -s 10.0.0.1:12345 -T 4 -c 32 -q {qps} -u 0 -i exponential:1 -t 10 --noload > {logdir}/{qps}qps").wait() == 0)

    subprocess.run("./reset.sh", shell=True)


def nginx(preset_rates, dataroot):
    pool_pvcc.credit(tslice_us=100, ratelimit_us=100, cpus=[0])

    for i in range(1, 4+1):
        xl_create(f"fstack{i}")

    for i in range(1, 4+1):
        host = f"192.168.70.{50+i}"
        wait_domain(host)
        # vfiobind(host)
        ssh_popen(host, f"/usr/local/nginx_fstack/sbin/nginx")
        xl_cpupool_migrate(f"fstack{i}", "credit")

    time.sleep(5)

    logdir = f"{dataroot}/nginx/pvcc"
    subprocess.run(f"mkdir -p {logdir}", shell=True, check=True)

    rates = list(range(2000, 50000 + 1, 2000))
    if preset_rates:
        rates = preset_rates

    for rate in rates:
        ssh_run(client, f"~/wrk2/wrk http://10.0.0.11 --duration 10 --threads 24 --connections 24 --rate {rate} --u_latency | tee {logdir}/{rate}rps", check=True)

    subprocess.run("./reset.sh", shell=True)


def redis(preset_rates, dataroot):
    pool_pvcc.credit(tslice_us=100, ratelimit_us=100, cpus=[0])

    for i in range(1, 4+1):
        xl_create(f"fstack{i}")

    for i in range(1, 4+1):
        host = f"192.168.70.{50+i}"
        wait_domain(host)
        # vfiobind(host)
        ssh_popen(host, f"/usr/local/bin/redis-server --conf /usr/local/nginx_fstack/conf/f-stack.conf --proc-type=primary --proc-id=0 /root/fstack/app/redis-6.2.6/redis.conf")
        xl_cpupool_migrate(f"fstack{i}", "credit")

    time.sleep(5)

    logdir = f"{dataroot}/redis/pvcc"
    subprocess.run(f"mkdir -p {logdir}", shell=True, check=True)

    rates = list(range(100, 3000+1, 100))
    if preset_rates:
        rates = preset_rates

    for rate in rates:
        ssh_run(client, f"~/memtier_benchmark/memtier_benchmark --host 10.0.0.11 --port 6379 --test-time 10 --ratio 0:1 --threads 24 --clients 1 --rate {rate} | tee {logdir}/{rate}rps", check=True)

    subprocess.run("./reset.sh", shell=True)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--workloads", type=str, nargs="*")
    parser.add_argument("--rates", type=int, nargs="*")
    parser.add_argument("--trial", type=int)
    args = parser.parse_args()

    dataroot = "data/fig06"
    if args.trial is not None:
        idx = str(args.trial).zfill(2)
        dataroot = f"data/fig06.{idx}"

    workloads = ["memcached", "nginx", "redis"]
    if args.workloads:
        workloads = args.workloads

    if "memcached" in workloads:
        memcached(args.rates, dataroot)
    if "nginx" in workloads:
        nginx(args.rates, dataroot)
    if "redis" in workloads:
        redis(args.rates, dataroot)

