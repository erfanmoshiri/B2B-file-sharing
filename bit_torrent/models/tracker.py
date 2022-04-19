import json
import random
import socket
import threading
import time

from bit_torrent.enums import MESSAGE_PEER_IN, MESSAGE_PEER_HAS_FILE, MESSAGE_PEER_OUT, MESSAGE_PEER_REQUESTS_FILE, \
    MESSAGE_INCOMING_FILE_PARTS, TRACKER_PORT, MESSAGE_ACKNOWLEDGE, MESSAGE_PEER_SHOULD_SEND_THIS_FILE
from bit_torrent.models import DbPeer, Message, DbTransaction


class Tracker:

    def __init__(self):
        self.RECV_PORT = TRACKER_PORT
        self.current_busy_ports = []

    def get_all_peer_ports(self):
        return DbPeer.objects.all().values_list('port', flat=True)

    def listen_to_requests(self):
        while True:
            addr = '<not connected yet>'
            try:

                s = socket.socket()
                time.sleep(1)
                s.bind(('', self.RECV_PORT))
                print(f'socket binded to {self.RECV_PORT}')

                s.listen(5)
                print("socket is listening")
                while True:
                    c, addr = s.accept()
                    print('Got connection from', addr)

                    recv_message = c.recv(1024).decode()
                    print(f'received_message from {addr}')
                    dict_msg = json.loads(recv_message)

                    returned = self.execute_opertaion(dict_msg)
                    dumped = json.dumps(
                        Message(
                            MESSAGE_ACKNOWLEDGE,
                            {'data': returned},
                            TRACKER_PORT
                        ).__dict__
                    )
                    c.send(dumped.encode())

                    print(dict_msg)
                    c.close()

            except Exception as e:
                print(str(e))
                print(f'something went wrong while receiving message from {addr}')
                try:
                    c.close()
                    s.detach()
                    s.close()
                except:
                    pass

    @staticmethod
    def peer_in(self, obj, **kwargs):
        # save to db
        message = obj['message']
        peer_name = message['peer_name']
        peer = DbPeer.objects.filter(name=peer_name).first()
        if peer:
            peer.activate()
            return peer.port
        else:
            peer_ports = self.get_all_peer_ports()
            while True:
                random_port = random.randint(0, 10000)
                if random_port not in self.current_busy_ports or random_port in peer_ports:
                    DbPeer.objects.create(
                        name=peer_name,
                        port=random_port
                    )
                    return random_port

    def peer_out(self, obj, **kwargs):
        # set as inactive in db
        message = obj['message']
        peer_name = message['peer_name']
        peer = DbPeer.objects.filter(name=peer_name).first()
        peer.deactivate()

    def peer_have_file(self, obj, **kwargs):
        from bit_torrent.models.db_models import DbFile
        from bit_torrent.models.db_models import DbPeer

        message = obj['message']
        file_name = message['file_name']
        peer_name = message['peer_name']

        file = DbFile.objects.filter(name=file_name).first()
        if not file:
            DbFile.objects.create(name=file_name)
            file = DbFile.objects.filter(name=file_name).first()

        file.peers.add(
            DbPeer.objects.get(name=peer_name)
        )
        return 'added'

    def peer_requests_file(self, obj, **kwargs):
        from bit_torrent.models.db_models import DbFile

        message = obj['message']
        receiver_name = message['peer_name']
        file_name = message['file_name']
        peers = DbFile.objects.filter(name=file_name).first().peers.all()
        rcv_peer = DbPeer.objects.get(name=receiver_name)
        rcv_peer_port = rcv_peer.port

        # choose among peers and select a list of them
        chosen_peers = peers[:4]
        # chosen_peers: [DbPeer]
        parts_count = len(chosen_peers)
        peer_ports = self.get_all_peer_ports()
        new_ports = []
        for p in chosen_peers:
            while True:
                r = random.randint(0, 10000)
                if r not in self.current_busy_ports or r in peer_ports:
                    new_ports.append(r)
                    break
        self.current_busy_ports += new_ports

        divisions = []
        sender_msgs = []
        threads_list = []
        for i, p in enumerate(chosen_peers):
            DbTransaction.objects.create(receiver_id=rcv_peer.id, sender_id=p.id)
            divisions.append({'peer_name': p.name, 'port': new_ports[i], 'part': i})
            sender_dict_msg = {'peer_name': receiver_name, 'port': new_ports[i], 'part': i, 'file_name': file_name,
                               'parts_count': parts_count}
            sender_msgs.append(sender_dict_msg)
            threads_list.append(
                threading.Thread(
                    target=Tracker.send_message,
                    args=(
                        Message(MESSAGE_PEER_SHOULD_SEND_THIS_FILE, sender_dict_msg),
                        p.port
                    )
                )
            )

        receiver_msg = {
            '_type': MESSAGE_INCOMING_FILE_PARTS,
            'file_name': file_name,
            'divisions': divisions,
            'parts_count': parts_count
        }

        # tell receiver msg
        rcv_message = Message(MESSAGE_INCOMING_FILE_PARTS, receiver_msg)
        receiver_thread = threading.Thread(target=Tracker.send_message, args=(rcv_message, rcv_peer_port))
        receiver_thread.start()
        receiver_thread.join()
        time.sleep(2)
        # tell senders each division
        for t in threads_list:
            t.start()

    @staticmethod
    def send_message(msg, port):
        counter = 3
        while counter > 0:
            try:
                counter -= 1
                s = socket.socket()
                s.connect(('127.0.0.1', port))
                print(f'connected to peer on port {port}')
                break
            except:
                print(f'connection to {port} refused')
                time.sleep(1)
        try:
            msg = json.dumps(msg.__dict__)
            s.send(msg.encode())
            print(f'tracker SENT message to port {port}')

            msg_in = s.recv(1024).decode()
            dict_msg = json.loads(msg_in)
            s.close()
            return dict_msg
        except:
            pass
            print('not sent')
            s.close()
            # log

    def execute_opertaion(self, dict_msg):
        msg_type = dict_msg['_type']
        function = func_mapper[msg_type]
        return_value = function(self, dict_msg)
        return return_value


func_mapper = {
    MESSAGE_PEER_IN: Tracker.peer_in,
    MESSAGE_PEER_OUT: Tracker.peer_out,
    MESSAGE_PEER_HAS_FILE: Tracker.peer_have_file,
    MESSAGE_PEER_REQUESTS_FILE: Tracker.peer_requests_file,
}
