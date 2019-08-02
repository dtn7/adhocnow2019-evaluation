from core.service import CoreService
from core.service import ServiceMode

import nacl.hash
from nacl.encoding import HexEncoder
from nacl.bindings import crypto_sign_seed_keypair, crypto_sign_ed25519_sk_to_curve25519, crypto_scalarmult_base

sevald_keyring_dump_format_legacy = '''0: type=4(DID)  DID="{did}" Name="{name}"
0: type=1(CRYPTOBOX)  pub={box_pk} sec={box_sk}
0: type=2(CRYPTOSIGN)  pub={sign_pk} sec={sign_sk}
0: type=3(RHIZOME)  sec={rhiz_pk}
'''

servald_keyring_dump_format = '''0: type=0x04(DID)  DID="{did}" Name="{name}"
0: type=0x06 (CRYPTOCOMBINED)  pub={sign_pk}{box_pk} sec={sign_sk}{box_sk}
0: type=0x03(RHIZOME)  sec={rhiz_pk}
'''


def generate_serval_keys(name):
    node_hash = HexEncoder.decode(nacl.hash.sha256(name.encode("utf-8")))
    sign_pk, sign_sk = crypto_sign_seed_keypair(node_hash)
    box_sk = crypto_sign_ed25519_sk_to_curve25519(sign_sk)
    box_pk = crypto_scalarmult_base(box_sk)

    rhiz_pk = HexEncoder.decode(
        nacl.hash.sha256(("rhizome"+name).encode("utf-8")))

    keys = {
        "sign_pk": HexEncoder.encode(sign_pk).decode("ascii").upper(),
        "box_sk":  HexEncoder.encode(box_sk).decode("ascii").upper(),
        "sign_sk": HexEncoder.encode(sign_sk).decode("ascii").upper(),
        "box_pk":  HexEncoder.encode(box_pk).decode("ascii").upper(),
        "sid":     HexEncoder.encode(box_pk).decode("ascii").upper(),
        "rhiz_pk": HexEncoder.encode(rhiz_pk).decode("ascii").upper(),
    }
    return keys


def generate_serval_keyring_dump(name):
    keys = generate_serval_keys(name)
    keys["did"] = "".join(c for c in name if c.isdigit()).rjust(5, "0")
    keys["name"] = name

    return sevald_keyring_dump_format_legacy.format(**keys)


class ServalService(CoreService):
    name = "Serval"

    group = "DTN"

    executables = ('servald', )

    dependencies = ("bwm-ng", "pidstat")

    configs = ('serval.conf', 'keyring.dump', 'serval.sid')

    startup = (
        'bash -c "servald keyring load keyring.dump; nohup servald start foreground > serval_run.log 2>&1 &"', )

    validate = ('bash -c "servald status"', )   # ps -C returns 0 if the process is found, 1 if not.

    validation_mode = ServiceMode.NON_BLOCKING  # NON_BLOCKING uses the validate commands for validation.

    validation_timer = 5                        # Wait 1 second before validating service.

    validation_period = 5                       # Retry after 1 second if validation was not successful.

    shutdown = ('bash -c "servald stop"', )

    @classmethod
    def generate_config(cls, node, filename):
        ''' Return a string that will be written to filename, or sent to the
            GUI for user customization.
        '''
        if filename == "serval.conf":
            return '''interfaces.0.match=*
interfaces.0.type=ethernet
server.motd="{}"
api.restful.users.pyserval.password=pyserval
rhizome.advertise.interval=2000
'''.format(node.name)

        if filename == "keyring.dump":
            return generate_serval_keyring_dump(node.name)

        if filename == "serval.sid":
            return generate_serval_keys(node.name)["sid"]
