import socket
import struct
import sys
import time
import random
import heapq
import threading
from Queue import Queue

data_heap = []

multicast_group = '224.0.0.1'
#server_address = ('127.0.0.1', 10000+int(sys.argv[2]))
server_address = ('224.0.0.1', 10000)

# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

# Tell the operating system to add the socket to the multicast group
# on all interfaces.
group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
#sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton("224.0.0.1") + socket.inet_aton("192.168.5.138"))
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT , 1)
#sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
#sock.setsockopt(socket.SOL_SOCKET, socket.IP_MULTICAST_TTL, 2)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
host = socket.gethostbyname(socket.gethostname())
sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(host))

# Bind to the server address
sock.bind(('224.0.0.1', 10000))

turn = int(sys.argv[2])

def get_info(data):
    return data[0:data.find('-')]

def get_pid(data):
    return data[data.find('-')+1:data.find('*')]

def get_mid(data):
    return data[data.find('*')+1:]

def sender(p, q):
    global turn
    current_message_id = 0
    while True:
        if turn == 1 and current_message_id <= 4:
            t = q.get()
            q.put(t+1)
            message = str(t) + '-' + str(p) + '*' + str(current_message_id)
            current_message_id = current_message_id + 1
            print ('sending %s' % message)
            sent = sock.sendto(message.encode(), ('224.0.0.1', 10000))

def receiver(p, n, q):
    ack_list = []
    acked = 0
    global turn
    while True:
        print(data_heap)

        first_pass = True
        popped = False

        while first_pass or popped:
            if (len(data_heap) != 0):
                top_message_time, top_message = data_heap[0]
                if len([x for x in ack_list if get_mid(x) == get_mid(top_message) and get_pid(x) == get_pid(top_message)]) == n:
                    print('processed message with id %s from process %s' % (get_mid(top_message), get_pid(top_message)))
                    heapq.heappop(data_heap)
                    popped = True
                    acked = acked + 1
                    print('number of processed messages: %d' % acked)
                    ack_list = [x for x in ack_list if get_mid(x) != get_mid(top_message) or get_pid(x) != get_pid(top_message)]
                else:
                    popped = False
            else:
                popped = False
            first_pass = False

        print ('\nwaiting to receive message')
        data = sock.recv(1024).decode()

        if turn != 1:
            turn = turn - 1

        message_info = get_info(data)
        message_pid = get_pid(data)
        message_id = get_mid(data)

        print ('message_info: %s\nmessage_pid: %s\nthis pid: %d' % (message_info, message_pid, p))

        if message_info != 'ack':
            message_time = message_info
            #if t < int(message_time):
            #    print ('current time is less than message time: %d < %d', (t, int(message_time)))
            #    t = int(message_time)
            #else:
            #    t = t + 1
            t = q.get()
            q.put(max(int(message_time), t) + 1)
            heapq.heappush(data_heap, (int(message_time), data))
            print('sending ack to process %s with message %s' % (message_pid, message_id))
            sock.sendto(('ack-' + message_pid + '*' + message_id).encode(), ('224.0.0.1', 10000))
        else:
            ack_list.append(data)
            print (ack_list)

        time.sleep(random.random()*5)

        print (data)

# Receive/respond loop
def rr_loop (t, p, n):
    current_message_id = 0
    ack_list = []
    acked = 0
    #turn = p
    t = int(str(t) + str(p))
    queue = Queue()
    queue.put(t)
    t_sender = threading.Thread(target=sender,args=(p, queue))
    t_receiver = threading.Thread(target=receiver, args=(p, n, queue))
    
    t_sender.start()
    t_receiver.start()
    t_sender.join()
    t_receiver.join()
    """
    while True:
        print(data_heap)

        if turn == 1 and current_message_id <= 4:
            t = t + 1
            message = str(t) + '-' + str(p) + '*' + str(current_message_id)
            current_message_id = current_message_id + 1
            print ('sending %s' % message)
            print(type(message.encode('utf-8')))
            #for i in range(1,n+1):
            #    sent = sock.sendto(message.encode(), ('127.0.0.1', 10000+i))
            sent = sock.sendto(message.encode(), ('224.0.0.1', 10000))
            #sent = sock.sendmsg(message.encode('utf-8'))

        first_pass = True
        popped = False

        while first_pass or popped:
            if (len(data_heap) != 0):
                top_message_time, top_message = data_heap[0]
                if len([x for x in ack_list if get_mid(x) == get_mid(top_message) and get_pid(x) == get_pid(top_message)]) == n:
                    print('processed message with id %s from process %s' % (get_mid(top_message), get_pid(top_message)))
                    heapq.heappop(data_heap)
                    popped = True
                    acked = acked + 1
                    print('number of processed messages: %d' % acked)
                    ack_list = [x for x in ack_list if get_mid(x) != get_mid(top_message) or get_pid(x) != get_pid(top_message)]
                else:
                    popped = False
            else:
                popped = False
            first_pass = False

        if turn != 1 and turn != 0:
            turn = turn - 1
        if turn == 1:
            t_sender.start()
            turn = turn - 1

        print ('\nwaiting to receive message')
        data = sock.recv(1024).decode()

        message_info = get_info(data)
        message_pid = get_pid(data)
        message_id = get_mid(data)

        print ('message_info: %s\nmessage_pid: %s\nthis pid: %d' % (message_info, message_pid, p))

        if message_info != 'ack':
            message_time = message_info
            #if t < int(message_time):
            #    print ('current time is less than message time: %d < %d', (t, int(message_time)))
            #    t = int(message_time)
            #else:
            #    t = t + 1
            t = max(int(message_time), t) + 1
            heapq.heappush(data_heap, (int(message_time), data))
            print('sending ack to process %s with message %s' % (message_pid, message_id))
            sock.sendto(('ack-' + message_pid + '*' + message_id).encode(), ('224.0.0.1', 10000))
        else:
            ack_list.append(data)
            print (ack_list)

        time.sleep(random.random()*5)

        print (data)
    """

rr_loop(int(sys.argv[1]),int(sys.argv[2]), int(sys.argv[3]))
