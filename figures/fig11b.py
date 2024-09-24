import pandas as pd
from dep import *
import sys
import argparse

dpdk_vm_num = 4
phase_num = 3

def run(plt, dataroot, outfile):
    plt.rcParams.update(rcParams_halfwidth)
    plt.plot([], [])

    for vm_num in range(1, dpdk_vm_num + 1):
        df_phase = []
        for phase in range(phase_num):
            df = pd.read_csv(f"{dataroot}/pvcc/samples/p{phase}-vm{vm_num}-samples", sep=' ', header=None, names=['start_time', 'latency'], dtype={'start_time': 'float64', 'latency': 'float64'})
            df_phase.append(df)
        latency = []
        for i in range(50):
            df_phase_sec = []
            for phase in range(phase_num):
                df_phase_sec.append(df_phase[phase].query(f'{i - 10 * phase} <= start_time < {i - 10 * phase + 1}'))
            df_sec = pd.concat(df_phase_sec, axis=0)
            latency.append(df_sec['latency'].quantile(0.99, interpolation="nearest"))
        
        plt.plot(latency, label=f'vm{vm_num}', ms=5)

# plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=4)
    plt.legend(**(params_legend_upper_center | { "ncol": 4, "handlelength": 1.5, }))
# plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=4, frameon=False, handletextpad=0.7, fontsize=10, columnspacing=1.3)

    plt.xlim([0, 50])
    plt.ylim([0, 1700])
    plt.xlabel('Elapsed Time [s]')
    plt.ylabel('99%-ile Latency [µs]')
    plt.yticks([0, 500, 1000, 1500])

#targets = [500, 1000, 2000, 4000]
    targets = [300, 600, 1200, 2400]

    for target in targets:
        plt.axhline(y=target, color='gray', linestyle=':', linewidth=1)
        plt.annotate(f'{target}µs', xy=(50, target), color='gray', fontsize=9)
        # ax.annotate(f'{slo}µs', xy=(xlim * 0.85, slo), color='gray', fontsize=8)
    plt.savefig(outfile, bbox_inches="tight")
# plt.show()

def main():
    import matplotlib.pyplot as plt

    parser = argparse.ArgumentParser()
    parser.add_argument("--trial", type=int)
    args = parser.parse_args()

    dataroot = "/data/fig11"
    outfile = "/figures/fig11b.pdf"
    if args.trial is not None:
        supplement = f".{str(args.trial).zfill(2)}"
        dataroot = f"/data/fig11{supplement}"
        outfile = f"/figures/fig11b{supplement}.pdf"

    run(plt, dataroot, outfile)

if __name__ == "__main__":
    main()

