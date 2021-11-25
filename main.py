#!/usr/bin/env python3
import base64
import zlib
import json
import sys
import zlib
import argparse

from PIL import Image
from pyzbar.pyzbar import decode


def pad_base64(data):
    """Make sure base64 data is padded correctly

    Args:
        data (string): A base64 string

    Returns:
        string: A correctly padded base64 string
    """
    missing_padding = len(data) % 4
    if missing_padding != 0:
        data += '=' * (4 - missing_padding)
    return data


def parse_jwt(qr_data):
    """Parse a jwt out of the qr data that comes in as a base64 string

    Args:
        qr_data (string): A base64 string

    Returns:
        string: A deflate encoded jwt
    """
    jwt = ""
    previousChar = None
    for element in qr_data:
        if str.isdigit(element):
            if previousChar is not None:
                jwt += str(chr(int(previousChar + element) + 45))
                previousChar = None
            else:
                previousChar = element
        if not element:
            break
    return jwt


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs=1,
                    help="Filename (default: image file, e.g. png/jpg)")
    ap.add_argument("-t", "--textfile", action="store_true",
                    help="Input as text file")
    ap.add_argument("-c", "--commandline", action="store_true",
                    help="Input via command line")
    args = ap.parse_args()

    if args.textfile:
        with open(args.input[0]) as f:
            qr_data = f.read()
    elif args.commandline:
        qr_data = args.input[0]
    else:
        data = decode(Image.open(args.input[0]))
        if data == []:
            sys.stderr.write("Error: Unable to decode QR code\n")
            sys.exit(1)
        qr_data = data[0].data.decode()

    # jwt is going to look like a jwt but it is deflate encoded
    jwt = parse_jwt(qr_data)
    header, jwt_body, signature = jwt.split('.')
    # Inflate the jwt body so we can parse it
    decompressor = zlib.decompressobj(wbits=-15)
    printable_jwt = decompressor.decompress(
        base64.urlsafe_b64decode(pad_base64(jwt_body)))

    # Parse and print the jwt body
    print(json.dumps(json.loads(printable_jwt), indent=4, sort_keys=True))
