from collections import defaultdict
from json import load, dump, dumps
from os.path import join as pjoin, exists
from os import access, R_OK, environ, makedirs


class ConfigAgent():

    def __init__(self):

        home = environ.get('HOME')
        config_path = pjoin(home, '.config/salty_wpa/')
        self.config_file = pjoin(config_path, 'config')
        self.skip_encrypt = ['salt']

        if not exists(config_path):
            makedirs(config_path)

        if access(self.config_file, R_OK):

            self._read_config_file(self.config_file)

        else:
            self.config = defaultdict(str)

    def get(self, name, args):

        if name in self.config:
            return self.config[name].get(args, False)

    def set(self, name, key, value):

        if name not in self.config:
            self.config[name] = {}

        self.config[name][key] = value

    def delete_network(self, ssid):

        if ssid in self.config:
            self.config.pop(ssid)

    def decrypt_config_items(self, crypto):

        for item in self.config:
            for key in self.config[item].keys():

                if key not in self.skip_encrypt:
                    value = self.config[item][key]
                    self.config[item][key] = crypto.decrypt_value(
                                    value
                                ).decode('utf-8')

    def encrypt_config_items(self, crypto):

        for item in self.config:
            for key in self.config[item].keys():

                if key not in self.skip_encrypt:
                    value = self.config[item][key]
                    self.config[item][key] = crypto.encrypt_value(
                                    value
                                ).decode('utf-8')

    def return_saved_networks(self):

        available = set()

        for item in self.config:

            if item != 'settings':
                available.add(item)

        return available

    def write_config(self):

        with open(self.config_file, 'w+') as fd:
            dump(self.config, fd)

    def _read_config_file(self, config):

        with open(self.config_file) as fd:
            self.config = load(fd)

    def __str__(self):

        return dumps(self.config)
