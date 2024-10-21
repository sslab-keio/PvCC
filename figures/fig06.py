from dep import *
import argparse

titley = -0.45
markersize=4

plotparams = {
    "pvcc": { "label": 'PvCC (tslice=100µs)', "marker": "o", "color": "darkorange", "markersize": 5 },
    "credit": { "label": 'Credit (tslice=1000µs)', "marker": "^", "color": "yellowgreen", "markersize": 5 },
    "credit2": { "label": 'Credit2 (ratelimit=0µs)', "marker": "D", "color": "forestgreen", "markersize": 4 },
}
labels = {"pvcc": 'PvCC (tslice=100µs)', "credit": 'Credit (tslice=1000µs)', "credit2": 'Credit2 (ratelimit=0µs)'}

def memcached(ax, dataroot, setup, preset_rates, linestyle):

    rates = list(range(5000, 100000, 5000))
    if preset_rates:
        rates = preset_rates

    qpss = []
    p99s = []

    for rate in rates:
        # filepath = f"{filepaths[setup]}/{preset_qps}qps"
        filepath = f"{dataroot}/memcached/{setup}/{rate}qps"
        summary = Mutilate.parse(filepath)
        qpss.append(summary.qps / 1000)
        p99s.append(summary.read_p99)
    ax.plot(qpss, p99s, **plotparams[setup], linestyle=linestyle)
    print(f"Memcached, {setup}, max throughput: {max(qpss)}")

    ax.set_xlim(0)
    ax.set_ylim(0)
    ax.set_xlabel("Throughput [K queries/sec]")
    ax.set_ylabel("99%-ile Latency [µs]")
    ax.set_title("Memcached", y=titley, fontsize=11)

def nginx(ax, dataroot, setup, preset_rates, linestyle):

    rates = list(range(2000, 50000 + 1, 2000))
    if preset_rates:
        rates = preset_rates

    rpss = []
    p99s = []
    p50s = []
    p99s_corrected = []
    p50s_corrected = []
    for rps in rates:
        summary = Wrk2.parse(f"{dataroot}/nginx/{setup}/{rps}rps")
        rpss.append(summary.throughput / 1000)
        p99s_corrected.append(summary.p99_corrected)

    ax.plot(rpss, p99s_corrected, **plotparams[setup], linestyle=linestyle)
    ax.set_ylabel("99%-ile Latency [µs]")
    print(f"Nginx, {setup}, max throughput: {max(rpss)}")

    ax.set_xlim(0)
    ax.set_xlabel("Throughput [K requests/sec]")
    ax.set_ylim((0, 6500))
    ax.set_yticks([0, 2000, 4000, 6000])
    ax.set_title("Nginx", y=titley, fontsize=11)

def redis(ax, dataroot, setup, preset_rates, linestyle):
    rpss = []
    p50s = []
    p99s = []

    rates = list(range(100, 3000 + 1, 100))
    if preset_rates:
        rates = preset_rates
    
    for preset_rate in rates:
        filepath = f"{dataroot}/redis/{setup}/{preset_rate}rps"
        summary = Memtier.parse(filepath)
        rpss.append(summary.get_rps / 1000)
        p50s.append(summary.get_p50 * 1000)
        p99s.append(summary.get_p99 * 1000)
    
    ax.plot(rpss, p99s, **plotparams[setup], linestyle=linestyle)
    print(f"Redis, {setup}, max throughput: {max(rpss)}")

    ax.set_xlim((0))
    ax.set_ylim((0, 3500))
    ax.set_xlabel("Throughput [K requests/sec]")
    ax.set_ylabel("99%-ile Latency [µs]")
    ax.set_title("Redis", y=titley, fontsize=11)


def main():
    import matplotlib.pyplot as plt

    parser = argparse.ArgumentParser()
    parser.add_argument("--workloads", type=str, nargs="*")
    parser.add_argument("--setups", type=str, nargs="*")
    parser.add_argument("--rates", type=int, nargs="*")
    parser.add_argument("--trial", type=int)
    args = parser.parse_args()

    linestyle = "-"
    rates = None
    if args.rates:
        linestyle = "none"
        rates = args.rates

    dataroot = "/data/fig06"
    outfile = "/figures/fig06.pdf"
    if args.trial is not None:
        idx = str(args.trial).zfill(2)
        dataroot = f"/data/fig06.{idx}"
        outfile = f"/figures/fig06.{idx}.pdf"

    setups = ["credit", "credit2", "pvcc"]
    if args.setups:
        setups = args.setups

    workloads = ["memcached", "nginx", "redis"]
    if args.workloads:
        workloads = args.workloads


    fig, axes = plt.subplots(1, 3, figsize=(12, 2))

    for setup in setups:
        if "memcached" in workloads:
            memcached(axes[0], dataroot, setup, rates, linestyle)
        if "nginx" in workloads:
            nginx(axes[1], dataroot, setup, rates, linestyle)
        if "redis" in workloads:
            redis(axes[2], dataroot, setup, rates, linestyle)

    axes[0].legend(loc="upper center", bbox_to_anchor=(0.5, 1.25), ncol=3, frameon=False, handlelength=0, handletextpad=0.9, fontsize=10, columnspacing=1.5)

    plt.subplots_adjust(wspace=0.3)
    plt.savefig(outfile, bbox_inches="tight")

if __name__ == "__main__":
    main()
