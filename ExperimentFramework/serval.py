import time

from base import Software


class Serval(Software):

    def send_file(self, node_name, path, dst):
        node = self.session.get_object_by_name(node_name)
        node.cmd(
            "bash -c 'servald rhizome add file `cat serval.sid` {path}'".format(**locals()))

    def wait_for_arrival(self, node_name):
        node = self.session.get_object_by_name(node_name)

        with open("{node.nodedir}/serval.log".format(**locals())) as log_file:

            while True:

                if self._timeout_reached():
                    print("Timeout reached. Stopping experiment.")
                    break

                line = log_file.readline()

                if not line:
                    time.sleep(0.1)
                    continue

                if "rhizome_database.c:1363:rhizome_store_manifest()  RHIZOME ADD MANIFEST service=file bid=" in line:
                    break
