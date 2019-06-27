#!/usr/bin/env python3

import sys
sys.path.append('..')
from local.imports import *

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
    msg.ip = "127.0.0.1"
  else:
    mp[msg.alias] = msg.ip
    print("registered " +msg.ip+" as "+msg.alias)
  return msg

if __name__ == "__main__":
  sys.exit(main())
