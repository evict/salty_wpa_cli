import select
from os import getpid, unlink, access, R_OK, listdir
from socket import socket, AF_UNIX, SOCK_DGRAM

from lib.util import print_color, colored_string


class WPASock():
    """Class for communication with the wpa_supplicant ctrl_interface"""

    def __init__(self, args):

        if args.ctrl:
            path = args.ctrl

        else:
            # requests will be made to this socket
            path = "/var/run/wpa_supplicant"

        if args.interface:
            interface = args.interface

        else:
            # we pick the last one, because the first one is probably p2p-dev-*
            interface = listdir(path)[-1]

        self.sock = socket(AF_UNIX, SOCK_DGRAM)
        self.sock.settimeout(3)

        # response will be written to this socket
        self.recv_sock = f"/tmp/wpa_ctrl_{getpid()}"
        self.sock.bind(self.recv_sock)

        if not access(path, R_OK):
            raise FileNotFoundError(f"{path} not found / readable")

        ctrl_interface = f"{path}/{interface}"

        if not access(ctrl_interface, R_OK):
            raise FileNotFoundError(f"{ctrl_interface} not found / readable")

        self.sock.connect(ctrl_interface)

        interface = colored_string('underlined', interface)
        print(f"Selected interface '{interface}'")

        # attach to wpa_supplicant
        self.sock.send(b'ATTACH')

        if self.sock.recv(3) != b'OK\n':
            raise OSError(f"error attaching to {ctrl_interface}")

    def _recvall(self, timeout):
        """Use poll() to receive all content from the socket, until timeout"""

        poll = select.poll()
        poll.register(self.sock, select.POLLIN)

        data = []

        while poll.poll(timeout):
            result = self.sock.recv(4096)

            if result:
                data.append(result)

        return data

    def add_network_interactive(self, ssid, key_mgmt, psk):
        """Add a network using the ADD_NETWORK and SET_NETWORK commands"""

        self.sock.send(bytes("ADD_NETWORK", 'utf-8'))

        n = self.sock.recv(10).rstrip(b'\n')

        if not n.isdigit():
            raise ValueError('add_network did not return a digit')

        self.execute_command(f'SET_NETWORK {n} ssid "{ssid}"')

        if key_mgmt:
            self.execute_command(
                       f"SET_NETWORK {n} key_mgmt {key_mgmt}"
                    )

        if psk:
            self.execute_command(f'SET_NETWORK {n} psk "{psk}"')

        return n

    def remove_all_networks(self):
        """Delete all networks we are not using"""

        networks = self.execute_command("LIST_NETWORKS")

        for line in networks.split('\n'):

            if line and '[CURRENT]' not in line:
                n = line.split()[0]

                if n.isdigit():
                    self.execute_command(f"REMOVE_NETWORK {n}")

    def retrieve_all_networks(self, crypto):
        """Retrieve and parse all networks from SCAN_RESULTS"""

        self.sock.send(bytes("SCAN", 'utf-8'))
        self._recvall(5000)

        self.sock.send(bytes("SCAN_RESULTS", 'utf-8'))

        data = self._recvall(250)[0]

        ssids = set()

        for line in data.split(b'\n')[1::]:

            if line:
                line = line.decode('utf-8')

                bssid, frequency, signal, flags, ssid = line.split('\t')
                ssids.add((ssid, crypto.hash_value(ssid), int(signal)))

        return ssids

    def close_interface(self):
        """Close the interface and unlink the socket we created"""

        self.sock.close()
        unlink(self.recv_sock)

    def select_interface(self, interface):
        """Close the current interface, and initialize with the newly
           chosen one"""

        self.close_interface()
        self.__init__(interface)

    def execute_command(self, command, timeout=500):

        self.sock.send(bytes(command, 'utf-8'))
        result = self._recvall(timeout)

        return '\n'.join([r.decode('utf-8') for r in result])

    def execute_scan_command(self):
        """Execute the SCAN command."""

        done = b'<3>CTRL-EVENT-SCAN-RESULTS '

        self.sock.send(bytes("SCAN", 'utf-8'))

        data = self._recvall(5000)

        if done in data:
            self.sock.send(bytes("SCAN_RESULTS", 'utf-8'))

            for line in self._recvall(200):
                print(line.decode('utf-8'))

    def execute_connect_command(self, number):
        """Connect to specified network number"""

        done = b'<3>CTRL-EVENT-SUBNET-STATUS-UPDATE status=0'

        self.sock.send(bytes(f"SELECT_NETWORK {number}", 'utf-8'))

        if self._wait_for_string_recv(done, 2500):
            print_color('bold_green', 'connected to network')

    def execute_disconnect_command(self):
        """Disconnect from the current network"""

        done = b'<3>CTRL-EVENT-DISCONNECTED'

        self.sock.send(bytes('DISCONNECT', 'utf-8'))

        data = self._recvall(250)

        if [d for d in data if done in d]:
            print_color('bold_red', 'disconnected from network')

    def _wait_for_string_recv(self, done, timeout=250):
        """Receive all information from socket and check if string in done
           is contained within the results"""

        data = self._recvall(timeout)

        if done in data:
            return True
