# Import socket module
import socket

class c:
    def __init__(self, name, h):
        c.name = name
        c.h = h

# Create a socket object
s = socket.socket()

# Define the port on which you want to connect
port = 12345

# connect to the server on local computer
print('connecting')
s.connect(('127.0.0.1', port))
print('connected')
while True:
    i = input()
    i1 = input()
    c = c(i, i1)
    if i == 'cc':
        break
    # s.send(c..encode())
# receive data from the server and decoding to get the string.
print(s.recv(1024).decode())
# close the connection
s.close()
