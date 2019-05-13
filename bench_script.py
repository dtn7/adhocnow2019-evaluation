#!/usr/bin/env python2

import csv
import datetime
import json
import os
import shutil
import time

from core.emulator.coreemu import CoreEmu
from core.emulator.emudata import IpPrefixes, NodeOptions
from core.enumerations import EventTypes


class Software:
    "Software is an eNuMeRaTiOn"
    DTN7_STATIC = 0
    DTN7_AUTO = 1
    FORBAN = 2
    SERVAL = 3

    @staticmethod
    def str(software):
        if software == Software.DTN7_STATIC:
            return "dtn7-static"
        elif software == Software.DTN7_AUTO:
            return "dtn7-auto"
        elif software == Software.FORBAN:
            return "forban"
        elif software == Software.SERVAL:
            return "serval"


def create_node(session, name, x=None, y=None, software=Software.DTN7_STATIC):
    "Create a new node with an optional position"
    opts = NodeOptions(name=name, model="host")
    if x is not None and y is not None:
        opts.set_position(x, y)

    n = session.add_node(node_options=opts)

    # Override services, otherwise they won't appear on firstboot
    servs = ["DefaultRoute"]
    if software == Software.DTN7_AUTO:
        servs.append("dtn7")
    elif software == Software.FORBAN:
        servs.append("Forban")
    elif software == Software.SERVAL:
        servs.append("Serval")

    n.services = []
    session.services.add_services(n, n.type, servs)

    return n


def dtn7_config(node_name, peers):
    "Returns a static dtn7-configuration for a node; peers is a list of (name, IP)."
    peer_conf = lambda (name, ip): '''
[[peer]]
node = "dtn://{name}/"
protocol = "mtcp"
endpoint = "{ip}:35037"
    '''.format(name=name, ip=ip)

    return '''
[core]
store = "store/"
inspect-all-bundles = true
node-id = "dtn://{node_name}/"

[logging]
level = "info"
format = "json"

[simple-rest]
node = "dtn://{node_name}/"
listen = "127.0.0.1:8080"

[[listen]]
protocol = "mtcp"
endpoint = ":35037"

{peer_conf}
    '''.format(
            node_name=node_name,
            peer_conf="\n".join([peer_conf(p) for p in peers]))


def serval_rhizome_time(node):
    "Returns the time of the rhizome bundle."
    _, rh_output = node.cmd_output(
            "bash -c 'SERVALINSTANCE_PATH={} servald rhizome list'".format(node.nodedir))
    # it starts with a line just saying 13..
    rh_csv = csv.DictReader(rh_output.split("\n")[1:], delimiter=':')
    for row in rh_csv:
        try:
            return float(row[".inserttime"])
        except:
            return None

    return None


def generate_chain(session, amount, software):
    "Generates a chain of pairwise connected nodes and returns the  peers and networks"
    if amount > 255:
        raise ValueError("amount must be <= 255")

    nodes = [create_node(session, "n{}".format(i), x=i*150+50, y=50, software=software)
            for i in range(amount)]
    networks = [IpPrefixes("10.0.{}.0/24".format(i)) for i in range(amount-1)]

    for i in range(amount-1):
        nodeA, nodeB = nodes[i], nodes[i+1]

        ifA = networks[i].create_interface(nodeA)
        ifB = networks[i].create_interface(nodeB)

        session.add_link(nodeA.objid, nodeB.objid,
                interface_one=ifA, interface_two=ifB)

    return (nodes, networks)


