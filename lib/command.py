
from cmd import Cmd
from os import listdir
from sys import stderr, exit
from getpass import getpass

from lib.config import ConfigAgent
from lib.cryptoagent import CryptoAgent
from lib.util import print_color, colored_string


class Command(Cmd):

    intro = 'Salty WPA CLI v0.1\n'
    intro += 'Type ? or help to list command.\n'
    prompt = '> '

    def __init__(self, wpa_sock, **kwargs):

        super().__init__(**kwargs)

        self.wpa_sock = wpa_sock
        self.config = ConfigAgent()
        self.crypto = CryptoAgent(getpass('passphrase: '),
                                  self.config)

        self.available = self.config.return_saved_networks()

    def _print_error(self, msg):
        msg = colored_string('red', msg)
        print(msg, file=stderr)

    def default(self, line):

        args = line.split()
        args[0] = args[0].upper()

        result = self.wpa_sock.execute_command(' '.join(args))

        print(result)

    def do_exit(self, arg):

        self.wpa_sock.remove_all_networks()
        self.wpa_sock.close_interface()
        exit(0)

    def do_save(self, arg):
        self.config.write_config()

    def do_interface(self, arg):
        """Select different interface from /var/run/wpa_supplicant/"""

        self.wpa_sock.select_interface(arg)

    def complete_interface(self, text, line, begidx, endidx):

        completion = listdir('/var/run/wpa_supplicant')

        if text:
            completion = [c for c in completion if c.startswith(text)]

        return completion

    def do_list_networks(self, arg):
        """List networks that are registered with wpa_supplicant"""

        retval = self.wpa_sock.execute_command('LIST_NETWORKS')

        print(retval)

    def do_scan(self, args):
        """Let wpa_supplicant scan for available networks and print
           scan_result"""

        self.wpa_sock.execute_scan_command()

    def do_auto(self, arg):

        available = set()
        closest = -100

        for ssid, hashed_ssid, signal in self.wpa_sock.retrieve_all_networks(
                                        self.crypto
                                    ):

            if hashed_ssid in self.available:

                if signal > closest:
                    closest = signal

                available.add((ssid, hashed_ssid, signal))

        for ssid, hashed_ssid, signal in available:

            if signal == closest:
                key_mgmt_enc = self.config.get(hashed_ssid, 'key_mgmt')
                psk_enc = self.config.get(hashed_ssid, 'psk')

                psk = self.crypto.decrypt_value(
                             psk_enc
                        ) if psk_enc else False
                key_mgmt = self.crypto.decrypt_value(
                                 key_mgmt_enc
                            ) if key_mgmt_enc else False

                n = self.wpa_sock.add_network_interactive(ssid,
                                                          key_mgmt, psk)
                print_color('green',
                            f"network available! connecting to {ssid}..."
                            )

                self.wpa_sock.execute_connect_command(n)

    def do_connect(self, arg):

        if not arg.isdigit():
            self._print_error('please supply a valid number')

        self.wpa_sock.execute_connect_command(arg)

    def do_disconnect(self, arg):

        self.wpa_sock.execute_disconnect_command()

    def do_remove_network(self, arg):
        """Delete network n from wpa_supplicant"""

        if not arg.isdigit():
            self._print_error('please supply a valid number')

            return

        network_name = self.wpa_sock.execute_command(f"GET_NETWORK {arg} ssid")
        network_name = network_name.replace('"', '')

        retval = self.wpa_sock.execute_command(f"REMOVE_NETWORK {arg}")

        self.config.delete_network(self.crypto.hash_value(network_name))

        print(retval)

    def do_add_network(self, arg):

        ssid = input('ssid: ')
        hashed_ssid = self.crypto.hash_value(ssid)

        if not ssid:
            self._print_error('please specify a valid SSID')

            return

        if arg == 'open':
            key_mgmt = 'NONE'
            self.config.set(hashed_ssid, 'key_mgmt',
                            self.crypto.encrypt_value(key_mgmt)
                            )
            psk = False

        else:
            key_mgmt = False
            psk = getpass('psk: ')
            self.config.set(hashed_ssid, 'psk',
                            self.crypto.encrypt_value(psk)
                            )

        if not psk and not key_mgmt:
            self._print_error('not key_mgmt nor psk specified')

            return

        self.wpa_sock.add_network_interactive(ssid, key_mgmt, psk)

    def do_set_network(self, args):
        """Execute SET_NETWORK command on wpa_supplicant"""

        if not self._is_valid_set_network_argument(args):
            return

        retval = self.wpa_sock.execute_command(f"SET_NETWORK {args}")

        print(retval)

    def _is_valid_set_network_argument(self, args):
        """Validate SET_NETWORK argument syntax"""

        if '"' in args:
            args = self._split_quoted_args(args)

        else:
            args = args.split()

        valid_args = ['ssid', 'psk', 'key_mgmt', 'identity', 'password']

        if not len(args) == 3:
            self._print_error('SET_NETWORK n key value')

            return False

        if not args[0].isdigit():
            self._print_error('please supply a valid network number')

            return False

        if args[1] not in valid_args:
            self._print_error(f"{args[1]} is not a valid argument")

            return False

        return True

    def _split_quoted_args(self, args):

        args = args.split('"')
        quoted = args[1]

        # add quoted args to the regular args
        args = args[0].split()
        args.append(quoted)

        return args
