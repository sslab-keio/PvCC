# PvCC: A vCPU Scheduling Policy for DPDK-applied Systems at Multi-Tenant Edge Data Centers

## Overview

This repository contains the artifact for the Middleware'24 paper (to appear).

> Yuki Tsujimoto, Yuki Sato, Kenichi Yasukata, Kenta Ishiguro, and Kenji Kono. 2024. PvCC: A vCPU Scheduling Policy for DPDK-applied Systems at Multi-Tenant Edge Data Centers. In Proceedings of 25th International Middleware Conference (Middleware ’24)

This paper explores a practical means to employ Data Plane Development Kit (DPDK) in resource-limited multi-tenant edge data centers.

## Getting Started

### Prerequisites

- Two Linux machines
    - We recommend Ubuntu 18.04 for the server and Ubuntu 20.04 for the client
- Network access
- SR-IOV capable 10G NIC
- Software
    - Docker and docker-compose to draw the figures
        - Refer to [docker official document](https://docs.docker.com/engine/install/) for installation guide

### Experimental Setup

We conduct the evaluation with the following machines (server and client).

|||
|-|-|
|CPU            |Intel Xeon Gold 5318Y CPU @ 2.10GHz|
|DRAM           |128GiB, 4 * 32GiB DDR4 3200 MHz    |
|NIC            |Intel X540-AT2 (direct connect)    |
|Hyper Threading|disabled                           |
|C-State        |disabled                           |

The server machine runs Xen hypervisor v4.12.1 with Ubuntu 18.04 and Linux v4.15.0.

The client machine runs Ubuntu 20.04.

## Server Side Setups
### Build and Install PvCC

Clone this repository and fetch all submodules on the server machine.
```sh
$ git clone https://github.com/sslab-keio/PvCC
$ cd PvCC
$ git submodule update --init --recursive
```

Install build dependencies as follows.
```sh
$ sudo apt build-dep xen  # Need to enable source repository
$ sudo apt install build-essential bcc bin86 gawk bridge-utils iproute2 libcurl4-openssl-dev bzip2 module-init-tools transfig tgif texinfo texlive-latex-base texlive-latex-recommended texlive-fonts-extra texlive-fonts-recommended libpci-dev mercurial make gcc libc6-dev zlib1g-dev python python-dev python-twisted libncurses5-dev patch libvncserver-dev libsdl1.2-dev acpica-tools libbz2-dev e2fslibs-dev git uuid-dev ocaml ocaml-findlib libx11-dev bison flex xz-utils libyajl-dev gettext libpixman-1-dev libaio-dev markdown pandoc ninja-build meson libsystemd-dev python3 python3-dotenv
```

Build and install vanilla Xen and Xen equipped with PvCC.
```sh
$ cd $ARTIFACT_ROOT           # Path to the cloned repository
$ build-xen/vanilla/build.sh  # For vanilla Xen
$ build-xen/pvcc/build.sh     # For PvCC
```

Reboot into the vanilla Xen with the following commands.
```sh
$ echo "GRUB_DISABLE_SUBMENU=y" | sudo tee -a /etc/default/grub
$ echo 'GRUB_CMDLINE_LINUX_DEFAULT="nomdmonddf nomdmonisw intel_iommu=on pci=assign-busses"' | sudo tee -a /etc/default/grub
$ echo 'GRUB_CMDLINE_XEN="timer_slop=0 max_cstate=0"' | sudo tee -a /etc/default/grub
$ sudo update-grub
$ sudo grub-reboot "Ubuntu GNU/Linux, with Xen 4.12.1-ae-vanilla and Linux `uname -r`"
$ sudo reboot
```

### Network configuration

**Netplan configuration**

`${ARTIFACT_ROOT}/netplan/server/50-ae.yaml` is a netplan configuration for the server.

Update the following points according to your environment.

- \<netif SR-IOV PF\>
    - an SR-IOV physical function
- \<netif external\>
    - a network interface to the external network


```yaml
network:
    ethernets:
        <netif SR-IOV PF>:
            virtual-function-count: 32
    bridges:
        xenbr0:
            addresses: [192.168.70.250/24]
            dhcp4: false
        xenbr1:
            interfaces:
              - <netif external>
            dhcp4: true
    version: 2
```



Apply the updated netplan configuration.
```sh
$ cd $ARTIFACT_ROOT
$ sudo cp netplan/server/50-ae.yaml /etc/netplan
$ sudo netplan apply
```

**SSH setup**

Set up an SSH key so that the **root** user can log in to the client machine.

Fill in the username and the client's address for SSH login in the .env file, copied from .env.template.

```sh
$ cd ${ARTIFACT_ROOT}
$ cp .env.template .env
$ $EDITOR .env

# .env file example:
CLIENT_USERNAME="somebody"
CLIENT_ADDR="client.machine.example.com"
## or
CLIENT_ADDR="192.168.50.10"
```

### Preparing VM configuration files
A VM configuration file needs an absolute path to the kernel, initrd, and root filesystem image.

By default, the seastar and sysbench VMs need a Linux kernel v4.15.0 image and initrd under `/boot`.
The F-Stack VMs need a Linux kernel v5.15.0 image and initrd.
Update `kernel` and `ramdisk` parameters within configuration files according to your environment.

The script `domu-configs/populate_path.sh` completes a placeholder of the root filesystem image path inside the configuration file.

```sh
$ cd $ARTIFACT_ROOT
$ domu-configs/populate_path.sh
```

### Preparing VM root filesystem images

Retrieve base images by `debootstrap` command.
```sh
$ sudo apt install debootstrap
$ cd $ARTIFACT_ROOT
$ sudo debootstrap bionic images/debootstrap-bionic
$ sudo debootstrap jammy images/debootstrap-jammy
```

Run the following commands to create each image.
Before executing the following scripts, place an SSH key to log in to VMs under `/root/.ssh/`.
These scripts register /root/.ssh/*.pub to VMs' `authorized_keys`.
```sh
$ cd $ARTIFACT_ROOT
$ images/seastar.sh   # For seastar
$ images/fstack.sh    # For F-Stack
$ images/sysbench.sh  # For sysbench
```

### Compiling vCPU scaling API server

The vCPU scaling API server scales up and down the number of dedicated physical CPUs for I/O.

Compile the vCPU scaling API server with the following commands.

```sh
$ cd ${ARTIFACT_ROOT}/pvcc-server
$ make
```

## Client Side Setups

### Installing benchmark tools

Install mutilate, wrk2, and memtier_benchmark on the client machine.
```
# Install build dependencies
$ sudo apt install -y scons libevent-dev gengetopt libzmq3-dev make libevent-dev libpcre3-dev libssl-dev autoconf automake pkg-config make g++

$ cd $HOME
$ git clone https://github.com/leverich/mutilate
$ cd mutilate
$ git checkout d65c6ef7c2f78ae05a9db3e37d7f6ddff1c0af64
$ sed -i -E 's/print "(.*)"/print("\1")/g' SConstruct
$ scons

$ cd $HOME
$ git clone https://github.com/giltene/wrk2
$ cd wrk2
$ git checkout 44a94c17d8e6a0bac8559b53da76848e430cb7a7
$ make

$ cd $HOME
$ git clone https://github.com/RedisLabs/memtier_benchmark
$ cd memtier_benchmark
$ git checkout 0c0c440a0cb8f7e0195b86520cd261f823f8e2e0
$ autoreconf -ivf
$ ./configure
$ make
```

### Network configuration

A netplan configuration file for the server (`${ARTIFACT_ROOT}/netplan/client/50-ae.yaml`) is as follows.

Update the following point according to your environment.

- \<netif to server\>
    - a network interface to communicate with the server machine

```yaml
network:
  ethernets:
    <netif to server>:
      dhcp4: no
      addresses: [10.0.0.250/24]
```

Apply the updated configuration.
```
$ sudo cp <path/to/the/config/above> /etc/netplan
$ sudo netplan apply
```

## Major Claims

* **Claim 1**: DPDK applied system can utilize CPU cycles more efficiently than the kernel network stack. (Figure 2)
* **Claim 2**: In consolidated setup, serving latency of DPDK-applied systems increases. (Figure 6)
* **Claim 3**: The serving latency can be decreased by adopting a microsecond-scale time slice. (Figure 6)
* **Claim 4**: Short time slices trade off maximum throughput for low serving latency. (Figure 10)
* **Claim 5**: vCPU scaling API mitigates this trade-off by changing the CPU overcommitment ratio. (Figure 11)

## Experiment workflows

### Experiment for Claim 1

To quantify the optimizations of DPDK, this experiment compares the performance of the DPDK-based network stack and the kernel network stack.

To conduct the experiment, run:

```sh
$ cd $ARTIFACT_ROOT

$ sudo python3 experiments/fig02.py
$ ls data/fig02/dpdk data/fig02/linux

$ sudo docker compose run --rm graph python3 /scripts/fig02.py
$ ls figures/fig02.pdf
```

You will see that DPDK achieves around higher throughput than the kernel network stack, using the same amount of CPU resources (Claim 1).

<details>
    <summary>Evaluation with restrictive data</summary>

In case of time constraints, you can evaluate the optimization of DPDK with restrictive data.

```sh
$ cd $ARTIFACT_ROOT

# Picking up fewer cases;
# The client benchmark tool uses 1, 12, or 24 threads
$ sudo python3 experiments/fig02.py --threads 1 12 24 --trial 1
$ sudo docker compose run --rm graph python3 /scripts/fig02.py --threads 1 12 24 --trial 1
```
</details>

### Experiment for Claim 2,3

This experiment compares PvCC with the baseline settings, the Credit and Credit2 schedulers of Xen.

First, run the experiment for Credit and Credit2 schedulers with vanilla Xen.
```sh
$ cd $ARTIFACT_ROOT

$ sudo python3 experiments/fig06_vanilla.py
$ ls data/fig06/memcached/credit data/fig06/memcached/credit2
$ ls data/fig06/nginx/credit data/fig06/nginx/credit2
$ ls data/fig06/redis/credit data/fig06/redis/credit2
```

Then, run the experiment for PvCC.
```sh
# Reboot into Xen equipped with PvCC.
$ sudo grub-reboot "Ubuntu GNU/Linux, with Xen 4.12.1-ae-pvcc and Linux `uname -r`"
$ sudo reboot

# Apply netplan again
$ sudo netplan apply

# Run the experiment
$ cd $ARTIFACT_ROOT
$ sudo python3 experiments/fig06_pvcc.py
$ ls data/fig06/memcached/pvcc
$ ls data/fig06/nginx/pvcc
$ ls data/fig06/redis/pvcc
```

To summarize the result in a figure, run:
```sh
$ cd $ARTIFACT_ROOT
$ sudo docker compose run --rm graph python3 /scripts/fig06.py
$ ls figures/fig06.pdf
```

In `figures/fig06.pdf`, you will see the default Credit or Credit2 scheduler always causes a 99th-percentile latency of several milliseconds (Claim 2).

PvCC is expected to achieve 99th-percentile latency of sub-milliseconds in memcached and around one millisecond in nginx and Redis.

This result shows that a microsecond-scale time slice can reduce serving latency of DPDK (Claim 3).

<details>
    <summary>Evaluation with restrictive data</summary>

You can evaluate the benefit of a microsecond-scale time slice with restrictive data.

```sh
$ cd $ARTIFACT_ROOT

# Picking up one workload (memcached)
# Restricting the variety of incoming load (only 5000, 40000, 90000 RPS)
$ sudo python3 experiments/fig06_vanilla.py --workloads memcached --rates 5000 40000 90000 --trial 1
$ sudo python3 experiments/fig06_pvcc.py --workloads memcached --rates 5000 40000 90000 --trial 1
$ sudo docker compose run --rm graph python3 /scripts/fig06.py --workloads memcached --rates 5000 40000 90000 --trial 1
```
</details>

### Experiment for Claim 4
This experiment shows how the short time slices trade-off maximum throughput for low serving latency.

Run the following commands to conduct the experiment.

```sh
$ cd $ARTIFACT_ROOT
$ sudo python3 experiments/fig10.py
$ ls data/fig10
$ sudo docker compose run --rm graph python3 /scripts/fig10.py
$ ls figures/fig10.pdf
```

In `figures/fig10.pdf`, you will see that short time slices offer the latency advantage when the incoming request rate is low.

However, as the number of consolidated VMs increases, the maximum throughput of short time slices is substantially reduced due to the frequent context switch overhead.

This means that short time slices offer low latency at the expense of high maximum throughput (Claim 4).

<details>
    <summary>Evaluation with restrictive data</summary>

The following commands consider:
- 4VM consolidation
- [100, 1000] µs timeslices
- [1000, 40000, 100000] incoming RPS

```sh
$ cd $ARTIFACT_ROOT

$ sudo python3 experiments/fig10.py --vms 4 --tslices 100 1000 --rates 1000 40000 100000 --trial 1
$ sudo docker compose run --rm graph python3 /scripts/fig10.py --vms 4 --tslices 100 1000 --rates 1000 40000 100000 --trial 1
```
</details>

### Experiment for Claim 5
This experiment shows how the vCPU scaling API contributes to handling load increase.

Run the following commands to conduct the experiment.

```sh
$ cd $ARTIFACT_ROOT
$ sudo python3 experiments/fig11.py
$ ls data/fig11
$ sudo docker compose run --rm graph python3 /scripts/fig11a.py
$ sudo docker compose run --rm graph python3 /scripts/fig11b.py
$ sudo docker compose run --rm graph python3 /scripts/fig11c.py
$ ls figures/fig11a.pdf figures/fig11b.pdf figures/fig11c.pdf
```

"PvCC" denotes the setup with the short time slice (100us) adopting the vCPU scaling API.

In `figures/fig11a.pdf`, you will see that the PvCC case keeps up with the performance of the Pin case where physical CPUs are dedicated to each latency-sensitive task.

In `figures/fig11c.pdf`, you will observe that, with the vCPU scaling API, the best-effort task can utilize the CPU time while it is not used by latency-sensitive tasks.

These results show that the vCPU scaling API successfully handles dynamically changing workloads (Claim 5) and preserves CPU cycles for best-effort tasks.