def bench(path, node_amount, software, interactive=False):
    # Setup CORE
    coreemu = globals().get(
            "coreemu",
            CoreEmu({"custom_services_dir": "/root/.core/myservices"}))
    session = coreemu.create_session()
    session.set_state(EventTypes.CONFIGURATION_STATE)

    # Setup Nodes
    nodes, networks = generate_chain(session, node_amount, software)

    session.instantiate()
    time.sleep(0.5)

    # Setup dtn7's static configuration
    if software == Software.DTN7_STATIC:
        # Create config
        for i in range(len(nodes)):
            node = nodes[i]

            neighbors = []
            if i != 0:
                neighbors.append(
                        ("n{}".format(i-1), networks[i-1].ip4_address(nodes[i-1])))
            if i != len(nodes)-1:
                neighbors.append(
                        ("n{}".format(i+1), networks[i].ip4_address(nodes[i+1])))

            with open("{}/dtnd.toml".format(node.nodedir), "w") as f:
                f.write(dtn7_config("n{}".format(i), neighbors))

        # Fire up
        for node in nodes:
            node.cmd("bash -c 'dtn7d dtnd.toml 2>&1 | tee dtnd.log'", wait=False)

        # Wait for neighbors
        for i in range(len(nodes)):
            while True:
                logfile = "{}/dtnd.log".format(nodes[i].nodedir)

                while not os.path.isfile(logfile):
                    time.sleep(0.1)

                with open(logfile) as f:
                    n_log = f.readlines()

                # each member within the chain has two neighbors
                # the peripheral devices have only one neighbor
                # plus one for the node's own CLA
                target = (1 if i == 0 or i == len(nodes)-1 else 2) + 1

                try:
                    for line in n_log:
                        json_obj = json.loads(line)
                        if json_obj["msg"] == "Started and registered CLA":
                            target = target - 1
                except:
                    pass

                if target == 0:
                    break

                time.sleep(0.1)

    # Benchmark code will follow; stopping here in the interactive mode
    if interactive:
        return None

    if software in [Software.DTN7_STATIC, Software.DTN7_AUTO]:
        nodes[0].cmd("bash -c 'cat {path} | dtn7cat send \"http://127.0.0.1:8080\" \"dtn://n{dest}/\"'".format(
            path=path, dest=len(nodes)-1))

        time.sleep(1)

        with open("{}/dtnd.log".format(nodes[0].nodedir)) as f:
            n0_log = f.readlines()

        for line in n0_log:
            json_obj = json.loads(line)
            if json_obj["msg"] == "Transmission of bundle requested":
                send_time = datetime.datetime.strptime(
                        json_obj["time"][:-4], "%Y-%m-%dT%H:%M:%S.%f")

        flag = False
        while not flag:
            with open("{}/dtnd.log".format(nodes[-1].nodedir)) as f:
                n1_log = f.readlines()

            try:
                for line in n1_log:
                    json_obj = json.loads(line)
                    if json_obj["msg"] == "Received bundle for local delivery":
                        recv_time = datetime.datetime.strptime(
                                json_obj["time"][:-4], "%Y-%m-%dT%H:%M:%S.%f")
                        flag = True
                        break
            except:
                pass

            time.sleep(0.1)

        coreemu.shutdown()

        return (recv_time - send_time).total_seconds()
    elif software == Software.FORBAN:
        n0_file = '{}/forban/var/share/test'.format(nodes[0].nodedir)
        n1_file = '{}/forban/var/share/test'.format(nodes[-1].nodedir)

        shutil.copyfile(path, n0_file)

        while not os.path.isfile(n1_file):
            time.sleep(1)

        n0_mtime = os.stat(n0_file).st_mtime
        n1_mtime = os.stat(n1_file).st_mtime

        coreemu.shutdown()

        return n1_mtime - n0_mtime
    elif software == Software.SERVAL:
        nodes[0].cmd("rhizome put {path}".format(path=path))
        time.sleep(0.2)

        while True:
            n0_time = serval_rhizome_time(nodes[0])
            if n0_time is not None:
                break
            time.sleep(0.1)

        while True:
            n1_time = serval_rhizome_time(nodes[-1])
            if n1_time is not None:
                break
            time.sleep(0.1)

        coreemu.shutdown()

        return (n1_time - n0_time) / 1000.0


def bench_run(software, node_amounts, sizes, n):
    for node_amount in node_amounts:
        for size in sizes:
            # Create dummy file
            with open("/dump", "wb") as f:
                f.seek(size-1)
                f.write(b"\0")

            for i in range(n):
                bench_val = bench("/dump", node_amount, software)
                if bench_val is not None:
                    print("{software},{nodes},{size},{time}".format(
                        software=Software.str(software), nodes=node_amount,
                        size=size, time=bench_val))


if __name__ in ["__main__", "__builtin__"]:
    # Interactive = True just creates the nodes; can be used inside the GUI
    interactive = False

    # For a non-interactive mode, specify the amount of runs
    n = 50

    if not interactive:
        print("software,nodes,bytesize,seconds")

        bench_run(
                software=Software.DTN7_STATIC,
                node_amounts=[2, 3],
                sizes=[1, 1024, 1024*1024, 10*1024*1024],
                n=n)

        bench_run(
                software=Software.DTN7_AUTO,
                node_amounts=[2, 3],
                sizes=[1, 1024, 1024*1024, 10*1024*1024],
                n=n)

        bench_run(
                software=Software.FORBAN,
                node_amounts=[2],  # Fails with >= 3 nodes :^)
                sizes=[1, 1024, 1024*1024, 10*1024*1024],
                n=n)

        bench_run(
                software=Software.SERVAL,
                node_amounts=[2, 3],
                sizes=[1, 1024, 1024*1024, 10*1024*1024],
                n=n)
    else:
        bench(None, 2, Software.DTN7_AUTO, interactive=True)
