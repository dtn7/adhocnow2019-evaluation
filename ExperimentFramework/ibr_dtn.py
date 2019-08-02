import time

from base import Software


class IBRDTN(Software):

    def send_file(self, node_name, path, dst):
        node = self.session.get_object_by_name(node_name)
        node.cmd(
            "bash -c 'tar c {path} | dtnsend --src ibrdtn dtn://{dst}/ibrdtn'".format(**locals()))

    def wait_for_arrival(self, node_name):
        node = self.session.get_object_by_name(node_name)

        with open("{node.nodedir}/ibrdtn_run.log".format(**locals())) as log_file:

            while True:

                if self._timeout_reached():
                    print("Timeout reached. Stopping experiment.")
                    break

                line = log_file.readline()

                if not line:
                    time.sleep(0.1)
                    continue

                if "NOTICE BundleCore: Bundle received" in line:
                    break
