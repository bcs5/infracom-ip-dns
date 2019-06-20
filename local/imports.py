import os
import time
import socket
import struct
import pickle
import itertools
import subprocess
from enum import Enum
import threading
from socket import socket as Socket

MAX_PACKETS = 1512

class Command(Enum):
  LIST = 1
  GET = 2

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
