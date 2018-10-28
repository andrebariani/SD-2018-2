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
number_of_resources = 3
resource_status = Queue()
resource_status.put(number_of_resources * [0]) # 0 -> not using resource, 1 -> wants resource, 2 -> using resource
num_oks = number_of_resources * [0]
rd = Queue()

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

def get_resource(data):
    return data[data.find('*')+1:]

def make_time(t,p,n = 0):
    return str(int(t[0:t.find(':')]) + n) + ':' + str(p)

def time2number(t,p,n = 0):
    return int(str(int(t[0:t.find(':')]) + n) + str(p))

def sender(p, n, osn, hsn):
    global turn, resource_status
    current_message_id = 0
    request_resource = 0
    while True:
        if turn == 1 and current_message_id < number_of_messages:
            command = input()
            r = int(command[1])
            if (command[0] == 'w'):
                print ('\033[93m I WANT THE RESOURCE %d \033[0m' % r)
                rs = resource_status.get()
                rs[r] = 1
                resource_status.put(rs)
                print('PREPARING TO SEND RESOURCE SOLICITATION')
                t = hsn.get()
                osn.get()
                #t = make_time(t,p,1)
                osn.put(t)
                hsn.put(t)
                message = str(t) + '-' + str(p) + '*' + str(r)
                current_message_id = current_message_id + 1
                print ('SENDING %s' % message)
                for i in range(1, n+1):
                    sent = sock.sendto(message.encode(), ('127.0.0.1', 10000 + i))
                while True:
                    time.sleep(random.random())
                    if num_oks[r] == n:
                        break
                print('\033[4m I HAVE THE RESOURCE %d \033[0m' % r)
            elif (command[0] == 'r'):
                print ('\033[92m I FREED THE RESOURCE %d \033[0m' % r)
                rs = resource_status.get()
                rs[r] = 0
                resource_status.put(rs)
                nodes = rd.get()
                for i in range(n):
                    if (nodes[r][i] == 1):
                        sent = sock.sendto(('ok-' + str(p) + '*' + str(r)).encode(), ('127.0.0.1', 10000 + i + 1))
                        nodes[r][i] = 0
                num_oks[r] = 0
                rd.put(nodes)
            
            
        #print('current_message_id: %d' % current_message_id)
        #print('resource_status in sender: %d' % resource_status)
        time.sleep(random.random() * 5)

def receiver(p, n, osn, hsn):
    global turn
    while True:
        print('MESSAGE QUEUE:')
        print(rd.queue[0])

        print ('\nwaiting to receive message')
        data = sock.recv(1024).decode()

        if turn != 1:
            turn = 1

        message_info = get_info(data)
        message_pid = get_pid(data)
        message_resource = int(get_resource(data))
        message_sender = ('127.0.0.1', 10000 + int(message_pid))

        print ('message_info: %s\nmessage_pid: %s\nthis pid: %d' % (message_info, message_pid, p))

        if message_info != 'ok' and message_info != 'nok':
            message_time = time2number(message_info, message_pid)
            message_time_tmp = time2number(message_info, message_pid, 1)
            t = osn.get()
            tmp = time2number(t,p,1)
            osn.put(t)
            rcs = resource_status.get()
            print('my request time: %d\n message time: %d' % (tmp, message_time_tmp))
            print('resource_status: %d' % rcs[message_resource])
            if rcs[message_resource] == 0: # not using resource
                sock.sendto(('ok-' + str(p) + '*' + str(message_resource)).encode(), message_sender)
            elif rcs[message_resource] == 1: # plan to use or am using resource
                if message_time_tmp <= tmp:
                    sock.sendto(('ok-' + str(p) + '*' + str(message_resource)).encode(), message_sender)
                else:
                    nodes = rd.get()
                    nodes[message_resource][int(message_pid) - 1] = 1
                    sock.sendto(('nok-' + str(p) + '*' + str(message_resource)).encode(), message_sender)
                    rd.put(nodes)

            # lines below update the actual lamport clock
            t = hsn.get()
            tmp = time2number(t,p,1)
            
            if tmp > message_time_tmp:
                hsn.put(make_time(t,p,1))
            else:
                hsn.put(make_time(message_info, message_pid, 1))
            
            resource_status.put(rcs)
        elif message_info == 'ok': # change here as well
            num_oks[message_resource] = num_oks[message_resource] + 1

        print('OKS:')
        print(num_oks)

        print (data)

        time.sleep(random.random() * 5)


# Receive/respond loop
def rr_loop (t, p, n):
    t = str(t) + ':' + str(p)
    osn = Queue()
    hsn = Queue()
    osn.put(t)
    hsn.put(t)
    rd.put([x[:] for x in [[0] * n] * n])
    t_sender = threading.Thread(target=sender, args=(p, n, osn, hsn))
    t_receiver = threading.Thread(target=receiver, args=(p, n, osn, hsn))

    t_sender.start()
    t_receiver.start()
    t_sender.join()
    t_receiver.join()

rr_loop(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
