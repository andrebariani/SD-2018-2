import socket
import struct
import sys
import time
import random
import heapq
import threading
from queue import Queue

data_heap = []
processed_order_list = []
received_order_list = []

number_of_messages = 5

multicast_group = '224.0.0.1'
#server_address = ('127.0.0.1', 10000+int(sys.argv[2]))
server_address = ('224.0.0.1', 10000)

# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

# Tell the operating system to add the socket to the multicast group
# on all interfaces.
group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT , 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
host = socket.gethostbyname(socket.gethostname())
sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(host))

# Bind to the server address
sock.bind(('224.0.0.1', 10000))

if (int(sys.argv[2]) == 1):
    turn = 1
else:
    turn = 2

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
        time.sleep(random.random()*5)
        if turn == 1 and current_message_id < number_of_messages:
            t = q.get()
            t = str(int(t[0:t.find(':')]) + 1) + ':' + str(p)
            q.put(t)
            message = str(t) + '-' + str(p) + '*' + str(current_message_id)
            current_message_id = current_message_id + 1
            print ('sending %s' % message)
            sent = sock.sendto(message.encode(), ('224.0.0.1', 10000))

def receiver(p, n, q):
    global turn
    ack_list = []
    acked = 0
    while True:
        print('MESSAGE QUEUE:')
        print(data_heap)

        first_pass = True
        popped = False

        while first_pass or popped:
            if (len(data_heap) != 0):
                top_message_time, top_message = data_heap[0]
                if len([x for x in ack_list if get_mid(x) == get_mid(top_message) and get_pid(x) == get_pid(top_message)]) == n:
                    print('processed message with id %s from process %s' % (get_mid(top_message), get_pid(top_message)))
                    processed_order_list.append(heapq.heappop(data_heap))
                    popped = True
                    acked = acked + 1
                    print('number of processed messages: %d' % acked)
                    ack_list = [x for x in ack_list if get_mid(x) != get_mid(top_message) or get_pid(x) != get_pid(top_message)]
                else:
                    popped = False
            else:
                popped = False
            first_pass = False

        if acked == n * number_of_messages:
            print('RECEIVED ORDER LIST:')
            print(received_order_list)
            print('PROCESSED ORDER LIST')
            print(processed_order_list)

        print ('\nwaiting to receive message')
        data = sock.recv(1024).decode()

        if turn != 1:
            turn = turn - 1

        message_info = get_info(data)
        message_pid = get_pid(data)
        message_id = get_mid(data)

        print ('message_info: %s\nmessage_pid: %s\nthis pid: %d' % (message_info, message_pid, p))

        if message_info != 'ack':
            received_order_list.append(data)
            message_time = int(str(int(message_info[0:message_info.find(':')])) + str(message_pid))
            message_time_tmp = int(str(int(message_info[0:message_info.find(':')]) + 1) + str(message_pid))
            t = q.get()
            tmp = int(str(int(t[0:t.find(':')]) + 1) + str(p))
            if message_time_tmp > tmp:
                q.put(str(int(message_info[0:message_info.find(':')]) + 1) + ':' + str(message_pid))
            else:
                q.put(str(int(t[0:t.find(':')]) + 1) + ':' + str(p))
            heapq.heappush(data_heap, (int(message_time), data))
            print('Sending ack to process %s with message %s' % (message_pid, message_id))
            sock.sendto(('ack-' + message_pid + '*' + message_id).encode(), ('224.0.0.1', 10000))
        else:
            ack_list.append(data)
            print ('ACKNOWLEDGEMENT LIST:')
            print (ack_list)

        time.sleep(random.random()*5)

        print (data)

# Receive/respond loop
def rr_loop (t, p, n):
    t = str(t) + ':' + str(p)
    queue = Queue()
    queue.put(t)
    t_sender = threading.Thread(target=sender,args=(p, queue))
    t_receiver = threading.Thread(target=receiver, args=(p, n, queue))

    t_sender.start()
    t_receiver.start()
    t_sender.join()
    t_receiver.join()

rr_loop(int(sys.argv[1]),int(sys.argv[2]), int(sys.argv[3]))
