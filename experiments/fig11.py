import pool_pvcc
from xlutil import *
import socket
import os
import argparse

LSVM_NUM = 4

def scaling_api_send(phase):
    ip_addr = "192.168.70.250"
    port = 7777
    weights = [
        [128, 64, 32, 16],
        [128, 64, 32, 32],
        [128, 128, 128, 128],
        [128, 64, 32, 32],
        [128, 64, 32, 16],
    ]

    for idx in range(LSVM_NUM):
        msg = f"SET {idx + 1} {weights[phase][idx]}"
        print(f'send {msg} to {ip_addr}:{port}')
        server_addr = (ip_addr, port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(server_addr)
        sock.send(msg.encode('utf-8'))
        msg = sock.recv(1024)
        end_msg = 'END'
        sock.send(end_msg.encode('utf-8'))

def naive(dataroot: str):
    logdir = f"{dataroot}/naive"
    remotelogdir = "/tmp/fig11-naive"
    subprocess.run(f"mkdir -p {logdir}", shell=True)
    assert(client_popen(f"mkdir {remotelogdir}").wait() == 0)

    pool_pvcc.credit(tslice_us=1000, ratelimit_us=1000, cpus=[1,2,3,4,5,6], name="be")

    xl_create(f"seastar1")
    time.sleep(1)
    xl_create(f"seastar2")
    time.sleep(1)
    xl_create(f"seastar3")
    time.sleep(1)
    xl_create(f"seastar4")
    time.sleep(1)
    xl_create(f"loadvm1")

    wait_domain("root@192.168.70.1")
    vfiobind("root@192.168.70.1")
    wait_domain("root@192.168.70.2")
    vfiobind("root@192.168.70.2")
    wait_domain("root@192.168.70.3")
    vfiobind("root@192.168.70.3")
    wait_domain("root@192.168.70.4")
    vfiobind("root@192.168.70.4")
    wait_domain("root@192.168.70.101")

    ssh_popen(f"root@192.168.70.1", f"nohup taskset -c 0 /root/seastar/build/release/apps/memcached/memcached --network-stack native --dpdk-pmd --dhcp 0 --host-ipv4-addr 10.0.0.1 --netmask-ipv4-addr 255.255.255.0 --smp 1 --port 12345 &", stdout=subprocess.DEVNULL)
    ssh_popen(f"root@192.168.70.2", f"nohup taskset -c 0 /root/seastar/build/release/apps/memcached/memcached --network-stack native --dpdk-pmd --dhcp 0 --host-ipv4-addr 10.0.0.2 --netmask-ipv4-addr 255.255.255.0 --smp 1 --port 12345 &", stdout=subprocess.DEVNULL)
    ssh_popen("root@192.168.70.3", f"nohup taskset -c 0 /root/seastar/build/release/apps/memcached/memcached --network-stack native --dpdk-pmd --dhcp 0 --host-ipv4-addr 10.0.0.3 --netmask-ipv4-addr 255.255.255.0 --smp 1 --port 12345 &", stdout=subprocess.DEVNULL)
    ssh_popen("root@192.168.70.4", f"nohup taskset -c 0 /root/seastar/build/release/apps/memcached/memcached --network-stack native --dpdk-pmd --dhcp 0 --host-ipv4-addr 10.0.0.4 --netmask-ipv4-addr 255.255.255.0 --smp 1 --port 12345 &", stdout=subprocess.DEVNULL)

    while client_popen("ping -c 1 -W 1 10.0.0.1").wait(): time.sleep(1)
    assert(client_popen(f"taskset -c 0 ~/mutilate/mutilate -s 10.0.0.1:12345 -T 1 --loadonly").wait() == 0)
    while client_popen("ping -c 1 -W 1 10.0.0.2").wait(): time.sleep(1)
    assert(client_popen(f"taskset -c 0 ~/mutilate/mutilate -s 10.0.0.2:12345 -T 1 --loadonly").wait() == 0)
    while client_popen("ping -c 1 -W 1 10.0.0.3").wait(): time.sleep(1)
    assert(client_popen(f"taskset -c 0 ~/mutilate/mutilate -s 10.0.0.3:12345 -T 1 --loadonly").wait() == 0)
    while client_popen("ping -c 1 -W 1 10.0.0.4").wait(): time.sleep(1)
    assert(client_popen(f"taskset -c 0 ~/mutilate/mutilate -s 10.0.0.4:12345 -T 1 --loadonly").wait() == 0)

    p_sysbench = ssh_popen("root@192.168.70.101", f"sysbench cpu --cpu-max-prime=10000 --threads=24 --time=80 --report-interval=1 run > {logdir}/sysbench")

    time.sleep(15)

    xl_cpupool_migrate("loadvm1", "be")
    xl_cpupool_migrate("seastar1", "be")
    xl_cpupool_migrate("seastar2", "be")
    xl_cpupool_migrate("seastar3", "be")
    xl_cpupool_migrate("seastar4", "be")

    time.sleep(15)

    client_popen(f"taskset -c 0-1 ~/mutilate/mutilate -s 10.0.0.1:12345 -T 2 -c 16 -q 1000 -u 0 -i exponential:1 -t 50 --noload --save={remotelogdir}/p0-vm1-samples > {logdir}/p0-vm1")
    client_popen(f"taskset -c 2-3 ~/mutilate/mutilate -s 10.0.0.2:12345 -T 2 -c 16 -q 1000 -u 0 -i exponential:1 -t 50 --noload --save={remotelogdir}/p0-vm2-samples > {logdir}/p0-vm2")
    client_popen(f"taskset -c 4-5 ~/mutilate/mutilate -s 10.0.0.3:12345 -T 2 -c 16 -q 1000 -u 0 -i exponential:1 -t 50 --noload --save={remotelogdir}/p0-vm3-samples > {logdir}/p0-vm3")
    client_popen(f"taskset -c 6-7 ~/mutilate/mutilate -s 10.0.0.4:12345 -T 2 -c 16 -q 1000 -u 0 -i exponential:1 -t 50 --noload --save={remotelogdir}/p0-vm4-samples > {logdir}/p0-vm4")
    time.sleep(10)
    client_popen(f"taskset -c  8-9  ~/mutilate/mutilate -s 10.0.0.1:12345 -T 2 -c 16 -q 9000 -u 0 -i exponential:1 -t 30 --noload --save={remotelogdir}/p1-vm1-samples > {logdir}/p1-vm1")
    client_popen(f"taskset -c 10-11 ~/mutilate/mutilate -s 10.0.0.2:12345 -T 2 -c 16 -q 9000 -u 0 -i exponential:1 -t 30 --noload --save={remotelogdir}/p1-vm2-samples > {logdir}/p1-vm2")
    client_popen(f"taskset -c 12-13 ~/mutilate/mutilate -s 10.0.0.3:12345 -T 2 -c 16 -q 9000 -u 0 -i exponential:1 -t 30 --noload --save={remotelogdir}/p1-vm3-samples > {logdir}/p1-vm3")
    client_popen(f"taskset -c 14-15 ~/mutilate/mutilate -s 10.0.0.4:12345 -T 2 -c 16 -q 9000 -u 0 -i exponential:1 -t 30 --noload --save={remotelogdir}/p1-vm4-samples > {logdir}/p1-vm4")
    time.sleep(10)
    client_popen(f"taskset -c 16-17 ~/mutilate/mutilate -s 10.0.0.1:12345 -T 2 -c 16 -q 90000 -u 0 -i exponential:1 -t 10 --noload --save={remotelogdir}/p2-vm1-samples > {logdir}/p2-vm1")
    client_popen(f"taskset -c 18-19 ~/mutilate/mutilate -s 10.0.0.2:12345 -T 2 -c 16 -q 90000 -u 0 -i exponential:1 -t 10 --noload --save={remotelogdir}/p2-vm2-samples > {logdir}/p2-vm2")
    client_popen(f"taskset -c 20-21 ~/mutilate/mutilate -s 10.0.0.3:12345 -T 2 -c 16 -q 90000 -u 0 -i exponential:1 -t 10 --noload --save={remotelogdir}/p2-vm3-samples > {logdir}/p2-vm3")
    client_popen(f"taskset -c 22-23 ~/mutilate/mutilate -s 10.0.0.4:12345 -T 2 -c 16 -q 90000 -u 0 -i exponential:1 -t 10 --noload --save={remotelogdir}/p2-vm4-samples > {logdir}/p2-vm4")

    p_sysbench.wait()

    client_fetch(remotelogdir, f"{logdir}/samples")
    assert(client_popen(f"rm -rf {remotelogdir}").wait() == 0)

    subprocess.run("./reset.sh", shell=True)

def pin(dataroot: str):
    logdir = f"{dataroot}/pin"
    remotelogdir = "/tmp/fig11-pin"
    subprocess.run(f"mkdir -p {logdir}", shell=True)
    assert(client_popen(f"mkdir {remotelogdir}").wait() == 0)

    pool_pvcc.credit(tslice_us=1000, ratelimit_us=1000, cpus=[1,2,3,4], name="ls")
    pool_pvcc.credit(tslice_us=30000, ratelimit_us=1000, cpus=[5,6], name="be")

    xl_create(f"seastar1")
    time.sleep(1)
    xl_create(f"seastar2")
    time.sleep(1)
    xl_create(f"seastar3")
    time.sleep(1)
    xl_create(f"seastar4")
    time.sleep(1)
    xl_create(f"loadvm1")

    wait_domain("root@192.168.70.1")
    vfiobind("root@192.168.70.1")
    wait_domain("root@192.168.70.2")
    vfiobind("root@192.168.70.2")
    wait_domain("root@192.168.70.3")
    vfiobind("root@192.168.70.3")
    wait_domain("root@192.168.70.4")
    vfiobind("root@192.168.70.4")
    wait_domain("root@192.168.70.101")

    ssh_popen(f"root@192.168.70.1", f"nohup taskset -c 0 /root/seastar/build/release/apps/memcached/memcached --network-stack native --dpdk-pmd --dhcp 0 --host-ipv4-addr 10.0.0.1 --netmask-ipv4-addr 255.255.255.0 --smp 1 --port 12345 &", stdout=subprocess.DEVNULL)
    ssh_popen(f"root@192.168.70.2", f"nohup taskset -c 0 /root/seastar/build/release/apps/memcached/memcached --network-stack native --dpdk-pmd --dhcp 0 --host-ipv4-addr 10.0.0.2 --netmask-ipv4-addr 255.255.255.0 --smp 1 --port 12345 &", stdout=subprocess.DEVNULL)
    ssh_popen("root@192.168.70.3", f"nohup taskset -c 0 /root/seastar/build/release/apps/memcached/memcached --network-stack native --dpdk-pmd --dhcp 0 --host-ipv4-addr 10.0.0.3 --netmask-ipv4-addr 255.255.255.0 --smp 1 --port 12345 &", stdout=subprocess.DEVNULL)
    ssh_popen("root@192.168.70.4", f"nohup taskset -c 0 /root/seastar/build/release/apps/memcached/memcached --network-stack native --dpdk-pmd --dhcp 0 --host-ipv4-addr 10.0.0.4 --netmask-ipv4-addr 255.255.255.0 --smp 1 --port 12345 &", stdout=subprocess.DEVNULL)

    while client_popen("ping -c 1 -W 1 10.0.0.1").wait(): time.sleep(1)
    assert(client_popen(f"taskset -c 0 ~/mutilate/mutilate -s 10.0.0.1:12345 -T 1 --loadonly").wait() == 0)
    while client_popen("ping -c 1 -W 1 10.0.0.2").wait(): time.sleep(1)
    assert(client_popen(f"taskset -c 0 ~/mutilate/mutilate -s 10.0.0.2:12345 -T 1 --loadonly").wait() == 0)
    while client_popen("ping -c 1 -W 1 10.0.0.3").wait(): time.sleep(1)
    assert(client_popen(f"taskset -c 0 ~/mutilate/mutilate -s 10.0.0.3:12345 -T 1 --loadonly").wait() == 0)
    while client_popen("ping -c 1 -W 1 10.0.0.4").wait(): time.sleep(1)
    assert(client_popen(f"taskset -c 0 ~/mutilate/mutilate -s 10.0.0.4:12345 -T 1 --loadonly").wait() == 0)

    p_sysbench = ssh_popen("root@192.168.70.101", f"sysbench cpu --cpu-max-prime=10000 --threads=24 --time=80 --report-interval=1 run > {logdir}/sysbench")

    time.sleep(15)

    xl_cpupool_migrate("seastar1", "ls")
    xl_cpupool_migrate("seastar2", "ls")
    xl_cpupool_migrate("seastar3", "ls")
    xl_cpupool_migrate("seastar4", "ls")
    xl_cpupool_migrate("loadvm1", "be")

    xl_vcpu_pin("seastar1", "0", "1")
    xl_vcpu_pin("seastar2", "0", "2")
    xl_vcpu_pin("seastar3", "0", "3")
    xl_vcpu_pin("seastar4", "0", "4")

    time.sleep(15)

    client_popen(f"taskset -c 0-1 ~/mutilate/mutilate -s 10.0.0.1:12345 -T 2 -c 16 -q 1000 -u 0 -i exponential:1 -t 50 --noload --save={remotelogdir}/p0-vm1-samples > {logdir}/p0-vm1")
    client_popen(f"taskset -c 2-3 ~/mutilate/mutilate -s 10.0.0.2:12345 -T 2 -c 16 -q 1000 -u 0 -i exponential:1 -t 50 --noload --save={remotelogdir}/p0-vm2-samples > {logdir}/p0-vm2")
    client_popen(f"taskset -c 4-5 ~/mutilate/mutilate -s 10.0.0.3:12345 -T 2 -c 16 -q 1000 -u 0 -i exponential:1 -t 50 --noload --save={remotelogdir}/p0-vm3-samples > {logdir}/p0-vm3")
    client_popen(f"taskset -c 6-7 ~/mutilate/mutilate -s 10.0.0.4:12345 -T 2 -c 16 -q 1000 -u 0 -i exponential:1 -t 50 --noload --save={remotelogdir}/p0-vm4-samples > {logdir}/p0-vm4")
    time.sleep(10)
    client_popen(f"taskset -c  8-9  ~/mutilate/mutilate -s 10.0.0.1:12345 -T 2 -c 16 -q 9000 -u 0 -i exponential:1 -t 30 --noload --save={remotelogdir}/p1-vm1-samples > {logdir}/p1-vm1")
    client_popen(f"taskset -c 10-11 ~/mutilate/mutilate -s 10.0.0.2:12345 -T 2 -c 16 -q 9000 -u 0 -i exponential:1 -t 30 --noload --save={remotelogdir}/p1-vm2-samples > {logdir}/p1-vm2")
    client_popen(f"taskset -c 12-13 ~/mutilate/mutilate -s 10.0.0.3:12345 -T 2 -c 16 -q 9000 -u 0 -i exponential:1 -t 30 --noload --save={remotelogdir}/p1-vm3-samples > {logdir}/p1-vm3")
    client_popen(f"taskset -c 14-15 ~/mutilate/mutilate -s 10.0.0.4:12345 -T 2 -c 16 -q 9000 -u 0 -i exponential:1 -t 30 --noload --save={remotelogdir}/p1-vm4-samples > {logdir}/p1-vm4")
    time.sleep(10)
    client_popen(f"taskset -c 16-17 ~/mutilate/mutilate -s 10.0.0.1:12345 -T 2 -c 16 -q 90000 -u 0 -i exponential:1 -t 10 --noload --save={remotelogdir}/p2-vm1-samples > {logdir}/p2-vm1")
    client_popen(f"taskset -c 18-19 ~/mutilate/mutilate -s 10.0.0.2:12345 -T 2 -c 16 -q 90000 -u 0 -i exponential:1 -t 10 --noload --save={remotelogdir}/p2-vm2-samples > {logdir}/p2-vm2")
    client_popen(f"taskset -c 20-21 ~/mutilate/mutilate -s 10.0.0.3:12345 -T 2 -c 16 -q 90000 -u 0 -i exponential:1 -t 10 --noload --save={remotelogdir}/p2-vm3-samples > {logdir}/p2-vm3")
    client_popen(f"taskset -c 22-23 ~/mutilate/mutilate -s 10.0.0.4:12345 -T 2 -c 16 -q 90000 -u 0 -i exponential:1 -t 10 --noload --save={remotelogdir}/p2-vm4-samples > {logdir}/p2-vm4")

    p_sysbench.wait()

    client_fetch(remotelogdir, f"{logdir}/samples")
    assert(client_popen(f"rm -rf {remotelogdir}").wait() == 0)

    subprocess.run("./reset.sh", shell=True)


def pvcc(dataroot: str):
    libpath = f"LD_LIBRARY_PATH={os.path.abspath('./build-xen/pvcc/install/lib')}"
    path = f"PATH={os.path.abspath('./build-xen/pvcc/install/sbin')}"
    logdir = f"{dataroot}/pvcc"
    remotelogdir = "/tmp/fig11-pvcc"
    interval = 10
    margin = 1

    subprocess.run(f"mkdir -p {logdir}", shell=True)
    assert(client_popen(f"mkdir {remotelogdir}").wait() == 0)

    pool_pvcc.credit(tslice_us=100, ratelimit_us=0, cpus=[1], name="ls")
    pool_pvcc.credit(tslice_us=30000, ratelimit_us=1000, cpus=[2,3,4,5,6], name="be")

    xl_create(f"seastar1")
    time.sleep(1)
    xl_create(f"seastar2")
    time.sleep(1)
    xl_create(f"seastar3")
    time.sleep(1)
    xl_create(f"seastar4")
    time.sleep(1)
    xl_create(f"loadvm1")

    spopen(f"{libpath} {path} ./pvcc-server/build/pvccsrv", shell=True)

    wait_domain("root@192.168.70.1")
    vfiobind("root@192.168.70.1")
    wait_domain("root@192.168.70.2")
    vfiobind("root@192.168.70.2")
    wait_domain("root@192.168.70.3")
    vfiobind("root@192.168.70.3")
    wait_domain("root@192.168.70.4")
    vfiobind("root@192.168.70.4")
    wait_domain("root@192.168.70.101")

    ssh_popen(f"root@192.168.70.1", f"nohup taskset -c 0 /root/seastar/build/release/apps/memcached/memcached --network-stack native --dpdk-pmd --dhcp 0 --host-ipv4-addr 10.0.0.1 --netmask-ipv4-addr 255.255.255.0 --smp 1 --port 12345 &", stdout=subprocess.DEVNULL)
    ssh_popen(f"root@192.168.70.2", f"nohup taskset -c 0 /root/seastar/build/release/apps/memcached/memcached --network-stack native --dpdk-pmd --dhcp 0 --host-ipv4-addr 10.0.0.2 --netmask-ipv4-addr 255.255.255.0 --smp 1 --port 12345 &", stdout=subprocess.DEVNULL)
    ssh_popen("root@192.168.70.3", f"nohup taskset -c 0 /root/seastar/build/release/apps/memcached/memcached --network-stack native --dpdk-pmd --dhcp 0 --host-ipv4-addr 10.0.0.3 --netmask-ipv4-addr 255.255.255.0 --smp 1 --port 12345 &", stdout=subprocess.DEVNULL)
    ssh_popen("root@192.168.70.4", f"nohup taskset -c 0 /root/seastar/build/release/apps/memcached/memcached --network-stack native --dpdk-pmd --dhcp 0 --host-ipv4-addr 10.0.0.4 --netmask-ipv4-addr 255.255.255.0 --smp 1 --port 12345 &", stdout=subprocess.DEVNULL)

    while client_popen("ping -c 1 -W 1 10.0.0.1").wait(): time.sleep(1)
    assert(client_popen(f"taskset -c 0 ~/mutilate/mutilate -s 10.0.0.1:12345 -T 1 --loadonly").wait() == 0)
    while client_popen("ping -c 1 -W 1 10.0.0.2").wait(): time.sleep(1)
    assert(client_popen(f"taskset -c 0 ~/mutilate/mutilate -s 10.0.0.2:12345 -T 1 --loadonly").wait() == 0)
    while client_popen("ping -c 1 -W 1 10.0.0.3").wait(): time.sleep(1)
    assert(client_popen(f"taskset -c 0 ~/mutilate/mutilate -s 10.0.0.3:12345 -T 1 --loadonly").wait() == 0)
    while client_popen("ping -c 1 -W 1 10.0.0.4").wait(): time.sleep(1)
    assert(client_popen(f"taskset -c 0 ~/mutilate/mutilate -s 10.0.0.4:12345 -T 1 --loadonly").wait() == 0)

    p_sysbench = ssh_popen("root@192.168.70.101", f"sysbench cpu --cpu-max-prime=10000 --threads=24 --time=80 --report-interval=1 run > {logdir}/sysbench")
    time.sleep(15)

    xl_cpupool_migrate(f"seastar1", "ls")
    xl_cpupool_migrate(f"seastar2", "ls")
    xl_cpupool_migrate(f"seastar3", "ls")
    xl_cpupool_migrate(f"seastar4", "ls")
    xl_cpupool_migrate("loadvm1", "be")

    time.sleep(15)

    scaling_api_send(phase=0)
    client_popen(f"taskset -c 0-1 ~/mutilate/mutilate -s 10.0.0.1:12345 -T 2 -c 16 -q 1000 -u 0 -i exponential:1 -t 50 --noload --save={remotelogdir}/p0-vm1-samples > {logdir}/p0-vm1 ; echo 'finished p0-vm1'")
    client_popen(f"taskset -c 2-3 ~/mutilate/mutilate -s 10.0.0.2:12345 -T 2 -c 16 -q 1000 -u 0 -i exponential:1 -t 50 --noload --save={remotelogdir}/p0-vm2-samples > {logdir}/p0-vm2 ; echo 'finished p0-vm2'")
    client_popen(f"taskset -c 4-5 ~/mutilate/mutilate -s 10.0.0.3:12345 -T 2 -c 16 -q 1000 -u 0 -i exponential:1 -t 50 --noload --save={remotelogdir}/p0-vm3-samples > {logdir}/p0-vm3 ; echo 'finished p0-vm3'")
    p_mutilate = client_popen(f"taskset -c 6-7 ~/mutilate/mutilate -s 10.0.0.4:12345 -T 2 -c 16 -q 1000 -u 0 -i exponential:1 -t 50 --noload --save={remotelogdir}/p0-vm4-samples > {logdir}/p0-vm4 ; echo 'finished p0-vm4'")
    time.sleep(interval - margin)
    scaling_api_send(phase=1)
    time.sleep(margin)
    client_popen(f"taskset -c  8-9  ~/mutilate/mutilate -s 10.0.0.1:12345 -T 2 -c 16 -q 9000 -u 0 -i exponential:1 -t 30 --noload --save={remotelogdir}/p1-vm1-samples > {logdir}/p1-vm1 ; echo 'finished p1-vm1'")
    client_popen(f"taskset -c 10-11 ~/mutilate/mutilate -s 10.0.0.2:12345 -T 2 -c 16 -q 9000 -u 0 -i exponential:1 -t 30 --noload --save={remotelogdir}/p1-vm2-samples > {logdir}/p1-vm2 ; echo 'finished p1-vm2'")
    client_popen(f"taskset -c 12-13 ~/mutilate/mutilate -s 10.0.0.3:12345 -T 2 -c 16 -q 9000 -u 0 -i exponential:1 -t 30 --noload --save={remotelogdir}/p1-vm3-samples > {logdir}/p1-vm3 ; echo 'finished p1-vm3'")
    client_popen(f"taskset -c 14-15 ~/mutilate/mutilate -s 10.0.0.4:12345 -T 2 -c 16 -q 9000 -u 0 -i exponential:1 -t 30 --noload --save={remotelogdir}/p1-vm4-samples > {logdir}/p1-vm4 ; echo 'finished p1-vm4'")
    time.sleep(interval - margin)
    scaling_api_send(phase=2)
    client_popen(f"taskset -c 16-17 ~/mutilate/mutilate -s 10.0.0.1:12345 -T 2 -c 16 -q 90000 -u 0 -i exponential:1 -t 10 --noload --save={remotelogdir}/p2-vm1-samples > {logdir}/p2-vm1 ; echo 'finished p2-vm1'")
    client_popen(f"taskset -c 18-19 ~/mutilate/mutilate -s 10.0.0.2:12345 -T 2 -c 16 -q 90000 -u 0 -i exponential:1 -t 10 --noload --save={remotelogdir}/p2-vm2-samples > {logdir}/p2-vm2 ; echo 'finished p2-vm2'")
    client_popen(f"taskset -c 20-21 ~/mutilate/mutilate -s 10.0.0.3:12345 -T 2 -c 16 -q 90000 -u 0 -i exponential:1 -t 10 --noload --save={remotelogdir}/p2-vm3-samples > {logdir}/p2-vm3 ; echo 'finished p2-vm3'")
    client_popen(f"taskset -c 22-23 ~/mutilate/mutilate -s 10.0.0.4:12345 -T 2 -c 16 -q 90000 -u 0 -i exponential:1 -t 10 --noload --save={remotelogdir}/p2-vm4-samples > {logdir}/p2-vm4 ; echo 'finished p2-vm4'")
    time.sleep(interval + margin)
    scaling_api_send(phase=3)
    time.sleep(interval)
    scaling_api_send(phase=4)
    
    p_sysbench.wait()
    p_mutilate.wait()

    client_fetch(remotelogdir, f"{logdir}/samples")
    assert(client_popen(f"rm -rf {remotelogdir}").wait() == 0)

    subprocess.run("./reset.sh", shell=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--trial", type=int)
    args = parser.parse_args()

    dataroot = "data/fig11"
    supplement = ""
    if args.trial is not None:
        supplement = f".{str(args.trial).zfill(2)}"
        dataroot = f"data/fig11{supplement}"

    naive(dataroot)
    pin(dataroot)
    pvcc(dataroot)

