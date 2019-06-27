#!/usr/bin/env python3

import sys
sys.path.append('..')
from local.imports import *


class ACKT(Enum):
  SYN = 0
  SYNACK = 1
  ACK = 2

ACK = namedtuple("ACK", ["type", "ack", "seq"]);
PACKET = namedtuple("PACKET", ["seq", "data"]);

def pack(datagram):
  data = pickle.dumps(datagram);
  return struct.pack("!i{}s".format(len(data)), len(data), data);

def unpack(data):
  return pickle.loads(struct.unpack("!i{}s".format(len(data)-4), data)[1]);

seqA = random.randint(0, 0x3f3f3f3f);
seqB = -1;

senderbuffer = queue.Queue();
acks = queue.Queue(256);
pktsqueue = queue.Queue(256);
rcvbuffer = queue.Queue();
controlacks = queue.Queue(256);

def connect (sck, address):
  global seqA, seqB, controlacks
  print("client seq {}".format(seqA));
  while (True):
    pkt = ACK(type = ACKT.SYN, seq = seqA, ack = -1);
    sck.sendto(pack(pkt), address);
    try:
      pkt = unpack(controlacks.get(0, 0.01)[0]);
    except Exception:
      continue;
    if (pkt.type == ACKT.SYNACK and pkt.ack == seqA+1):
      seqB = pkt.seq;
      seqA+=1;
      break;
  print("conneted {} to {}".format(seqA, seqB));

def sender_th (sck):
  global seqA, senderbuffer;
  while True:
    data, address = senderbuffer.get();
    pkt = PACKET(seq = seqA, data=data);
    while True:
      sck.sendto(pack(pkt), address)
      res = ""
      add = ("", 0);
      try:
        res, add = acks.get(0, 0.01);
        res = unpack(res);
      except:
        continue
      if (res.ack == seqA+1):
        print("acknowledged {}".format(seqA));
        seqA += 1
        break;
  return

def rcv_th (sck): # packets only
  global seqB, pktsqueue, rcvbuffer
  while True:
    pkt, address = pktsqueue.get();
    pkt = unpack(pkt);
    if (pkt.seq == seqB):
      #print("rcved data {}".format(pkt.seq))
      rcvbuffer.put((pkt.data, address));
      seqB += 1
    sck.sendto(pack(ACK(type = ACKT.ACK, ack= seqB, seq=-1)), address) #send ack
  return

def rcv_msg(): # return pickle
  unpacker = struct.Struct('!i')
  tot = unpacker.unpack(rcvbuffer.get()[0])[0];
  cur = 0
  data_string = b""
  while (cur < tot):
    data = rcvbuffer.get()[0]
    data_string += data
    cur += min(MAX_PACKETS, tot - cur)
  return pickle.loads(data_string)

def send_msg(data_string : str, address): # msg = pickle.dumps(msg)
  tot = len(data_string)
  senderbuffer.put((struct.pack("!i", tot), address));
  cur = 0
  while (cur < tot):
    data = data_string[cur:cur+MAX_PACKETS]
    senderbuffer.put((data, address))
    cur += MAX_PACKETS
  return

def udprcv_th(sck):
  while True:
    data = ""
    address = ("", 0)
    try:
      data, address = sck.recvfrom(2048);
    except Exception:
      continue;
    pkt = unpack(data);
    if (isinstance(pkt, ACK)):
      if(pkt.type != ACKT.ACK):
        try:
          controlacks.put_nowait((data, address))
        except Exception:
          pass
      else:
        try:
          acks.put_nowait((data, address));
        except Exception:
          pass
    else:
      try:
        pktsqueue.put_nowait((data, address));
      except Exception:
        pass


DNS_HOST = "127.0.0.1"
DNS_PORT = 5000

DNS_HOST = "127.0.0.1"
DNS_PORT = 5000

SERVER_PORT = 2080
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
  
class State(Enum):
  CONNECTED = 1
  DISCONNECTED = 2

def main():
  MY_HOST = "127.0.0.1"
  SERVER_PORT = 2080;

  MY_PORT = 2000+random.randint(0, 100)
  
  print(MY_PORT)
  
  sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM);
  sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  sck.bind((MY_HOST, MY_PORT));
  sck.settimeout(0.01)
  
  state = State.DISCONNECTED
  server_alias = "projectx.com"
  server_host = ""
  run = True;
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
        senderth = threading.Thread(target=sender_th, args = (sck,))
        senderth.start();
        
        rcvth = threading.Thread(target=rcv_th, args = (sck,))
        rcvth.start();
        
        udprcvth = threading.Thread(target=udprcv_th, args = (sck,))
        udprcvth.start();
        
        
        connect(sck, (server_host, SERVER_PORT))
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
        #thread close
        state = State.DISCONNECTED
        print("disconnected from", server_alias)
        serveralias = ""
        continue
      else:
        continue
      print("sending...")
      send_msg(pickle.dumps(msg), (server_host, SERVER_PORT))
      print("receiving...")
      res = rcv_msg()
      
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
            
if __name__ == "__main__":
  sys.exit(main())
  
  
  

