import subprocess
import time
import dotenv
import os

# XL = "LD_LIBRARY_PATH=./build-xen/pvcc/install/lib ./build-xen/pvcc/install/sbin/xl"
XL = "xl"
CONFDIR = "./domu-configs"
SSHPARAMS = "-o ConnectTimeout=1 -o StrictHostKeyChecking=no"

dotenv.load_dotenv(".env")
client_username = os.getenv("CLIENT_USERNAME")
client_addr = os.getenv("CLIENT_ADDR")

def sprun(cmd, **kwargs):
    print(f"+ {cmd}")
    proc = subprocess.run(cmd, **kwargs)
    if proc.returncode:
        print(f"\033[0;31mError: \ncommand: {cmd}\nstderr: {proc.stderr}\nstdout: {proc.stdout}\033[0m")
        exit(1)
    return proc

def spopen(cmd, **kwargs):
    print(f"+ {cmd}")
    return subprocess.Popen(cmd, **kwargs)

def xl_cpupool_migrate(domain: str, cpupool_name: str) -> subprocess.CompletedProcess:
    return sprun(f"{XL} cpupool-migrate {domain} {cpupool_name}", shell=True, check=True)

def xl_create(domain: str) -> subprocess.CompletedProcess:
    return sprun(f"{XL} create {CONFDIR}/{domain}.cfg", check=True, shell=True)

def xl_vcpu_pin(domain: str, vcpu: str, hard_affinity: str) -> subprocess.CompletedProcess:
    return sprun(f"{XL} vcpu-pin {domain} {vcpu} {hard_affinity}", shell=True, check=True)

def ssh_run(host: str, command: str, **kwargs):
    return sprun(f"ssh {SSHPARAMS} {host} {command}", shell=True, **kwargs)

def ssh_popen(host: str, command: str, **kwargs):
    return spopen(f"ssh {SSHPARAMS} {host} {command}", shell=True, **kwargs)

def wait_domain(host: str):
    print(f"Waiting for {host} ", end="", flush=True)
    while subprocess.run(f"ssh {SSHPARAMS} {host} :", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
        print(".", end="", flush=True)
        time.sleep(1)
    print("")

def vfiobind(host: str):
    return ssh_run(host, f"/dpdk-usertools/dpdk-devbind.py -b vfio-pci 00:06.0", check=True)

def client_popen(command: str, **kwargs):
    return spopen(f"ssh {SSHPARAMS} {client_username}@{client_addr} {command}", shell=True, **kwargs)

def client_fetch(remote_path: str, local_path: str):
    return sprun(f"scp {SSHPARAMS} -r {client_username}@{client_addr}:{remote_path} {local_path}", shell=True)

