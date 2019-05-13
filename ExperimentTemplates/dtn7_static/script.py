### ENV int node_amount "How many nodes should be emulated"
### ENV int size "Size of payload to be sent in bytes"

import csv
import datetime
import json
import os
import shutil
import time
import random
import struct

from core.emulator.coreemu import CoreEmu
from core.emulator.emudata import IpPrefixes, NodeOptions
from core.enumerations import EventTypes

import framework


def prepare_log_file(input_file):
    total_file_size = os.path.getsize(input_file)

    if total_file_size > 20000000:
        too_big_file = open(input_file, 'rb')

        def get_chunk():
            return too_big_file.read(20000000)

        chunk_count = 0
        for chunk in iter(get_chunk, ''):
            chunk_path = '{}_chunk{}'.format(input_file, chunk_count)
            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(chunk)
                framework.addBinaryFile(chunk_path)
            chunk_count = chunk_count + 1

        too_big_file.close()

    else:
        framework.addBinaryFile(input_file)


def collect_logs(session_dir):
    for root, _, files in os.walk(session_dir):
        for f in files:
            src_file_path = os.path.join(root, f)

            if '.conf' not in src_file_path:
                continue

            if 'store/' in src_file_path:
                continue

            session_dir_trailing = '{}/'.format(session_dir)
            new_file_name = src_file_path.replace(session_dir_trailing,
                                                  '').replace('/', '_')
            dst_file_path = '{}/{}'.format(os.getcwd(), new_file_name)

            try:
                shutil.move(src_file_path, dst_file_path)
                prepare_log_file(new_file_name)
            except IOError:
                continue

    prepare_log_file('parameters.py')

def create_node(session, name, x=None, y=None):
    "Create a new node with an optional position"
    opts = NodeOptions(name=name, model="host")
    if x is not None and y is not None:
        opts.set_position(x, y)

    n = session.add_node(node_options=opts)

    # Override services, otherwise they won't appear on firstboot
    servs = ["DefaultRoute", "bwm-ng", "pidstat"]

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


def generate_chain(session, amount):
    "Generates a chain of pairwise connected nodes and returns the  peers and networks"
    if amount > 255:
        raise ValueError("amount must be <= 255")

    nodes = [create_node(session, "n{}".format(i), x=i*150+50, y=50)
            for i in range(amount)]
    networks = [IpPrefixes("10.0.{}.0/24".format(i)) for i in range(amount-1)]

    for i in range(amount-1):
        nodeA, nodeB = nodes[i], nodes[i+1]

        ifA = networks[i].create_interface(nodeA)
        ifB = networks[i].create_interface(nodeB)

        session.add_link(nodeA.objid, nodeB.objid,
                interface_one=ifA, interface_two=ifB)

    return (nodes, networks)


def bench(path, node_amount, interactive=False):
    # Setup CORE
    coreemu = globals().get(
            "coreemu",
            CoreEmu({"custom_services_dir": "/root/.core/myservices"}))
    session = coreemu.create_session(_id={{simInstanceId}})
    session.set_state(EventTypes.CONFIGURATION_STATE)

    # Setup Nodes
    nodes, networks = generate_chain(session, node_amount)

    session.instantiate()
    time.sleep(0.5)

    # Setup dtn7's static configuration
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

    return ((recv_time - send_time).total_seconds(), coreemu, session.session_dir)

if __name__ in ["__main__", "__builtin__"]:
    framework.start()

    random.seed({{seed}})

    with open("/dump", "wb") as f:
        for _ in range({{size}}):
            rand_int = random.randint(0, 255)
            rand_byte = struct.pack("B", rand_int)
            f.write(rand_byte)

    bench_val, coreemu, session_dir = bench("/dump", {{node_amount}})

    log_file_name = "bench_{}.csv".format(int(time.time()))

    with open(log_file_name, 'w') as log_file:
        log_file.write("{nodes},{size},{time}".format(nodes={{node_amount}},
            size={{size}}, time=bench_val))

    collect_logs(session_dir)
    framework.addBinaryFile(log_file_name)

    coreemu.shutdown()

    framework.stop()
