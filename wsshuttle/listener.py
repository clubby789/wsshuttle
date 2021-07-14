#! /usr/bin/python3

from typing import List, Tuple
import socket
import threading
import socketserver
import base64
import random

import winrm
from winrm import transport

from .utils import connect_socks, get_orig_dest, get_ps_code, setup_iptables

class WsshuttleListener:
    host: str
    sess: winrm.Session
    username: str
    password: str
    shells: List[str]
    retries: int

    def __init__(self, username, password, host, dest, mask):
        self.host = host
        self.dest = dest
        self.username = username
        self.password = password
        self.retries = 0
        setup_iptables(mask)
        self.create_session()
        self.test_conn()
        self.create_server()

    def create_session(self, auth=None):
        if auth is None:
            auth = (self.username, self.password)
        self.sess = winrm.Session(self.dest, auth=auth, transport="ntlm")
        self.shells = []

    def test_conn(self):
        self.shells.append(self.sess.protocol.open_shell())

    def create_server(self, ip="0.0.0.0", port=6000):
        socketserver.TCPServer.allow_reuse_address = True
        server =  ShuttleTCPServer((ip, port), ShuttleRequestHandler)
        server.listener = self
        with server:
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.start()
            server_thread.join()

    def run_command(self, shell, path, argv) -> bool:
        try:
            self.sess.protocol.run_command(shell, path, argv)
            self.retries = 0
            return False
        except (winrm.exceptions.WinRMError, winrm.exceptions.WinRMTransportError):
            if self.retries >= 5:
                print("Error - max retries exceeded during connection")
                exit(-1)
            self.create_session()
            self.retries += 1
            return True


class ShuttleTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    listener: WsshuttleListener
    
    def get_shell(self) -> str:
        if len(self.listener.shells) < 1:
            try:
                return self.listener.sess.protocol.open_shell()
            except:
                # Session is broken, restore it
                self.listener.create_session()
        else:
            return self.listener.shells.pop()

    def return_shell(self, shell: str):
        self.listener.shells.append(shell)

    def run_command(self, path, argv):
        shell = self.get_shell()
        while self.listener.run_command(shell, path, argv):
            shell = self.get_shell()
        self.return_shell(shell)


class ShuttleRequestHandler(socketserver.BaseRequestHandler):
    server: ShuttleTCPServer

    def handle(self) -> None:
        # Each in progress connection will use 1 shell. If none are available,
        # we create a new one. The number of available shells will gradually

        dest = get_orig_dest(self.request)
        # We setup a listener on a random port for the server to connect back to
        port = random.randint(50000, 65000)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            addr = (self.server.listener.host, port)
            s.bind(addr)
            s.listen()
            # Generate code to connect our listener and the target service
            code = get_ps_code(self.server.listener.host, port, dest[0], dest[1])
            # Prepare the command for powershell execution
            encoded = base64.b64encode(code.encode('utf-16-le')).decode()
            cmd = ["-EncodedCommand", encoded]
            
            # We must run this in another thread, because it will block until it exists
            def run():
                self.server.run_command('powershell.exe', cmd)
            t = threading.Thread(target=run)
            t.start()
            conn, _ = s.accept()
            connect_socks(conn, self.request)
            t.join()
