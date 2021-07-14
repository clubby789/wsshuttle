import socket
import threading
import struct
import ipaddress
import subprocess
import os
from typing import Tuple
import atexit


def connect_socks(s1: socket.socket, s2: socket.socket):
    t1 = threading.Thread(target=connect_loop, args=(s1, s2))
    t2 = threading.Thread(target=connect_loop, args=(s2, s1))
    t1.start()
    t2.start()
    t1.join()
    t2.join()


def connect_loop(s1: socket.socket, s2: socket.socket):
    while True:
        try:
            buf = s1.recv(1024)
            if len(buf) == 0:
                break
            s2.send(buf)
        except:
            break
    # s1 has stopped responding so we can shut down the other socket
    # This should also stop the other thread
    try:
        s2.shutdown(socket.SHUT_RDWR)
        s2.close()
    except OSError:
        pass

def get_orig_dest(sock: socket.socket) -> Tuple[str, int]:
    sockaddr_in = sock.getsockopt(socket.SOL_IP, 80, 16)
    port, raw_ip = struct.unpack_from('!2xH4s', sockaddr_in[:8])
    return (str(ipaddress.IPv4Address(raw_ip)), port)


def get_ps_code(backHost: str, backPort: int, targetHost: str, targetPort: int) -> Tuple[str, int]:
    code = """
using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Threading;

namespace ConnectTwo {
    public class Connector%i {
        public static void Main() {
            TcpClient c1 = new TcpClient("%s", %i);
            NetworkStream stream2 = c1.GetStream();
            TcpClient c2 = new TcpClient("%s", %i);
            NetworkStream stream1 = c2.GetStream();
            ConnectSockets(stream1, stream2);
        }

        public static void ConnectSockets(NetworkStream s1, NetworkStream s2) {
            Thread t1 = new Thread(() => ConnectLoop(s1, s2));
            Thread t2 = new Thread(() => ConnectLoop(s2, s1));
            t1.Start();
            t2.Start();
            t1.Join();
            t2.Join();

        }

        public static void ConnectLoop(NetworkStream s1, NetworkStream s2) {
            byte[] buffer = new byte[1024];
	    try {
                while (true) {
                    int amount = s1.Read(buffer, 0, 1024);
                    if (amount < 1) { break; }
                    s2.Write(buffer, 0, amount);
                }
	    } catch (System.IO.IOException e) {
		Console.WriteLine(e);
	    }
            s1.Close();
            s2.Close();
        }


    }
}""" % (backPort, backHost, backPort, targetHost, targetPort)
    ps_code = f"""
$code = @"
{code}
"@;
add-type -TypeDefinition $code;
iex "[ConnectTwo.Connector{backPort}]::Main()";
    """
    return ps_code


def setup_iptables(netmask: str):
    if os.getuid() != 0:
        print("wsshuttle must be run as root")
        exit(-1)
    prefix = ["iptables", "-t", "nat"]
    args = [
        ["-N", "wsshuttle"],    # Add wsshuttle chain
        ["-F", "wsshuttle"],    # Flush wsshuttle chain
        ["-I", "OUTPUT", "1", "-j", "wsshuttle"],       # Insert wsshuttle at the start of OUTPUT
        ["-I", "PREROUTING", "1", "-j", "wsshuttle"],   # Insert wsshuttle at the start of PREROUTING
        ["-A", "wsshuttle", "-j", "RETURN", "--dest", "0.0.0.0/32", "-p", "tcp"], # Ignore 0.0.0.0/32
        ["-A", "wsshuttle", "-j", "REDIRECT", "--dest", netmask, "-p", "tcp", "--to-ports", "6000"] # Redirect requests
        # to the desired subnet to the wsshuttle listener
    ]
    for cmd in args:
        argument = prefix + cmd
        subprocess.run(argument)
    atexit.register(clear_iptables)


def clear_iptables():
    os.system("iptables -t nat -F wsshuttle")           # Clear wsshuttle chain
    os.system("iptables -t nat -A wsshuttle -j RETURN")
