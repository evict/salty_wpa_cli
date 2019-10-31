# Salty wpa_cli

The goal is to write a `wpa_cli` application or interface that supports encryption of
`wpa_supplicant` configuration files. By default `wpa_supplicant` stores network information in
clear text, which may not be desirable in certain situations.

This interface would work for people using `wpa_cli` to connect to wireless networks.

Currently it supports OPEN networks and general WPA2 encrypted networks. More complex network configurations will be supported soon.

## Usage

```
usage: main.py [-h] [-i INTERFACE] [-c CTRL]

optional arguments:
  -h, --help            show this help message and exit
  -i INTERFACE, --interface INTERFACE
                        interface to use
  -c CTRL, --control-interface CTRL
                        path to control interface
```

By default it looks in `/var/run/wpa_supplicant` and gets the second interface.

```
(master) -> ./main.py                                                          INSERT
Selected interface 'wlp2s0'
passphrase:
Salty WPA CLI v0.1
Type ? or help to list command.

> ?

Documented commands (type help <topic>):
========================================
help  interface  list_networks  remove_network  scan  set_network

Undocumented commands:
======================
add_network  auto  connect  disconnect  exit  save

>
```

By default any undefined command, such as `status`, will be send directly to the `wpa_supplicant` daemon:

```
> status
<3>CTRL-EVENT-SCAN-STARTED
<3>CTRL-EVENT-REGDOM-CHANGE init=BEACON_HINT type=UNKNOWN
<3>CTRL-EVENT-SCAN-RESULTS
<3>CTRL-EVENT-SCAN-STARTED
<3>CTRL-EVENT-SCAN-RESULTS
bssid=[a_mac]
freq=5180
ssid=Example Network
id=0
mode=station
wifi_generation=5
pairwise_cipher=CCMP
group_cipher=CCMP
key_mgmt=WPA2-PSK
wpa_state=COMPLETED
ip_address=192.168.1.2
p2p_device_address=[a_mac]
address=[a_mac]
uuid=[uuid]
ieee80211ac=1

```

Encrypted configurations are stored in `${HOME}/.config/salty_wpa/config`
