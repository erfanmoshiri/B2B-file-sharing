# B2B-file-sharing
a bittorrent-based B2B file sharing simulation in python

### How to run the program:
In this program, Python and django are used to store program data such as files and peers.
To install the requirements in the main project path, use the following command:
```bash
pip install -r requirements.txt
```

In this project, in addition to the default Django files, there are 2 main files, Peer and Tracker, in the package
models.torrent_bit. The task of each is clear.
To work with them, we used 2 interface files called **peer_run**, **tracker_run**. You need it to work with peers and trackers.

Run the py.runner_tracker file to launch the tracker:
```bash
Python run_tracker.py
```
Also, to create and use an instance of peer, type the file py.runner_peer with the name of the peer:
```bash
Python run_peer.py peer1
```
You can do this in again to have more peers. If such a peer was created before, the tracker detects and returns its specified port. And if not, assign a new port to it.
This port represents on which port the peer receives the messages.
It should be noted that the tracker itself listens to a specific port in advance and responds to requests

### how it works in background:
- The tracker is always running and listening without interruption.
- A new peer comes in and informs the tracker that it is activated and the tracker informs him which port to listen on.
- Peer can also tell what files it already owes. By default, files are identified by their name, just as peers are identified by their names.
- Peer can also be removed, in which case the tracker will disable it.
- Any peer that declares a file to the tracker, Tracker has a list of peers that hold that file. Selects a number of them, Gives each one a specific port. It tells the recipient to listen to this port and wait for the a portion of the file you requested.
- tells each sender to send the that portion through this port (which is waiting for you).
- It should be noted that in order to inform, it uses threading, and in separate threads transimts this information simultaneously.
- Now we go to the peers section. We have each peer to listen on a port without interruption
- through it realizes that it must now send the part of the file (previously requested by others)
- For each one, it makes a series of fragments and transmits the sections through them
- It should be noted that before sending, Breaks the desired part and sends that desired part
- Also, if you have to wait for a large number of transmitted sections, listen to each one on a separate port as told by the tracker.
- After receiving all the sections, it binds them together and creates a file with the same file name (with a .bts extension)
- In addition to all this, because of multi-threading, a peer can receive other commands and execute them separately at the same time.
