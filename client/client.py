#!/usr/bin/env python3

import socket
import sys
import subprocess

import struct
import pickle
from enum import Enum

import time
import os

class Command (Enum):
  LIST = 1
  GET = 2

class State (Enum):
  CONNECTED = 1
  DISCONNECTED = 2

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
  data = b""

MAXPACKETSZ = 1512

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

server_port = 2080


def query_dns (alias):
  dnssocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  res = DNSPacket(alias, "")
  data_string = pickle.dumps(res)
  
  dnssocket.sendto(pickle.dumps(res), (DNS_HOST, DNS_PORT))
  data = dnssocket.recvfrom(1024)[0]
  print("trying...")
  if (data):
    res = pickle.loads(data)
  dnssocket.close()
  return res.ip
   
run = True
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
  state = State.DISCONNECTED
  server_alias = "projectx.com"
  server_host = ""
  while run:
    if (state == State.DISCONNECTED):
      indata = input().split()
      if (len(indata) == 0):
        continue
      cmd = indata[0]
      if (cmd == "connect"):
        server_alias = indata[1]
        server_host = query_dns(server_alias)
        time.sleep(1)
        if not server_host:
          print("failed")
          continue
        try:
          clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          clientSocket.connect((server_host, server_port))
        except Exception:
          print("Failed to connect to server", '\'' + server_host + '\'', "at:", server_port)
          raise
        state = state.CONNECTED
        print("connected to " + server_host)
    elif (state == State.CONNECTED):
      indata = input().split()
      if (len(indata) == 0):
        continue
      cmd = indata[0]
      
      msg = ClientPacket()
      if (cmd == "list"):
        msg.cmd = Command.LIST
      elif (cmd == "get"):
        msg.cmd = Command.GET
        msg.param = indata[1]
      elif (cmd == "disconnect"):
        clientSocket.close()
        #clientSocket.close()
        state = State.DISCONNECTED
        print("disconnected from", server_alias)
        serveralias = ""
        continue
      else:
        continue
      print("sending...")
      send_msg(clientSocket, pickle.dumps(msg))
      print("receiving...")
      res = rcv_msg(clientSocket)
      
      if res.cmd == Command.GET:
        if (not res.data):
          print("file not found.")
          continue
        filename = indata[1]
        if (len(indata) > 2):
          filename = indata[2]
        print("saving...")
        with open(filename, 'wb') as file:
          file.write(res.data)
        print("safe!")
      elif res.cmd == Command.LIST:
        arr = pickle.loads(res.data)
        for x in arr:
          print(x)
    
except KeyboardInterrupt:
  print("caught keyboard interrupt, exiting.")
except EOFError:
  print("end of input.")
finally:
  clientSocket.close()
  run = False
  print("bye.")
