import pandas as pd
import numpy as np
import sys
import argparse

def run(plt, dataroot, outfile):
    plt.rcParams.update(plt.rcParamsDefault | {
        "font.size": 10,
        "figure.figsize": [4.8, 3.0],
        "legend.fontsize": 10,
        "lines.markersize": 5,
        "axes.titlesize": 10,
        "figure.titlesize": 10,
    })

    params_legend_upper_center = {
        "loc": "upper center",
        "bbox_to_anchor": (0.5, 1.25),
        "frameon": False,
        "handlelength": 0,
        "handletextpad": 0.7,
        "fontsize": 10,
        "columnspacing": 1.3,
    }

    dpdk_vm_num = 4
    phase_num = 3
    y_prefix = 1000
    plotparams = {
        "pvcc_100": { "label": "PvCC", "color": "darkorange", "marker": "|", "markersize": 6 },
        "pin_1000": { "label": "Pin", "color": "royalblue", },
        "naive_1000": { "label": "Naive", "color": "turquoise", },
    }

    for (setup, label, root_dir, marker) in [
        ('pvcc_100', "PvCC", f"{dataroot}/pvcc/samples", "o"),
        ('pin_1000', "Pin", f"{dataroot}/pin/samples", "^"),
        ('naive_1000', "Naive", f"{dataroot}/naive/samples", "s"),
    ]:
        for vm_num in range(1, dpdk_vm_num + 1):
            df_phase = []
            for phase in range(phase_num):
                df = pd.read_csv(f"{root_dir}/p{phase}-vm{vm_num}-samples", sep=' ', header=None, names=['start_time', 'latency'], dtype={'start_time': 'float64', 'latency': 'float64'})
                df_phase.append(df)
                
            throughputs = []
            for i in range(50):
                df_phase_sec = []
                for phase in range(phase_num):
                    df_phase_sec.append(df_phase[phase].query(f'{i - 10 * phase} <= start_time < {i - 10 * phase + 1}'))
                df_sec = pd.concat(df_phase_sec, axis=0)
                throughputs.append(df_sec['latency'].count())
            if vm_num == 1:
                total_throughputs = np.array(throughputs)
            else:
                total_throughputs += np.array(throughputs)
                
        plt.plot(total_throughputs / y_prefix, **plotparams[setup])
    plt.legend(**(params_legend_upper_center | { "ncol": 3, "handlelength": 1.5, }))
    plt.xlabel('Time [s]')
    plt.ylabel('Total Throughput\n[Kqueries/sec]')
    plt.xlim((0, 50))
    plt.ylim(0)
    plt.yticks(list(range(0, 400 + 1, 100)))
    plt.savefig(outfile, bbox_inches="tight")


def main():
    import matplotlib.pyplot as plt

    parser = argparse.ArgumentParser()
    parser.add_argument("--trial", type=int)
    args = parser.parse_args()

    dataroot = "/data/fig11"
    outfile = "/figures/fig11a.pdf"
    if args.trial is not None:
        supplement = f".{str(args.trial).zfill(2)}"
        dataroot = f"/data/fig11{supplement}"
        outfile = f"/figures/fig11a{supplement}.pdf"

    run(plt, dataroot, outfile)

if __name__ == "__main__":
    main()

