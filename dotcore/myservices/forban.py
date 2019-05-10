from core.service import CoreService, ServiceMode

class ForbanService(CoreService):
    name = "Forban"
    group = "Utility"
    configs = ("forban.sh", )
    startup = ("bash {} start".format(configs[0]), )
    shutdown = ("bash {} stop".format(configs[0]), )

    @classmethod
    def generate_config(cls, node, filename):
        return '''
            #!/usr/bin/env bash

            if [ "$1" == "start" ]; then
              cp -r /forban/ {node_dir}/
            fi

            {node_dir}/forban/bin/forbanctl "$1"
        '''.format(node_dir=node.nodedir)
