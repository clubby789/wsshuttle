import argparse
import getpass

from .listener import WsshuttleListener



def main() -> int:
    parser = argparse.ArgumentParser(prog="wsshuttle")
    parser.add_argument("-u", "--username", required=True)
    parser.add_argument("-p", "--password", default=None)
    parser.add_argument("-b", "--host", required=True, help="IP of this machine to backconnect to")
    parser.add_argument("-i", "--dest", required=True, help="Host to connect to")
    parser.add_argument("-H", "--hash", default=None)
    parser.add_argument("-m", "--mask", required=True)
    args = parser.parse_args()

    if args.password is None and args.hash is None:
        args.password = getpass.getpass()

    listener = WsshuttleListener(username=args.username, password=args.password,
                                 host=args.host, dest=args.dest, mask=args.mask)
    return 0
