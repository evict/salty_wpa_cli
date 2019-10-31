#!/usr/bin/env python3
from argparse import ArgumentParser

from lib.wpasock import WPASock
from lib.command import Command


def main():

    parser = ArgumentParser()

    parser.add_argument('-i', '--interface', help='interface to use',
                        dest='interface')
    parser.add_argument('-c', '--control-interface',
                        help='path to control interface',
                        dest='ctrl', default='/var/run/wpa_supplicant')

    args = parser.parse_args()

    wpa_sock = WPASock(args)

    cmd = Command(wpa_sock)
    cmd.cmdloop()


if __name__ == '__main__':
    main()
