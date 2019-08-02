import subprocess
import os
import ipcalc

from core.service import CoreService, ServiceMode


class IbrDtnService(CoreService):
    name = "IBRDTN"

    group = "DTN"

    executables = ("dtnd", "dtnsend")

    dependencies = ("bwm-ng", "pidstat")

    dirs = ("/ibrdtn_inbox", )

    configs = ('ibrdtn.conf', )

    startup = ("bash -c '\
dtnd -c ibrdtn.conf -D; sleep 2; pkill -INT dtnd; nohup dtnd -v --timestamp -c ibrdtn.conf > ibrdtn_run.log 2>&1 &\
'", )

    validate = ('bash -c "ps -C dtnd"', )       # ps -C returns 0 if the process is found, 1 if not.

    validation_mode = ServiceMode.NON_BLOCKING  # NON_BLOCKING uses the validate commands for validation.

    validation_timer = 1                        # Wait 1 second before validating service.

    validation_period = 1                       # Retry after 1 second if validation was not successful.

    shutdown = ("bash -c 'pkill -INT dtnd'", )

    @classmethod
    def generate_config(cls, node, filename):
        cfg = '''storage_path = /ibrdtn_inbox
discovery_address = 224.0.0.142
discovery_interval = 2
routing = epidemic
routing_forwarding = yes
net_autoconnect = 10
net_interfaces = '''

        iface_config_template = '''
net_lan{index}_type = tcp
net_lan{index}_interface = {netif.name}
net_lan{index}_port = 4556
'''

        for index in range(node.numnetif()):
            cfg += "lan{} ".format(index)

        for index, netif in node._netif.iteritems():
            cfg += iface_config_template.format(**locals())

        return cfg
