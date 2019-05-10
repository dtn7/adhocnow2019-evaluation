#!/usr/bin/env python3

import pandas
import matplotlib.pyplot as plt


INDEX = ["1B", "1KiB", "1MiB", "10MiB"]


def plt_line_all(df, nodes, ext):
    "Line plot for all sizes of the softwares"
    grps = df[df["nodes"] == nodes].groupby("software")

    data = {}
    for software, software_grp in grps:
        bytesize_grps = software_grp.groupby("bytesize")
        bytesize_vals = [g["seconds"].median() for _, g in bytesize_grps]

        data[software] = bytesize_vals

    df = pandas.DataFrame(data, index=INDEX)

    for ax in df.plot(subplots=True, figsize=(6, 6)):
        ax.set_xticklabels(INDEX)
        ax.plot()

    plt.xticks(range(len(INDEX)), INDEX)
    plt.savefig("plt_line_all_{}.{}".format(nodes, ext))


def plt_line_comp23(df, ext, softwares=["dtn7-static", "serval"]):
    grps = df.groupby("software")
    for software, software_grp in grps:
        if software not in softwares:
            continue

        sgrps = software_grp.groupby(["bytesize"])

        node2, node3 = [], []
        err2, err3 = [], []
        for i, grp in sgrps:
            node2.append(grp[grp["nodes"] == 2]["seconds"].median())
            node3.append(grp[grp["nodes"] == 3]["seconds"].median())
            err2.append(grp[grp["nodes"] == 2]["seconds"].std())
            err3.append(grp[grp["nodes"] == 3]["seconds"].std())

        df = pandas.DataFrame({"2 Nodes": node2, "3 Nodes": node3}, index=INDEX)
        err_df = pandas.DataFrame({"2 Nodes": err2, "3 Nodes": err3}, index=INDEX)

        fig = df.plot.bar(yerr=err_df, capsize=4).get_figure()
        fig.savefig("plt_comp23_{}.{}".format(software, ext))


def latex_table(df):
    bytesize_dict = dict(zip([1, 2**10, 2**20, 10 * 2**20], INDEX))
    data = {}

    grps = df.groupby(["software", "nodes", "bytesize"])
    for (softwares, nodes, bytesize), grp in grps:
        bytesize_human = bytesize_dict[bytesize]
        data[(softwares, nodes, bytesize_human)] = grp["seconds"].median()

    print(" & & {} \\\\\n\\hline".format(" & ".join(INDEX)))

    for software in ["dtn7-auto", "dtn7-static", "forban", "serval"]:
        opts = [(software, 2), ("", 3)] if software != "forban" else [(software, 2)]
        for text, nodes in opts:
            print("\\textit{{{text}}} & {nodes} & ".format(text=text, nodes=nodes), end="")
            for i in range(len(INDEX)):
                end = i == len(INDEX)-1
                print("{bs:.5f} s {deli} ".format(
                    bs=data[(software, nodes, INDEX[i])], deli="\\\\" if end else "&"),
                    end="\n" if end else "")


if __name__ == "__main__":
    plt.style.use("grayscale")

    f = "bench_1555447066.csv"
    df = pandas.read_csv(f)

    latex_table(df)

    ext = "pgf"  # change to "pgf" for LaTeX

    plt_line_comp23(df, ext)
    plt_line_all(df, 2, ext)
    plt_line_all(df, 3, ext)
