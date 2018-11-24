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
import pickle
from queue import Queue

server_address = ('127.0.0.1', 10000+int(sys.argv[1]))

# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

# Bind to the server address
sock.bind(server_address)

chosen_node = { 'PID': '-1', 'CAPACITY': '-1' }
num_acks = 0
turn = 1
parent = '-1'

# use the code below for testing purposes
#if (int(sys.argv[2]) == 1):
#    turn = 1
#else:
#    turn = 2

def sender(p, neighbours):
    global turn, chosen_node, num_acks, parent
    current_message_id = 0
    request_resource = 0
    if turn == 1:
        input()
        print ('\033[93m STARTING ELECTION WITH ID %d \033[0m' % p)
        message = { 'TYPE': 'election', 'PID': p, 'ELID': p }
        for i in neighbours:
            sent = sock.sendto(pickle.dumps(message), ('127.0.0.1', 10000 + int(i)))
        parent = '0'
        
        while num_acks != len(neighbours):
            print ('NODE: %s CAPACITY: %s' % (chosen_node['PID'], chosen_node['CAPACITY']))
            print ('NUM OF ACKS: %d' % num_acks)
            time.sleep(random.random())
        print ('\033[93m RECEIVED ALL ACKS \033[0m')
        """
        message = { 'TYPE': 'info', 'PID': p, 'ELID': elid, 'NODE': chosen_node['pid'], 'CAPACITY': chosen_node['capacity']}
        pid = parent.get()
        sent = sock.sendto(pickle.dumps(message), ('127.0.0.1', 10000 + pid))
        parent.put(pid)
        """

def receiver(p, neighbours, capacity):
    elid = p
    global turn, chosen_node, num_acks, parent
    while True:
        #print('MESSAGE QUEUE:')
        #print(rd.queue[0])

        print ('\nwaiting to receive message')
        data = sock.recv(1024)

        if turn != 1:
            turn = 1

        message = pickle.loads(data)

        message_type = message['TYPE']
        message_pid = message['PID']
        message_elid = message['ELID']
        message_sender = ('127.0.0.1', 10000 + int(message_pid))

        if message_type == 'election':
            print ('RECEIVED ELECTION FROM %s' % message_pid)
            if message_elid > elid or parent == '-1':
                print('I HAVE NO PARENT')
                message = { 'TYPE': 'election', 'PID': p, 'ELID': message_elid }
                parent = message_pid
                elid = message_elid
                for i in filter(lambda x: x != parent, neighbours): # error
                    print(neighbours)
                    print ('SENDING TO %s, MY PARENT IS %s' % (i, parent))
                    sent = sock.sendto(pickle.dumps(message), ('127.0.0.1', 10000 + int(i)))
                num_acks = 0
            elif message_pid != parent:
                print('I HAVE A PARENT')
                message = { 'TYPE': 'ack', 'PID': p, 'ELID': elid, 'NODE': p, 'CAPACITY': capacity }
                sent = sock.sendto(pickle.dumps(message), message_sender)
        elif message_type == 'info': # Election ended
           none()
        elif message_type == 'ack':
            print ('RECEIVED ACK FROM %s' % message_pid)
            num_acks = num_acks + 1
            message_node = message['NODE']
            message_capacity = message['CAPACITY']
            if int(message_capacity) > int(chosen_node['CAPACITY']):
                for i in filter(lambda x: x != message_pid, neighbours):
                    sent = sock.sendto(pickle.dumps(message), ('127.0.0.1', 10000 + int(i)))
                chosen_node['PID'] = message_node
                chosen_node['CAPACITY'] = message_capacity

        if num_acks == len(neighbours) - 1:
            message = { 'TYPE': 'ack', 'PID': p, 'ELID': elid, 'NODE': chosen_node['PID'], 'CAPACITY': chosen_node['CAPACITY']}
            sent = sock.sendto(pickle.dumps(message), ('127.0.0.1', 10000 + int(parent)))


        time.sleep(random.random() * 5)


# Receive/respond loop
def rr_loop (p, n, capacity):
    neighbours = n.split(",")
    elid = p
    parent = -1
    num_acks = Queue()
    num_acks.put(0)

    t_sender = threading.Thread(target=sender, args=(p, neighbours))
    t_receiver = threading.Thread(target=receiver, args=(p, neighbours, capacity))

    t_sender.start()
    t_receiver.start()
    t_sender.join()
    t_receiver.join()

rr_loop(int(sys.argv[1]), sys.argv[2], sys.argv[3])
