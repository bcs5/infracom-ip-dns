#!/usr/bin/env python3

import sys
sys.path.append('..')
from local.imports import *

def rcv_msg (socket): # return pickle
  unpacker = struct.Struct('!i')
  tot = 0
  try:
    tot = unpacker.unpack(socket.recv(4))[0]
  except Exception:
    pass
    print("The connection was over.")
    return
  cur = 0
  data_string = b""
  while (cur < tot):
    data = socket.recv(min(MAX_PACKETS, tot-cur));
    data_string += data
    cur += min(MAX_PACKETS, tot-cur);
  return pickle.loads(data_string)

def send_msg (socket, data_string : str): # msg = pickle.dumps(msg)
  tot = len(data_string)
  socket.send(struct.pack("!i", tot));
  cur = 0;
  while (cur < tot):
    data = data_string[cur:cur+MAX_PACKETS]
    socket.send(data)
    cur += MAX_PACKETS
  return

DNS_HOST = "127.0.0.1"
DNS_PORT = 5000

SERVER_ALIAS = "projectx.com"
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 2080


def register_dns():
  dnssocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  res = DNSPacket(SERVER_ALIAS, SERVER_HOST);
  data_string = pickle.dumps(res)
  
  dnssocket.sendto(pickle.dumps(res), (DNS_HOST, DNS_PORT));
  data = dnssocket.recvfrom(1024)[0];
  res = DNSPacket("", "");
  if (data) :
    res = pickle.loads(data)
  
  dnssocket.close()
  return res.ip
  
def main():
  while not register_dns():
    print("trying")
  print("server ready")
  while True:
    with Socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
      server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      server_socket.bind((SERVER_HOST, SERVER_PORT))
      server_socket.listen(1)

      connection_socket, client_adress = server_socket.accept()

      while True:
        print("client accepted")
        res = rcv_msg(connection_socket)
        if not res:
          break
        msg = handle(res);
        send_msg(connection_socket, pickle.dumps(msg))
      connection_socket.close()
        
  return 0
def handle (msg):
  res = ServerPacket()
  print(msg.cmd)
  print(msg.param)
  if (msg.cmd == Command.LIST):
    arr = os.listdir()
    res.cmd = Command.LIST;
    res.data = pickle.dumps(arr);
    print("list")
    
  elif (msg.cmd == Command.GET):
    try:
      with open(msg.param, 'rb') as file:
        res.data = file.read();
    except Exception:
      pass
    res.cmd = Command.GET
    print("get ", sys.getsizeof(res.data))
    
  return res

if __name__ == "__main__":
  sys.exit(main())
