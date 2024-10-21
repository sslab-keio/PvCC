from parser import Mutilate
import sys
import argparse

conns_per_thread = 7

labels = {"linux": "Linux", "dpdk": "DPDK"}
plotparams = {
    "linux": { "label": 'Linux', "marker": "D", "color": "#ffb84c", "markersize": 5 },
    "dpdk": { "label": 'DPDK', "marker": "$✳$", "color": "#a459d1", "markeredgewidth": 0.001, "markersize": 8 },
}
legendparams = {
    "loc": "upper center",
    "bbox_to_anchor": (0.5, 1.13),
    "frameon": False,
    "handlelength": 0,
    "fontsize": 10,
    "ncol": 2,
    "handletextpad": 1.1,
    "columnspacing": 2.2,
}

def plot(plt, dataroot: str, setup: str, threads: list, linestyle: str):
    connections = list(map(lambda x: conns_per_thread * x, threads))
    throughputs = []
    for connection in connections:
        summary = Mutilate.parse(f"{dataroot}/{setup}/{connection}conns")
        throughputs.append(summary.qps / 1000)
    plt.plot(connections, throughputs, **plotparams[setup], linestyle=linestyle)

def draw(plt, outfile: str):
    plt.yticks(list(range(0, 400 + 1, 100)))
    plt.xlim((0))
    plt.ylim((0, 470))
    plt.xlabel("Connections")
    plt.ylabel("Throughput [K queries/sec]")
    plt.legend(**legendparams)
    plt.savefig(outfile, bbox_inches="tight")

def main():
    import matplotlib.pyplot as plt

    plt.rcParams.update(plt.rcParamsDefault | {
        "font.size": 10,
        "figure.figsize": [4.8, 3.0],
        "legend.fontsize": 10,
        "lines.markersize": 5,
        "axes.titlesize": 10,
        "figure.titlesize": 10,
    })

    parser = argparse.ArgumentParser()
    parser.add_argument("--threads", type=int, nargs="*")
    parser.add_argument("--trial", type=int)
    args = parser.parse_args()

    linestyle = "-"
    threads = list(range(1, 24+1))
    if args.threads:
        linestyle = "none"
        threads = args.threads

    dataroot = "/data/fig02"
    outfile = "/figures/fig02.pdf"
    if args.trial is not None:
        idx = str(args.trial).zfill(2)
        dataroot = f"/data/fig02.{idx}"
        outfile = f"/figures/fig02.{idx}.pdf"

    plot(plt, dataroot, "dpdk", threads, linestyle)
    plot(plt, dataroot, "linux", threads, linestyle)
    draw(plt, outfile)

if __name__ == "__main__":
    main()
