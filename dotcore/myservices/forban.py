import ipcalc

from core.service import CoreService, ServiceMode


class ForbanService(CoreService):
    name = "Forban"

    group = "DTN"

    dependencies = ("bwm-ng", "pidstat")

    configs = ("forban.cfg",)

    # forbanctl prints  the PIDs of the procceses, if they are running.
    # But PID:False is printed, then it is not running.
    validate = ("bash -c '\
if [ \"$(forban/bin/forbanctl status | tail -1 | cut -d\" \" -f2)\" == \"PID:False\" ]; then exit 1; else exit 0; fi'", )

    validation_mode = ServiceMode.NON_BLOCKING  # NON_BLOCKING uses the validate commands for validation.

    validation_timer = 10                       # Wait 1 second before validating service.

    validation_period = 10                      # Retry after 1 second if validation was not successful.

    shutdown = ("bash -c 'forban/bin/forbanctl stop >> forban/forban.log 2>&1'", )

    @classmethod
    def generate_config(cls, node, filename):
        destinations = []
        for netif in node._netif.values():
            for addr in netif.addrlist:
                broadcast = ipcalc.Network(addr).broadcast()
                if broadcast.version() == 4:
                    destinations.append(broadcast)

        destinations_str = ", ".join(
                ["\"{}\"".format(dest) for dest in destinations])

        return '''
[global]
name = {node_name}
version = 0.0.34

logging = INFO
loggingsizemax = 20000000

disabled_ipv6 = 1

destination = [ {destinations_str} ]

mode = opportunistic
announceinterval = 2

[forban]

[opportunistic]
filter =
maxsize = 0

[opportunistic_fs]
directory = /media
checkforban = 1
mode = out
    '''.format(node_name=node.name, destinations_str=destinations_str)

    @classmethod
    def get_startup(cls, node):
        cmds = ["cp -r /forban {nd}",
                "cp {nd}/forban.cfg {nd}/forban/cfg/",
                "{nd}/forban/bin/forbanctl start >> {nd}/forban/forban.log 2>&1"]
        cmd_line = " && ".join([c.format(nd=node.nodedir) for c in cmds])
        return ("bash -c '{cmd_line}'".format(cmd_line=cmd_line), )
