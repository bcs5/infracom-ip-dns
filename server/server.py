#!/usr/bin/env python3

import sys
import itertools
import socket
from socket import socket as Socket

import struct
import pickle
from enum import Enum

import os

class Command (Enum) :
  LIST = 1
  GET = 2
  CLOSE = 3

class DNSPacket:
  alias = ""
  ip = ""
  def __init__(self, alias, ip):
    self.alias = alias
    self.ip = ip

class ClientPacket:
  cmd = Command.GET
  param = ""

class ServerPacket:
  cmd = Command.GET
  arr = [""]
  data = b""

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

SERVER_ALIAS = "projectx.com"
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 2080

def register_dns ():
  dnssocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    dnssocket.connect((DNS_HOST, DNS_PORT));
  except Exception:
    pass

  res = DNSPacket(SERVER_ALIAS, SERVER_HOST);
  send_msg(dnssocket, pickle.dumps(res));
  res = rcv_msg(dnssocket);
  
  dnssocket.close()
  
def main():
  with Socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(1)
    print("server ready")
    register_dns();


    while True:
      with server_socket.accept()[0] as connection_socket:
        print("client accepted")
        res = rcv_msg(connection_socket);
        msg = handle(res);
        send_msg(connection_socket, pickle.dumps(msg));
        
  return 0
  
  
def handle (msg):
  res = ServerPacket()
  print(msg.cmd)
  print(msg.param)
  if (msg.cmd == Command.LIST):
    arr = os.listdir()
    res.cmd = Command.LIST;
    res.arr = arr;
    print("list")
    
  elif (msg.cmd == Command.GET):
    with open(msg.param, 'rb') as file:
      res.data = file.read();
    res.cmd = Command.GET
    print("get")
    
  elif (msg.cmd == Command.CLOSE):
    print("CONNECTION CLOSED");
    res.cmd = Command.CLOSE
    
  return res

if __name__ == "__main__":
  sys.exit(main())
  
  

