from dep import *
import sys

y_prefix = 1000

plotparams = {
    "pvcc_100": { "label": "PvCC", "color": "darkorange" },
    "pin_1000": { "label": "Pin", "color": "royalblue", },
    "naive_1000": { "label": "Naive", "color": "turquoise", },
}

time = 50

def run(plt, dataroot, outfile):
    plt.rcParams.update(plt.rcParamsDefault | {
        "font.size": 10,
        "figure.figsize": [4.8, 3.0],
        "legend.fontsize": 10,
        "lines.markersize": 5,
        "axes.titlesize": 10,
        "figure.titlesize": 10,
    })

    for (setup, label, filepath) in [
        ('pvcc_100', "PvCC", f"{dataroot}/pvcc/sysbench"),
        ('pin_1000', "Pin", f"{dataroot}/pin/sysbench"),
        ('naive_1000', "Naive", f"{dataroot}/naive/sysbench"),
    ]:
        data = get_data_of_sb(filepath)
        rep = data["report"].loc[30:]
        start_sec = rep.index[0]
        end_sec = rep.index[-1]
        xs = list(map(lambda x: x - start_sec, rep.index.to_numpy()))
        # xs = rep.index.to_numpy()
        ys = np.array(rep["throughput"]) / y_prefix
        plt.plot(xs, ys, **plotparams[setup])

    plt.legend(**(params_legend_upper_center | { "ncol": 3, "handlelength": 1.5, }))
        
    plt.xlabel('Time [s]')
    plt.ylabel('Sysbench Throughput [K events/sec]')
    plt.ylim([0, 16000 / y_prefix])
    plt.savefig(outfile, bbox_inches="tight")

def main():
    import matplotlib.pyplot as plt
    run(plt, "/data/fig11", "/figures/fig11c.pdf")

if __name__ == "__main__":
    main()
