from core.service import CoreService, ServiceMode


class ServalService(CoreService):
    name = "Serval"
    group = "Utility"
    executables = ("servald", "start_serval", )
    configs = ("servald_start.sh", )
    startup = ("bash {}".format(configs[0]), )
    validation_mode = ServiceMode.BLOCKING
    shutdown = ("servald stop", )

    @classmethod
    def generate_config(cls, node, filename):
        return '''
#!/usr/bin/env bash
cd {node_dir}
start_serval
        '''.format(node_dir=node.nodedir)
