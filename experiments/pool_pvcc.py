import subprocess

XL = "LD_LIBRARY_PATH=./build-xen/pvcc/install/lib ./build-xen/pvcc/install/sbin/xl"

def credit(tslice_us: int, ratelimit_us, cpus: list, name="credit"):
    subprocess.run(f"{XL} cpupool-create ./cpupools/{name}.cfg", check=True, shell=True)
    subprocess.run(f"{XL} sched-credit -s -u {tslice_us} -r {ratelimit_us} -p {name}", check=True, shell=True)
    for cpu in cpus:
        subprocess.run(f"{XL} cpupool-cpu-remove Pool-0 {cpu}", check=True, shell=True)
        subprocess.run(f"{XL} cpupool-cpu-add {name} {cpu}", check=True, shell=True)

