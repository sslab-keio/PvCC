import subprocess

# XL = "LD_LIBRARY_PATH=./build-xen/vanilla/install/lib ./build-xen/vanilla/install/sbin/xl"
XL = "xl"

def credit(tslice_ms: int, ratelimit_us, cpus: list):
    subprocess.run(f"{XL} cpupool-create ./cpupools/credit.cfg", check=True, shell=True)
    subprocess.run(f"{XL} sched-credit -s -t {tslice_ms} -r {ratelimit_us} -p credit", check=True, shell=True)
    for cpu in cpus:
        subprocess.run(f"{XL} cpupool-cpu-remove Pool-0 {cpu}", check=True, shell=True)
        subprocess.run(f"{XL} cpupool-cpu-add credit {cpu}", check=True, shell=True)

def credit2(ratelimit_us, cpus: list):
    subprocess.run(f"{XL} cpupool-create ./cpupools/credit2.cfg", check=True, shell=True)
    subprocess.run(f"{XL} sched-credit2 -s -r {ratelimit_us} -p credit2", check=True, shell=True)
    for cpu in cpus:
        subprocess.run(f"{XL} cpupool-cpu-remove Pool-0 {cpu}", check=True, shell=True)
        subprocess.run(f"{XL} cpupool-cpu-add credit2 {cpu}", check=True, shell=True)

