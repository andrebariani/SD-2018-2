import socket
import struct
import sys
import time
import heapq
from multiprocessing import Process

data_heap = []

multicast_group = '0.0.0.0'
server_address = ('0.0.0.0', 10000)

# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind to the server address
sock.bind(server_address)

# Tell the operating system to add the socket to the multicast group
# on all interfaces.
group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, mreq)

# Receive/respond loop
def rr_loop (t, p):
    sys.stdout = open('p' + str(p) + '.txt', 'a')
    while True:
        t = t + 1
        message = 't' + str(t) + '-p' + str(p)
        print ('sending %s' % message)
        sent = sock.sendto(message.encode(), (multicast_group, 10000))

        print ('\nwaiting to receive message')
        data, address = sock.recvfrom(1024)

        if (data == 'ack'):


        tmp = data[1:data.find('-')]

        heapq.heappush(data_heap, data)

        print(data_heap)

        time.sleep(5)

        print ('received %s bytes from %s' % (len(data), address))
        print (data)

        print ('sending acknowledgement to', address)
        sock.sendto('ack-' + (data[data.find('-')+2:]).encode(), address)

p = Process(target=rr_loop, args=(int(sys.argv[1]) + 1, int(sys.argv[2]) + 1))
p1 = Process(target=rr_loop, args=(int(sys.argv[1]) + 2, int(sys.argv[2]) + 2))
p.start()
p1.start()
rr_loop(sys.argv[1],sys.argv[2])
p.join()
p1.join()
