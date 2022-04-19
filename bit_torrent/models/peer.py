import json
import os
import socket
import threading
import time

from bit_torrent.enums import TRACKER_PORT, MESSAGE_PEER_OUT, MESSAGE_PEER_IN, MESSAGE_PEER_HAS_FILE, \
    MESSAGE_ACKNOWLEDGE, MESSAGE_INCOMING_FILE_PARTS, MESSAGE_FILE_PART, MESSAGE_PEER_SHOULD_SEND_THIS_FILE, \
    MESSAGE_PEER_REQUESTS_FILE
from bit_torrent.models import Message


class Peer:
    def __init__(self, name):
        self.name = name
        self.port = None

    def listen_to_requests(self):
        while True:
            addr = '<not connected yet>'
            try:

                s = socket.socket()
                s.bind(('', self.port))
                # print(f'peer socket binded to {self.port}')

                s.listen(5)
                print(f'from now on, peer is listening on port {self.port}')
                while True:
                    c, addr = s.accept()
                    print(f'peer {self.name} Got connection from', addr)

                    recv_message = c.recv(1024).decode()
                    print(f'received_message from {addr}')
                    dict_msg = json.loads(recv_message)
                    if dict_msg['_type'] == MESSAGE_INCOMING_FILE_PARTS:
                        pass
                        # create threads to take those files
                        t = threading.Thread(target=Peer.file_receiver, args=(self, dict_msg['message']))
                        t.start()

                    elif dict_msg['_type'] == MESSAGE_PEER_SHOULD_SEND_THIS_FILE:
                        pass
                        # create thread send a file part
                        t = threading.Thread(target=Peer.read_file_part_and_send, args=(self, dict_msg['message']))
                        t.start()

                    c.send(self.dump_acknowledge_message().encode())

                    print(dict_msg)
                    c.close()

            except Exception as e:
                print(str(e))
                print(f'something went wrong while receiving message from {addr}')
                # c.close()
                s.close()

    def get_file_path(self, file_name):
        root = os.getcwd()
        print('root:', root)
        return os.path.join(root, 'files/' f'{self.name}/{file_name}')

    def file_receiver(self, msg):
        print(f'trying to create threads for receiving files')
        parts_count = msg['parts_count']
        file_name = msg['file_name']
        path = self.get_file_path(file_name)
        if not os.path.isdir(path):
            os.makedirs(path)
        divisions = msg['divisions']
        threads_list = []
        for d in divisions:
            threads_list.append(
                threading.Thread(
                    target=Peer.listen_and_receive_file_part,
                    args=(self, d['port'], file_name, d['part'])
                )

            )
        for t in threads_list:
            t.start()
        for i, t in enumerate(threads_list):
            t.join()
            print(f'thread {i} of peer {self.name} finished receiving part a part of {file_name}')
        self.join_file_parts(file_name, parts_count)

        print(f'all parts of <{file_name}> where successfully received and joined. ')

        # tell Tracker you have this file
        self.say_i_have_file(file_name)

    def listen_and_receive_file_part(self, port, file_name, part):
        addr = '<not defined>'
        try:
            s = socket.socket()
            # print('binding port: ', port)
            s.bind(('', port))
            print(f'waiting to receive file <{file_name}> part {part}, on port {port}')

            s.listen(5)
            while True:
                c, addr = s.accept()
                # print('Got connection from', addr)

                recv_message = c.recv(10000000).decode()
                print(f'received_message part {part}')
                dict_msg = json.loads(recv_message)
                if dict_msg['_type'] == MESSAGE_FILE_PART:
                    # write to file
                    root = self.get_file_path(file_name)
                    file_name = f'part_{part}'
                    file = os.path.join(root, file_name)
                    # print(f'writing to file {file}')
                    with open(file, 'w+') as f:
                        for line in dict_msg['file']:
                            f.writelines(line)
                    print(f'successful writing to file {file_name}')

                c.send(self.dump_acknowledge_message().encode())

                print(dict_msg)
                c.close()
                break

        except Exception as e:
            print(str(e))
            print(f'something went wrong while receiving message from {addr}')
            s.close()
            # c.close()

    def say_hello(self):
        dict_msg = self.send_message(
            Message(
                MESSAGE_PEER_IN,
                {'peer_name': self.name},
                self.port,
            )
        )
        # print(f'peer {self.name} got a new port from tracker')
        self.port = dict_msg['message']['data']
        print(f'your port in {self.port} as Tracker says')

    def say_goodbye(self):
        dict_msg = self.send_message(
            Message(
                MESSAGE_PEER_OUT,
                {'peer_name': self.name},
                self.port,
            )
        )
        return dict_msg['_type']

    def say_i_have_file(self, file_name):
        dict_msg = self.send_message(
            Message(
                MESSAGE_PEER_HAS_FILE,
                {
                    'peer_name': self.name,
                    'file_name': file_name
                },
                self.port,
            )
        )
        return dict_msg['_type']

    def say_i_want_file(self, file_name):
        dict_msg = self.send_message(
            Message(
                MESSAGE_PEER_REQUESTS_FILE,
                {
                    'peer_name': self.name,
                    'file_name': file_name
                },
                self.port,
            )
        )
        return dict_msg.get('_type')

    def read_file_part_and_send(self, message):
        part = message['part']
        port = message['port']
        parts_count = message['parts_count']
        file_name = message['file_name']

        print(f'reading and sending file <{file_name}> part <{part}>')
        lines = []
        file_path = os.path.join(self.get_file_path(file_name), f'{file_name}.bts')
        num_lines = sum(1 for line in open(file_path))
        portion = num_lines // parts_count
        with open(file_path, 'r') as f:
            for i in range(part * portion):
                f.readline()
            for i in range(portion):
                lines.append(f.readline())
        self.send_message(
            Message(
                MESSAGE_FILE_PART,
                message,
                file=lines
            ),
            port
        )

    def send_message(self, msg, port=TRACKER_PORT):
        counter = 3
        while counter > 0:
            try:
                counter -= 1
                s = socket.socket()
                s.connect(('127.0.0.1', port))
                print(f'connected to receiver on port {port}')
                break
            except:
                time.sleep(1)
        try:
            msg = json.dumps(msg.__dict__)
            s.send(msg.encode())
            print(f'SENT message to port {port}')

            msg_in = s.recv(1024).decode()
            dict_msg = json.loads(msg_in)
            s.close()
            return dict_msg
        except:
            pass
            print('not sent')
            s.close()
            # log

    def dump_acknowledge_message(self):
        return json.dumps(
            Message(
                MESSAGE_ACKNOWLEDGE,
                {},
                self.port
            ).__dict__
        )

    def join_file_parts(self, file_name, parts_count):
        file_dir = self.get_file_path(file_name)
        file_path = os.path.join(file_dir, f'{file_name}.bts')
        with open(file_path, 'a+') as outfile:
            # Iterate through list
            for part in range(parts_count):
                # Open each file in read mode
                part_path = os.path.join(file_dir, f'part_{part}')
                with open(part_path, 'r') as infile:
                    for line in infile:
                        outfile.writelines(line)
                os.remove(part_path)
                # outfile.write("\n")

    def start_listening_thread(self):
        threading.Thread(
            target=Peer.listen_to_requests,
            args=(self,)
        ).start()
