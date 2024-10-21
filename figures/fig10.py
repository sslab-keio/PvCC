import matplotlib.pyplot as plt
import seaborn as sns
from parser import Mutilate
import argparse

sns.set_palette("tab10")

fig, axes = plt.subplots(2, 3, figsize=(12, 5))

plt.rcParams.update(plt.rcParamsDefault | {
    "font.size": 10,
    "figure.figsize": [4.8, 3.0],
    "legend.fontsize": 10,
    "lines.markersize": 5,
    "axes.titlesize": 10,
    "figure.titlesize": 10,
})

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

dataroot = "/data/fig10"
outfile = "/figures/fig10.pdf"
if args.trial is not None:
    idx = str(args.trial).zfill(2)
    dataroot = f"/data/fig10.{idx}"
    outfile = f"/figures/fig10.{idx}.pdf"

vms = [1,2,4,8,16,32]
if args.vms:
    vms = args.vms

for (dpdk_vm_num, preset_qpss, scale, ax, slos, xlim, conn) in [
    (1, None, 1, axes[0, 0], [300,600], 500, 128),
    (2, None, 2, axes[0, 1], [300,600,1200], 225, 128),
    (4, None, 5, axes[0, 2], [300,600,1200,2400], 100, 128),
    (8, None, 9, axes[1, 0], [600,1200,2400], 50, 128),
    (16, None, 18, axes[1, 1], [600,2400], 25, 64),
    (32, None, 36, axes[1, 2], [600,2400], 12, 64),
]:
    if dpdk_vm_num not in vms:
        continue

    ax.plot([], [])
    ax.plot([], [])

    tslices = [50,100,500,1000]
    if args.tslices:
        tslices = args.tslices

    for tslice in tslices:
        x = []
        y = []

        linestyle = "-"
        rates = all_rates[dpdk_vm_num][tslice]
        if args.rates:
            rates = args.rates
        
        for qps in rates:
            summary = Mutilate.parse(f"{dataroot}/{dpdk_vm_num}vms/{tslice}us/{qps}qps")
            x.append(summary.qps / 1000)
            y.append(summary.read_p99)
        
        ax.plot(x, y, marker="o", markersize=4, label=f'Tslice={tslice}µs', linestyle=linestyle)

    ax.set_xlabel('Throughput [Kqueries/sec]')
    ax.set_ylabel('99%-ile Latency [µs]')
    ax.set_xlim([0, xlim])
    
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.20), ncol=4, frameon=False, handlelength=0, handletextpad=0.9, fontsize=9, columnspacing=1.5)

    ax.set_title(f'{dpdk_vm_num} VM', y=-0.45)
    
    for slo in slos:
        ax.axhline(y=slo, color='gray', linestyle=':', linewidth=1)
        ax.annotate(f'{slo}µs', xy=(xlim * 0.85, slo), color='gray', fontsize=8)
        
plt.subplots_adjust(wspace=0.35, hspace=0.47)
plt.savefig(outfile, bbox_inches="tight")

