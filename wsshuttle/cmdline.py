import argparse
import getpass
import re
import warnings

from .listener import WsshuttleListener



def main() -> int:
    parser = argparse.ArgumentParser(prog="wsshuttle")
    parser.add_argument("-u", "--username", required=True, help="Target username")
    parser.add_argument("-p", "--password", default=None, help="Target user's password")
    parser.add_argument("-b", "--host", required=True, help="IP of this machine to backconnect to")
    parser.add_argument("-i", "--dest", required=True, help="Host to connect to")
    parser.add_argument("-H", "--hash", default=None, help="NTLM hash")
    parser.add_argument("-m", "--mask", required=True, help="Subnet mask to tunnel into")
    args = parser.parse_args()

    if args.hash and args.password:
        print("Only one of --hash and --password may be specified")
        return -1

    if args.hash is not None:
        print("WARNING: Using hash authentication currently requires installing an extra dependency - \n"
              "pip3 install git+https://github.com/clubby789/requests-ntlm@pyspnego")
        ntlm = args.hash.lower()
        if re.match("[a-z0-9]{32}", ntlm):
            args.password = "0" * 32 + ":" + ntlm
        elif re.match(":[a-z0-9]{32}", ntlm):
            args.password = "0" * 32 + ntlm
        elif re.match("[a-z0-9]{32}:[a-z0-9]{32}", ntlm):
            args.password = ntlm
        else:
            print("Invalid hash format")
            return -1

    if args.password is None:
        args.password = getpass.getpass()

    listener = WsshuttleListener(username=args.username, password=args.password,
                                 host=args.host, dest=args.dest, mask=args.mask)
    return 0
