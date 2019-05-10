from core.service import CoreService, ServiceMode

class Dtn7Service(CoreService):
    name = "dtn7"
    group = "Utility"
    executables = ("dtn7d", "dtn7cat", )
    configs = ("dtnd.toml", )
    startup = ("bash -c 'dtn7d {} 2>&1 | tee dtnd.log'".format(configs[0]), )
    shutdown = ("pkill dtn7d", )

    @classmethod
    def generate_config(cls, node, filename):
        return '''
[core]
store = "store_{node_name}/"
inspect-all-bundles = true
node-id = "dtn://{node_name}/"

[logging]
level = "info"
report-caller = false
format = "json"

[discovery]
ipv4 = true

[simple-rest]
node = "dtn://{node_name}/"
listen = "127.0.0.1:8080"

[[listen]]
protocol = "mtcp"
endpoint = ":35037"
        '''.format(node_name=node.name)
