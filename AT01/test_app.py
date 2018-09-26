import socket
import struct
import sys
import time
import random
import heapq
from multiprocessing import Process

data_heap = []

multicast_group = '127.0.0.1'
server_address = ('127.0.0.1', 10000+int(sys.argv[2]))

# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

# Tell the operating system to add the socket to the multicast group
# on all interfaces.
group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, mreq)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Bind to the server address
sock.bind(server_address)

def get_info(data):
    return data[0:data.find('-')]

def get_pid(data):
    return data[data.find('-')+1:data.find('*')]

def get_mid(data):
    return data[data.find('*')+1:]

# Receive/respond loop
def rr_loop (t, p, n):
    #sys.stdout = open('p' + str(p) + '.txt', 'a')
    current_message_id = 0
    ack_list = []
    acked = 0
    turn = p
    t = int(str(t) + str(p))
    while acked <= 30:
        print(data_heap)

        if turn == 1 and current_message_id <= 10:
            t = t + 1
            message = str(t) + '-' + str(p) + '*' + str(current_message_id)
            current_message_id = current_message_id + 1
            print ('sending %s' % message)
            print(type(message.encode('utf-8')))
            for i in range(1,n+1):
                sent = sock.sendto(message.encode(), ('127.0.0.1', 10000+i))
            #sent = sock.sendmsg(message.encode('utf-8'))

        if (len(data_heap) != 0):
            top_message_time, top_message = data_heap[0]
            #print (len([x for x in ack_list if get_mid(x) == get_mid(top_message) and get_pid(x) == get_pid(top_message)]))
            #print (n)
            if len([x for x in ack_list if get_mid(x) == get_mid(top_message) and get_pid(x) == get_pid(top_message)]) == n:
                print('processed message with id %s from process %s' % (message_id, message_pid))
                heapq.heappop(data_heap)
                acked = acked + 1
                print('number of processed messages: %d' % acked)
                ack_list = [x for x in ack_list if get_mid(x) != get_mid(top_message) or get_pid(x) != get_pid(top_message)]

        print ('\nwaiting to receive message')
        #data, address = sock.recvfrom(1024)
        data = sock.recv(1024).decode()
        if turn != 1:
            turn = turn - 1

        message_info = get_info(data)
        message_pid = get_pid(data)
        message_id = get_mid(data)

        print ('message_info: %s\nmessage_pid: %s\nthis pid: %d' % (message_info, message_pid, p))

        if message_info != 'ack':
            message_time = message_info
            if t < int(message_time):
                print ('current time is less than message time: %d < %d', (t, int(message_time)))
                t = int(message_time)
            heapq.heappush(data_heap, (int(message_time), data))
            #print ('sending acknowledgement to', address)
            for i in range(1,n+1):
                sock.sendto(('ack-' + message_pid + '*' + message_id).encode(), ('127.0.0.1', 10000+i))
        else:
            ack_list.append(data)
            print (ack_list)

        time.sleep(random.random()*5)

        #print ('received %s bytes from %s' % (len(data), address))
        print (data)

#p = Process(target=rr_loop, args=(int(sys.argv[1]) + 1, int(sys.argv[2]) + 1))
#p1 = Process(target=rr_loop, args=(int(sys.argv[1]) + 2, int(sys.argv[2]) + 2))
#p.start()
#p1.start()
rr_loop(int(sys.argv[1]),int(sys.argv[2]), int(sys.argv[3]))
#p.join()
#p1.join()
