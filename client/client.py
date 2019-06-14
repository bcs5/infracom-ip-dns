#!/usr/bin/env python3

import socket
import sys
import subprocess

import struct
import pickle
from enum import Enum

import time
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

def recv_msg(socket): # return pickle
  unpacker = struct.Struct('!i')
  packed_int = socket.recv(struct.calcsize('!i'));
  msg_size = unpacker.unpack(packed_int)[0]
  return pickle.loads(socket.recv(msg_size))

def send_msg(socket, data_string): # msg = pickle.dumps(msg)
  unpacker = struct.Struct('!i')
  packed_int = struct.pack("!i", sys.getsizeof(data_string))
  msg_size = unpacker.unpack(packed_int)[0]
  socket.send(packed_int)
  socket.send(data_string)
  return

DNS_HOST = "127.0.0.1"
DNS_PORT = 5000

server_alias = "projectx.com"
server_host = ""
server_port = 2080


def query_dns (alias):
  dnssocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    dnssocket.connect((DNS_HOST, DNS_PORT));
  except Exception:
    pass

  res = DNSPacket(alias, "");
  send_msg(dnssocket, pickle.dumps(res));
  res = recv_msg(dnssocket);
  dnssocket.close()
  return res.ip
   
run = True;
try:
  
  while True:
    server_host = query_dns("projectx.com");
    print("...")
    time.sleep(1)
    if server_host:
      break;
  print("connected to " + server_host)
  while run :
    arr = input().split();
    cmd = arr[0]
    param = ""
    if (len(arr) == 2):
      param = arr[1]
    
    msg = ClientPacket()
    if (cmd == "LIST"):
      msg.cmd = Command.LIST;
    elif (cmd == "GET"):
      msg.cmd = Command.GET
      msg.param = param
    elif (cmd == "CLOSE"):
      msg.cmd = Command.CLOSE
    
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
      clientSocket.connect((server_host,server_port))
    except Exception:
      pass
   
    send_msg(clientSocket, pickle.dumps(msg))
    res = recv_msg(clientSocket)
    
    clientSocket.close()
    
    if res.cmd == Command.GET: 
      with open(msg.param, 'wb') as file:
        file.write(res.data)
    elif res.cmd == Command.LIST:
      for x in res.arr:
        print(x)
    
except KeyboardInterrupt:
  print("caught keyboard interrupt, exiting")
  run = False
except EOFError:
  print("end of input")
  run = False
finally:
  print("bye");
