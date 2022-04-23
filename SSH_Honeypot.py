#!/usr/bin/env python
import argparse
import threading
import socket
import sys
import os
import traceback
import logger
import json
import paramiko
from datetime import datetime
from binascii import hexlify
from paramiko.py3compat import b, u, decodebytes

HOST_KEY = paramiko.RSAKey(filename='server.key')
SSH_BANNER = "Authorized access only! This system is a property of NewtonTech and is only meant to be accessed by system administrators and the IT manager.\nIf you are not authorized to access this system, disconnect immediately!"

UP_KEY = '\x1b[A'.encode()
DOWN_KEY = '\x1b[B'.encode()
RIGHT_KEY = '\x1b[C'.encode()
LEFT_KEY = '\x1b[D'.encode()
BACK_KEY = '\x7f'.encode()

logging.basicConfig(
    format='%(asctime)s : %(name)s : %(levelname)s : %(message)s',
    level=logging.INFO,
    filename='ssh_honeypot.log')

def handle_commands(cmd, chan, ip):

    response = ''
    if cmd.startswith('ls'):
        response = 'users.txt'
    elif cmd.startswith('pwd'):
        response = '/home/root'

    # Add more pseudo commands here

    if response != '':
        logging.info('Response from honeypot ({}): '.format(ip, response))
        response = response + '\r\n'
    chan.send(response)

class BasicSSHHoneypot(paramiko.ServerInterface):

    client_ip = None

    def __init__(self, client_ip):
        self.client_ip = client_ip
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        logging.info('client called check_channel_request ({}): {}'.format(
            self.client_ip, kind))
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED

    def get_allowed_auths(self, username):
        logging.info('client called get_allowed_auths ({}) with username {}'.format(
            self.client_ip, username))
        return 'publickey, password'

    def check_auth_publickey(self, username, key):
        fingerprint = u(hexlify(key.get_fingerprint()))
        logging.info('client public key ({}): {}, username: {}, key name: {}, md5 fingerprint: {}, base64: {}, bits: {}'.format(
            self.client_ip, username, key.get_name(), fingerprint, key.get_base64(), key.get_bits()))
        return paramiko.AUTH_PARTIALLY_SUCCESSFUL

    def check_auth_password(self, username, password):
        # Accept all passwords as valid by default
        logging.info('new client credentials ({}): username: {}, password: {}'.format(
            self.client_ip, username, password))
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_exec_request(self, channel, command):
        command_text = str(command.decode('utf-8'))

        logging.info('client sent command via check_channel_exec_request ({}): {}'.format(
            self.client_ip, username, command))

        return True

def handle_connection(client, addr):

    client_ip = addr[0]
        logging.info('New connection from: {}'.format(client_ip))

    try:
        transport = paramiko.Transport(client)
        transport.add_server_key(HOST_KEY)
        transport.local_version = SSH_BANNER
        server = BasicSSHHoneypot(client_ip)
        try:
            transport.start_server(server=server)
            
        except paramiko.SSHException:
            print('*** SSH negotiation failed. ')
            raise Exception("SSH negotiation failed")

        # wait for authentication
        chan = transport.accept(10)
        if chan is None:
            print('*** No channel (from '+clinet_ip+').')
            raise Exception("No channel")

        chan.settimeout(10)

        if transport.remote_mac != '':
            logging.info('Client mac ({}): {}'.format(client_ip, transport.remote_mac))

        if transport.remote_compression != '':
            logging.info('Client compression ({}): {}'.format(client_ip, transport.remote_compression))

        if transport.remote_version != '':
            logging.info('Client SSH version ({}): {}'.format(client_ip, transport.remote_version))

        if transport.remote_version != '':
            logging.info('Client SSH cipher ({}): {}'.format(client_ip, transport.remote_cipher))

        server.event.wait(10)
        if not server.event.is_set():
            logging.info('** Client ({}): never asked for a shell'.format(client_ip))
            raise Exception('No shell request')

        try:
            chan.send("Welcome to Ubuntu 18.04.1 LTS (GNU/Linux 4.15.0-36-generic x86_64)\r\n\r\n")
            run = True
            while run:
                chan.send("$ ")
                command = ''
                while not command.endswitch("\r"):
                    transport = chan.recv(1024)
                    print(client_ip+"- received:",transport)
                    # Echo input to pseudo-simulate a basic terminal
                    if(
                        transport != UP_KEY
                        and transport != DOWN_KEY
                        and transport != LEFT_KEY
                        and transport != RIGHT_KEY
                        and transport != BACK_KEY
                    ):
                        chan.send(transport)
                        command += transport.decode("utf-8")

                chan.send("\r\n")
                command = command.rstrip()
                logging.info('Command received ({}): {}'.format(client_ip, command))

                if command == 'exit':
                    settings.addLogEntry("Connection closed (via exit command): " + client_ip + '\n')
                    run = False

                else:
                    handle_commands(command, chan, client_ip)

        except Exception as err:
            print('!!! Exception: {}: {}'.format(err.__class__, err))
            try:
                transport.close()
            except Exception:
                pass

        chan.close()
    
    except Exception as err:
            print('!!! Exception: {}: {}'.format(err.__class__, err))
            try:
                transport.close()
            except Exception:
                pass

def start_server(port, bind):
    """Initialize and run the SSH server"""
    try:
        sock = socket.socket(socket.AF_INET, sock.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind, port))
    except Exception as err:
        print('*** Bind failed: {}'.format(err))
        traceback.print_exc()
        sys.exit(1)

    threads = []
    while True:
        try:
            sock.listen(100)
            print('Listening for connection ...')
            client, addr = sock.accept()
        except Exception as err:
            print('*** Listen/accept failed: {}'.format(err))
            traceback.print_exc()
        new_thread = threading.Thread(target=handle_connection, args=(client, addr))
        new_thread.start()
        threads.append(new_thread)

    for thread in threads:
        thread.join()

def detect_url(command, client_ip):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    result = re.findall(regex, command)
    if result:
        for ar in result:
            for url in ar:
                if url != '':
                    logging.info('New URL detected ({}): '.format(client_ip, url))
                    r.lpush("download_queue", url)

    ip_regex = r"([0-9]+(?:\.[0-9]+){3}\/\S*)"
    ip_result = re.findall(ip_regex, command)
    if ip_result:
        for ip_url in ip_result:
            if ip_url != '':
                logging.info('New IP-based URL detected ({}): '.format(client_ip, ip_url))
                r.lpush("download queue", ip_url)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run an SSH Honeypot server')
    parser.add_arguement("--port", "-p", help="The port to bind the SSH server to (default 22)", default=2222, type=int, action="store")
    parser.add_argument("--bind", "-b", help="The address to bind the SSH perver to", default="", type=str, action="store")
    args = parser.parse_args()
    start_server(args.port, args.bind)