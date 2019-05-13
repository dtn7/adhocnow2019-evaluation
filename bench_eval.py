#!/usr/bin/env python3

import pandas
import matplotlib.pyplot as plt


INDEX = ["1B", "1KiB", "1MiB", "10MiB"]


def plt_line_all(df, nodes, ext):
    "Line plot for all sizes of the softwares"
    grps = df[df["nodes"] == nodes].groupby("software")

    data_mdns, data_errs = {}, {}
    for software, software_grp in grps:
        bytesize_grps = software_grp.groupby("bytesize")
        bytesize_vals = [g["seconds"] for _, g in bytesize_grps]

        bytesize_mdns = [x.median() for x in bytesize_vals]
        bytesize_errs = [x.std() for x in bytesize_vals]

        data_mdns[software] = bytesize_mdns
        data_errs[software] = bytesize_errs

    df_mdns = pandas.DataFrame(data_mdns, index=INDEX)
    df_errs = pandas.DataFrame(data_errs, index=INDEX)

    for ax in df_mdns.plot(subplots=True, yerr=df_errs, capsize=3):
        ax.set_xticklabels(INDEX)
        ax.plot()

    plt.xticks(range(len(INDEX)), INDEX)
    plt.savefig("plt_line_all_{}.{}".format(nodes, ext))


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

    f = "bench_1.csv"
    df = pandas.read_csv(f)

    # latex_table(df)

    ext = "png"  # change to "pgf" for LaTeX

    # plt_line_comp23(df, ext)
    for node_no in [2, 10, 50, 100]:
        plt_line_all(df, node_no, ext)
