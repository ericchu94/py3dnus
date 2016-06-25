#!/usr/bin/env python3

import argparse
import binascii
import math
import os
import shutil
import subprocess
import sys
import urllib.request


CDN = 'http://nus.cdn.c.shop.nintendowifi.net/ccs/download'
MAX_SPOOF_VERSION = int(math.pow(2, 16)) - 1


def download(url, path):
    with urllib.request.urlopen(url) as res, open(path, 'wb') as dest:
        shutil.copyfileobj(res, dest)


def fetch(base_url, directory, version, spoof):
    os.makedirs(directory, exist_ok=True)

    tmd_tmp = os.path.join(directory, 'tmd')
    tmd_url = '{}/tmd.{}'.format(base_url, version)
    download(tmd_url, tmd_tmp)

    cetk_tmp = os.path.join(directory, 'cetk')
    cetk_url = '{}/cetk'.format(base_url, version)
    download(cetk_url, cetk_tmp)

    with open(tmd_tmp, 'rb') as tmd:
        tmd.seek(518)
        buf = tmd.read(2)
        num_contents = int.from_bytes(buf, 'big')

        for i in range(num_contents):
            offset = 2820 + 48 * i
            tmd.seek(offset)
            buf = tmd.read(4)
            content_id = str(binascii.hexlify(buf), 'ascii')

            content_tmp = os.path.join(directory, content_id)
            content_url = '{}/{}'.format(base_url, content_id)
            download(content_url, content_tmp)

        if spoof:
            buf = int.to_bytes(spoof, 'big')
            tmd.Seek(476)
            tmd.write(buf)


def make(directory, name):
    subprocess.run(
        ['make_cdn_cia', directory, name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def py3dnus(title, version, spoof):
    if spoof and spoof > MAX_SPOOF_VERSION:
        raise OverflowError('Spoof must be less than {}'.format(MAX_SPOOF_VERSION))

    base_url = '{}/{}'.format(CDN, title)
    directory = os.path.join('tmp', title, str(version))
    name = title + '.cia'

    fetch(base_url, directory, version, spoof)
    make(directory, name)

    return name


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('title')
    parser.add_argument('version', type=int)
    parser.add_argument('--spoof', '-s', type=int)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    name = py3dnus(args.title, args.version, args.spoof)
    print('Created {}'.format(name))
