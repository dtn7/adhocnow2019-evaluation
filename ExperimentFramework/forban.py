import json
import time

from base import Software


class Forban(Software):

    def send_file(self, node_name, path, dst):
        node = self.session.get_object_by_name(node_name)
        with open("{node.nodedir}/forban_insert.log".format(**locals()), "a") as insert_log:
            timestamp = time.time()
            insert_log.write("{node_name},{timestamp},{path},{dst}".format(**locals()))

        node.cmd(
            "bash -c 'cp {path} forban/var/share/'".format(**locals()))

    def wait_for_arrival(self, node_name):
        node = self.session.get_object_by_name(node_name)

        with open("{node.nodedir}/forban/var/log/forban_opportunistic.log".format(**locals())) as log_file:

            while True:

                if self._timeout_reached():
                    print("Timeout reached. Stopping experiment.")
                    break

                line = log_file.readline()

                if not line:
                    time.sleep(0.1)
                    continue

                if "saved local file" in line:
                    break
