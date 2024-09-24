import fig11a
import fig11b
import fig11c
import argparse
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument("--trial", type=int)
args = parser.parse_args()

dataroot = "/data/fig11"
supplement = ""
if args.trial is not None:
    supplement = f".{str(args.trial).zfill(2)}"
    dataroot = f"/data/fig11{supplement}"

fig11a.run(plt, dataroot, f"/figures/fig11a{supplement}.pdf")
plt.clf()
fig11b.run(plt, dataroot, f"/figures/fig11b{supplement}.pdf")
plt.clf()
fig11c.run(plt, dataroot, f"/figures/fig11c{supplement}.pdf")

