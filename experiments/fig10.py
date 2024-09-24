from xlutil import *
import pool_pvcc
import argparse

def exp(vms: int, tslice_us: int, rates: list, conns_per_thread: int, dataroot: str):
    pool_pvcc.credit(tslice_us=tslice_us, ratelimit_us=tslice_us, cpus=[1])

    for i in range(1, vms+1):
        xl_create(f"seastar{i}")
        time.sleep(1)

    for i in range(1, vms+1):
        host = f"root@192.168.70.{i}"
        wait_domain(host)
        vfiobind(host)
        ssh_popen(host, f"taskset -c 0 /root/seastar/build/release/apps/memcached/memcached --network-stack native --dpdk-pmd --dhcp 0 --host-ipv4-addr 10.0.0.{i} --netmask-ipv4-addr 255.255.255.0 --smp 1 --port 12345", stdout=subprocess.DEVNULL)

    time.sleep(5)

    for i in range(1, vms+1):
        while client_popen(f"ping -c 1 -W 1 10.0.0.{i}").wait(): time.sleep(1)
        assert(client_popen(f"taskset -c 0 ~/mutilate/mutilate -s 10.0.0.{i}:12345 -T 1 --loadonly").wait() == 0)
        xl_cpupool_migrate(f"seastar{i}", "credit")

    time.sleep(1)

    logdir = f"{dataroot}/{vms}vms/{tslice_us}us"
    subprocess.run(f"mkdir -p {logdir}", shell=True, check=True)

    for rate in rates:
        assert(client_popen(f"~/mutilate/mutilate -s 10.0.0.1:12345 -T 24 -c {conns_per_thread} -q {rate} -u 0 -i exponential:1 -t 20 --noload > {logdir}/{rate}qps").wait() == 0)

    subprocess.run("./reset.sh", shell=True)


if __name__ == "__main__":
    all_rates = {
        1: {
            50: [1000, 128000, 256000] + [i for i in range(280000, 400000 + 1, 20000)],
            100: [1000, 128000, 256000] + [i for i in range(280000, 400000 + 1, 20000)],
            500: [1000, 128000, 256000] + [i for i in range(280000, 400000 + 1, 20000)],
            1000: [1000, 128000, 256000] + [i for i in range(280000, 400000 + 1, 20000)],
        },
        2: {
            50: [1000, 16000, 64000] + [i for i in range(100000, 150000 + 1, 10000)],
            100: [1000, 16000, 64000] + [i for i in range(100000, 200000 + 1, 10000)],
            500: [1000, 16000, 64000] + [i for i in range(100000, 200000 + 1, 10000)],
            1000: [1000, 16000, 64000] + [i for i in range(100000, 200000 + 1, 10000)],
        },
        4: {
            50: [1000, 16000, 32000] + [i for i in range(40000, 60000 + 1, 5000)],
            100: [1000, 16000, 32000] + [i for i in range(40000, 70000 + 1, 5000)],
            500: [1000, 16000, 32000] + [i for i in range(40000, 100000 + 1, 5000)],
            1000: [1000, 16000, 32000] + [i for i in range(40000, 100000 + 1, 5000)],
        },
        8: {
            50: [i for i in range(2000, 20000 + 1, 2000)],
            100: [i for i in range(2000, 30000 + 1, 2000)],
            500: [i for i in range(2000, 50000 + 1, 2000)],
            1000: [i for i in range(2000, 50000 + 1, 2000)],
        },
        16: {
            50: [i for i in range(2000, 5000 + 1, 500)],
            100: [i for i in range(2000, 10000 + 1, 1000)],
            500: [i for i in range(2000, 24000 + 1, 2000)],
            1000: [i for i in range(2000, 24000 + 1, 2000)],
        },
        32: {
            50: [i for i in range(1000, 5000 + 1, 500)],
            100: [i for i in range(1000, 5000 + 1, 500)],
            500: [1000] + [i for i in range(2000, 12000 + 1, 2000)],
            1000: [1000] + [i for i in range(2000, 12000 + 1, 2000)],
        },
    }
    all_conns_per_thread = {
        1: 5,
        2: 5,
        4: 5,
        8: 5,
        16: 5,
        32: 3,
    }

    parser = argparse.ArgumentParser()
    parser.add_argument("--vms", type=int, nargs="*")
    parser.add_argument("--tslices", type=int, nargs="*")
    parser.add_argument("--rates", type=int, nargs="*")
    parser.add_argument("--trial", type=int)
    args = parser.parse_args()

    dataroot = "data/fig10"
    if args.trial is not None:
        idx = str(args.trial).zfill(2)
        dataroot = f"data/fig10.{idx}"

    vms = [1,2,4,8,16,32]
    if args.vms:
        vms = args.vms

    tslices = [50,100,500,1000]
    if args.tslices:
        tslices = args.tslices

    for vmnum in vms:
        for tslice in tslices:
            rates = all_rates[vmnum][tslice]
            if args.rates:
                rates = args.rates
            
            conns_per_thread = all_conns_per_thread[vmnum]
            exp(vmnum, tslice, rates, conns_per_thread, dataroot)
