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

MAXPACKETSZ = 512
def rcv_msg (socket): # return pickle
  unpacker = struct.Struct('!i')
  tot = unpacker.unpack(socket.recv(4))[0]
  cur = 0
  data_string = b""
  while (cur < tot):
    data = socket.recv(min(MAXPACKETSZ, tot-cur))
    data_string += data
    cur += min(MAXPACKETSZ, tot-cur)
  return pickle.loads(data_string)

def send_msg (socket, data_string : str): # msg = pickle.dumps(msg)
  tot = len(data_string)
  socket.send(struct.pack("!i", tot))
  cur = 0
  while (cur < tot):
    data = data_string[cur:cur+MAXPACKETSZ]
    socket.send(data)
    cur += MAXPACKETSZ
  return

DNS_HOST = "127.0.0.1"
DNS_PORT = 5000

def main():
  with Socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((DNS_HOST, DNS_PORT))
    print("server ready")

    while True:
        data_string, client = server_socket.recvfrom(1024)
        print(client)
        res = pickle.loads(data_string)
        res = handle(res)
        server_socket.sendto(pickle.dumps(res), client)
    
  return 0
  
mp = dict()
def handle (msg):
  if (msg.ip == ""):
    if msg.alias in mp:
      msg.ip = mp[msg.alias]
    print("get "+msg.alias)
  else:
    mp[msg.alias] = msg.ip
    print("registered " +msg.ip+" as "+msg.alias)
  return msg

if __name__ == "__main__":
  sys.exit(main())
