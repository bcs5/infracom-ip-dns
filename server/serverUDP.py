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
tid = 0
class Client:
  
  def __init__(self, sck, address):
    self.sck = sck
    self.clientaddress = address
    self.seqA = random.randint(0, 0x3f3f3f3f);
    self.seqB = -1
    self.senderbuffer = queue.Queue();
    self.controlacks = queue.Queue(256);
    self.acks = queue.Queue(256);
    self.pktsqueue = queue.Queue(256);
    self.rcvbuffer = queue.Queue();
    self.syncth = threading.Thread(target=self.sync_th)
    self.syncth.start();
    self.senderth = threading.Thread(target=self.sender_th)
    self.senderth.start();
    self.rcvth = threading.Thread(target=self.rcv_th)
    self.rcvth.start();
    self.runth = threading.Thread(target=self.run_th)
    self.runth.start();
  
  def sync_th(self) :
    print("server seq {}".format(self.seqA));
    while (True):
      pkt = self.controlacks.get();
      if (pkt.type == ACKT.SYN):
        #print("syn ", pkt.seq, self.seqA, self.clientaddress)
        self.seqB = pkt.seq+1
      self.sck.sendto(pack(ACK(type = ACKT.SYNACK, ack = self.seqB, seq = self.seqA)), self.clientaddress)
    return;
  
  def sender_th (self):
    while True:
      data = self.senderbuffer.get();
      pkt = PACKET(seq = self.seqA, data=data);
      while True:
        self.sck.sendto(pack(pkt), self.clientaddress)
        ack = ACK(0,0,0);
        try:
          ack = self.acks.get(0, 0.01);
        except:
          continue
        if (ack.ack == self.seqA+1):
          #print("acknowledged {}".format(self.seqA));
          self.seqA += 1
          break;
    return

  def rcv_th (self): # packets only
    while True:
      pkt = self.pktsqueue.get();
      if (pkt.seq == self.seqB):
        print("rcved data {} {}".format(pkt.seq, tid))
        self.rcvbuffer.put(pkt.data);
        self.seqB += 1
      self.sck.sendto(pack(ACK(type = ACKT.ACK, ack= self.seqB, seq=self.seqA)), self.clientaddress) #send ack
    return
  
  # application layer
  def rcv_msg(self): # return pickle
    unpacker = struct.Struct('!i')
    tot = unpacker.unpack(self.rcvbuffer.get())[0];
    cur = 0
    data_string = b""
    while (cur < tot):
      data = self.rcvbuffer.get()
      data_string += data
      cur += len(data)
    return pickle.loads(data_string)

  def send_msg(self, data_string : str): # msg = pickle.dumps(msg)
    tot = len(data_string)
    self.senderbuffer.put(struct.pack("!i", tot));
    cur = 0
    while (cur < tot):
      data = data_string[cur:cur+MAX_PACKETS]
      self.senderbuffer.put(data)
      cur += MAX_PACKETS
    return
  
  def run_th (self):
    while True:
      res = self.rcv_msg()
      msg = self.handle(res);
      self.send_msg(pickle.dumps(msg))
    return
    
  def handle (self, msg):
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
    
class esocket:
  framesqueue = queue.Queue(256);
  mp = dict();
  def __init__(self, sck):
    self.sck = sck;
    
    self.udprcvth = threading.Thread(target=self.udprcv_th)
    self.udprcvth.start();
    
    self.udpsendth = threading.Thread(target=self.udpsend_th)
    self.udpsendth.start();
    
  def sendto (self, data, address):
    self.framesqueue.put((data, address))

  def udpsend_th(self):
    while True:
      data, address = self.framesqueue.get();
      self.sck.sendto(data, address);    

  def udprcv_th(self):
    while True:
      data, address = self.sck.recvfrom(2048);
      if (address not in self.mp):
        self.mp[address] = Client(self, address);
      client = self.mp[address];
      pkt = unpack(data);
      if (isinstance(pkt, ACK)):
        if(pkt.type != ACKT.ACK):
          try:
            client.controlacks.put_nowait(pkt)
          except Exception:
            pass
        else:
          try:
            client.acks.put_nowait(pkt);
          except Exception:
            pass
      else:
        try:
          client.pktsqueue.put_nowait(pkt);
        except Exception:
          pass

def main():
  SERVER_HOST = "127.0.0.1"
  SERVER_PORT = 2080
  sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM);
  sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  sck.bind((SERVER_HOST, SERVER_PORT));
  esck = esocket(sck);
  
if __name__ == "__main__":
  sys.exit(main())
  
  
  

