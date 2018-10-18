# Autores:
# Breno Vinicius Viana de Oliveira - RA 726498
# Gabriel Rodrigues Rocha - RA 726518

import socket
import struct
import sys
import time
import random
import heapq
import threading
from queue import Queue

data_heap = []
resource_status = 0 # 0 -> not using resource, 1 -> wants resource, 2 -> using resource

number_of_messages = 5

multicast_group = '224.0.0.1'
server_address = ('127.0.0.1', 10000+int(sys.argv[2]))
#server_address = ('224.0.0.1', 10000)

# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

# Bind to the server address
sock.bind(server_address)

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

def make_time(t,p,n = 0):
    return str(int(t[0:t.find(':')]) + n) + ':' + str(p)

def time2number(t,p,n = 0):
    return int(str(int(t[0:t.find(':')]) + n) + str(p))

def sender(p, n, w, q):
    global turn, resource_status
    current_message_id = 0
    request_resource = 0
    while True:
        if random.random() > float(w) and resource_status == 0 and turn == 1 and current_message_id < number_of_messages:
            print ('\033[93m I WANT THE RESOURCE \033[0m')
            request_resource = 0
            resource_status = 1
        if current_message_id < number_of_messages and resource_status == 1 and request_resource == 0:
            print('PREPARING TO SEND RESOURCE SOLICITATION')
            t = q.get()
            t = make_time(t,p)
            q.put(t)
            message = str(t) + '-' + str(p) + '*' + str(current_message_id)
            current_message_id = current_message_id + 1
            print ('SENDING %s' % message)
            for i in range(1, n+1):
                sent = sock.sendto(message.encode(), ('127.0.0.1', 10000 + i))
            request_resource = 1
        print('current_message_id: %d' % current_message_id)
        print('resource_status in sender: %d' % resource_status)
        if (current_message_id == number_of_messages):
            resource_status = 0
        time.sleep(random.random()*5)


def receiver(p, n, w, q):
    global turn, resource_status
    oked = 0
    while True:
        print('MESSAGE QUEUE:')
        print(data_heap)
        
        if oked == n and resource_status == 1:
            print('\033[4m I HAVE THE RESOURCE \033[0m')
            resource_status = 2

        while True and resource_status == 2:
            time.sleep(random.random()*2)
            if random.random() > float(w):
                print ('\033[92m I FREED THE RESOURCE \033[0m')
                for i in range(len(data_heap)):
                    qt, data = heapq.heappop(data_heap)
                    message_pid = get_pid(data)
                    message = 'ok-' + str(message_pid) + '*0'
                    print('SENDING %s' % message)
                    sock.sendto((message).encode(), ('127.0.0.1', 10000 + int(message_pid))) # change to n resources
                oked = 0
                resource_status = 0
                print('resource_status after freeing: %d' % resource_status)

        print ('\nwaiting to receive message')
        data = sock.recv(1024).decode()

        if turn != 1:
            turn = 1

        message_info = get_info(data)
        message_pid = get_pid(data)
        message_id = get_mid(data)
        message_sender = ('127.0.0.1', 10000 + int(message_pid))

        print ('message_info: %s\nmessage_pid: %s\nthis pid: %d' % (message_info, message_pid, p))

        if message_info != 'ok' and message_info != 'nok':
            message_time = time2number(message_info, message_pid)
            message_time_tmp = time2number(message_info, message_pid, 1)
            t = q.get()
            tmp = time2number(t,p)
            print('my time: %d\n message time: %d' % (tmp, message_time_tmp))
            if resource_status == 0: # not using resource
                sock.sendto(('ok-' + str(p) + '*0').encode(), message_sender) # change to n resources
                q.put(make_time(t,p,1))
            elif resource_status == 1: # plan to use resource
                if message_time <= tmp:
                    sock.sendto(('ok-' + str(p) + '*0').encode(), message_sender) # change to n resources
                    q.put(make_time(message_info, message_pid, 1))
                else:
                    sock.sendto(('nok-' + str(p) + '*0').encode(), message_sender)
                    q.put(make_time(t, p, 1))
                    heapq.heappush(data_heap, (int(message_time), data))
            elif resource_status == 2: # using resource
                heapq.heappush(data_heap, (int(message_time), data))
        elif message_info == 'ok': # change here as well
            oked = oked + 1

        print('NUMBER OF OKS: %d' % oked)

        print (data)

        time.sleep(random.random()*5)

# Receive/respond loop
def rr_loop (t, p, n, w):
    t = str(t) + ':' + str(p)
    queue = Queue()
    queue.put(t)
    t_sender = threading.Thread(target=sender, args=(p, n, w, queue))
    t_receiver = threading.Thread(target=receiver, args=(p, n, w, queue))

    t_sender.start()
    t_receiver.start()
    t_sender.join()
    t_receiver.join()

rr_loop(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]))
