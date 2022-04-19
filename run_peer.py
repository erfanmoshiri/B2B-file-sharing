import os
import sys

import django

from bit_torrent.enums import MESSAGE_ACKNOWLEDGE

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "final_project.settings")
django.setup()
from bit_torrent.models.peer import Peer

# from final_project import settings
# settings.configure()


if __name__ == '__main__':
    argvs = sys.argv
    _name = argvs[1]
    peer = Peer(_name)
    peer.say_hello()
    peer.start_listening_thread()
    print('you are in the hub now.')
    while True:
        in_ = input()
        if in_ == 'leave':
            msg = peer.say_goodbye()
            if msg == MESSAGE_ACKNOWLEDGE:
                print('see you soon')
                break
            else:
                print('something went wrong, try again')
        elif in_ == 'new file':
            name = input('enter your file name: ')
            msg = peer.say_i_have_file(name)
            if msg == MESSAGE_ACKNOWLEDGE:
                print('file added')
            else:
                print('something went wrong, try again.')
        elif in_ == 'request file':
            name = input('enter your file name: ')
            msg = peer.say_i_want_file(name)
            if msg == MESSAGE_ACKNOWLEDGE:
                # print('its being processes :)')
                pass
            else:
                print('something went wrong, try again.')
