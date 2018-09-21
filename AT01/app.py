import socket
import struct
import sys

message = 'very important data'
multicast_group = ('127.0.0.1', 10000)

# Create the datagram socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set a timeout so the socket does not block indefinitely when trying
# to receive data.
#sock.settimeout(0.2)
sock.settimeout(100)

try:
    # Send data to the multicast group
    print('sending "%s"' % message)
    sent = sock.sendto(message.encode(), multicast_group)

    # Look for responses from all recipients
    while True:
        print('waiting to receive')
        try:
            data, server = sock.recvfrom(16)
        except socket.timeout:
            print ('timed out, no more responses')
            break
        else:
            print ('received "%s" from %s' % (data, server))

finally:
    print('closing socket')
    sock.close()
