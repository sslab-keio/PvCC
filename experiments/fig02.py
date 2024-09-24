import pool_vanilla
from xlutil import *
import argparse

domain = "seastar1"
host = "root@192.168.70.1"
conns_per_thread = 7

netstack_params = {
	"dpdk": "--network-stack native --dpdk-pmd",
	"linux": "--network-stack posix",
}

def fig02_exp(stack: str, threads: list, dataroot: str):
    pool_vanilla.credit(tslice_ms=30, ratelimit_us=1000, cpus=[0])

    xl_create(domain)
    xl_cpupool_migrate(domain, "credit")
    xl_vcpu_pin(domain, "0", "0")
    wait_domain(host=host)

    if stack == "dpdk":
        vfiobind(host=host)
    elif stack == "linux":
        ssh_run(host, "ip a a dev ens6 10.0.0.1/24", check=True)
        ssh_run(host, "ip l s dev ens6 up", check=True)
    else: assert(False)

    ssh_popen(host, f"taskset -c 0 /root/seastar/build/release/apps/memcached/memcached --dhcp 0 --host-ipv4-addr 10.0.0.1 --netmask-ipv4-addr 255.255.255.0 --smp 1 --port 12345 {netstack_params[stack]}", stdout=subprocess.DEVNULL)

    while client_popen(f"ping -c 3 -W 1 10.0.0.1").wait(): time.sleep(1)
    assert(client_popen(f"taskset -c 0 ~/mutilate/mutilate -s 10.0.0.1:12345 -T 1 --loadonly").wait() == 0)

    datadir = f"{dataroot}/{stack}"
    subprocess.run(f"mkdir -p {datadir}", shell=True)

    for thds in threads:
        assert(client_popen(f"~/mutilate/mutilate -s 10.0.0.1:12345 -T {thds} -c {conns_per_thread} -q 0 -u 0 -i exponential:1 -t 10 --noload > {datadir}/{thds * conns_per_thread}conns").wait() == 0)

    subprocess.run("./reset.sh")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--threads", type=int, nargs="*")
    parser.add_argument("--trial", type=int)
    args = parser.parse_args()

    threads = list(range(1, 24+1))
    if args.threads:
        threads = args.threads

    dataroot = "data/fig02"
    if args.trial is not None:
        idx = str(args.trial).zfill(2)
        dataroot = f"data/fig02.{idx}"

    fig02_exp("dpdk", threads, dataroot)
    fig02_exp("linux", threads, dataroot)

