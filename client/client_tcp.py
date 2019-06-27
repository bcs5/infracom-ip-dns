#!/usr/bin/env python3

import sys
sys.path.append('..')
from local.imports import *

class State(Enum):
  CONNECTED = 1
  DISCONNECTED = 2

def rcv_msg(socket): # return pickle
  unpacker = struct.Struct('!i')
  tot = unpacker.unpack(socket.recv(4))[0]
  cur = 0
  data_string = b""
  print("Status: [", end = '')
  while (cur < tot):
    print(str(int(cur / tot *100)) + '%', end = '... ')
    data = socket.recv(min(MAX_PACKETS, tot - cur))
    data_string += data
    cur += min(MAX_PACKETS, tot - cur)
  print('100%]\n')
  return pickle.loads(data_string)

def send_msg(socket, data_string : str): # msg = pickle.dumps(msg)
  tot = len(data_string)
  socket.send(struct.pack("!i", tot))
  cur = 0
  while (cur < tot):
    data = data_string[cur:cur+MAX_PACKETS]
    socket.send(data)
    cur += MAX_PACKETS
  return

DNS_HOST = "127.0.0.1"
DNS_PORT = 5000

server_port = 2080

def query_dns(alias):
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
          print("Failed to connect to server", '\'' + server_host + '\'', "at:", server_port + '.')
          raise
        state = state.CONNECTED
        print("connected to " + server_host)
      elif (cmd == "exit"):
        run = 0
        continue
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
        print('Avaliable files at', '\'' + server_alias + '\':')
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
