#!/usr/bin/env python3

import sys
import itertools
import socket
from socket import socket as Socket

import struct
import pickle
from enum import Enum

import os

class DNSPacket:
  alias = ""
  ip = ""
  def __init__(self, alias, ip):
    self.alias = alias
    self.ip = ip

def rcv_msg (socket): # return pickle
  unpacker = struct.Struct('!i')  
  packed_int = socket.recv(struct.calcsize('!i'));
  msg_size = unpacker.unpack(packed_int)[0]
  return pickle.loads(socket.recv(msg_size))

def send_msg (socket, data_string): # msg = pickle.dumps(msg)
  unpacker = struct.Struct('!i')  
  packed_int = struct.pack("!i", sys.getsizeof(data_string))  
  msg_size = unpacker.unpack(packed_int)[0]
  socket.send(packed_int)
  socket.send(data_string)  
  return

DNS_HOST = "127.0.0.1"
DNS_PORT = 5000

def main():
  with Socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((DNS_HOST, DNS_PORT))
    server_socket.listen(1)
    print("server ready")

    while True:
      with server_socket.accept()[0] as connection_socket:
        print("dns request")
        res = rcv_msg(connection_socket);
        msg = handle(res);
        send_msg(connection_socket, pickle.dumps(msg));
    
  return 0
  
mp = dict()
def handle (msg):
  if (msg.ip == ""):
    if msg.alias in mp:
      msg.ip = mp[msg.alias];
    print("get "+msg.alias);
  else:
    mp[msg.alias] = msg.ip;
    print("registered " +msg.ip+" as "+msg.alias);
  return msg

if __name__ == "__main__":
  sys.exit(main())
  
  

