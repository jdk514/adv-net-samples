# Source: http://www.pythonforpentesting.com/2014/08/tcp-packet-injection-with-python.html
#
#
# 

import socket
import struct
import threading
import time
import sys
import random
from optparse import OptionParser
import pdb
from struct import * 
from graph_tool.all import *
import pickle

class Node(object):
	def __init__(self, pdid, time):
		self.pdid = pdid
		self.time = time

class ip(object):
	def __init__(self, source, destination):
		self.version = 4
		self.ihl = 5 # Internet Header Length
		self.tos = 0 # Type of Service
		self.tl = 0 # total length will be filled by kernel
		self.id = 54321
		self.flags = 0 # More fragments
		self.offset = 0
		self.ttl = 255
		self.protocol = socket.IPPROTO_TCP
		self.checksum = 0 # will be filled by kernel
		self.source = socket.inet_aton(source)
		self.destination = socket.inet_aton(destination)
	def pack(self):
		ver_ihl = (self.version << 4) + self.ihl
		flags_offset = (self.flags << 13) + self.offset
		ip_header = struct.pack("!BBHHHBBH4s4s",
					ver_ihl,
					self.tos,
					self.tl,
					self.id,
					flags_offset,
					self.ttl,
					self.protocol,
					self.checksum,
					self.source,
					self.destination)
		return ip_header


class tcp(object):
	def __init__(self, srcp, dstp):
		self.srcp = srcp
		self.dstp = dstp
		self.seqn = 0
		self.ackn = 0
		self.offset = 5 # Data offset: 5x4 = 20 bytes
		self.reserved = 0
		self.ece = 1
		self.cwr = 1
		self.urg = 1
		self.ack = 1
		self.psh = 1
		self.rst = 1
		self.syn = 1
		self.fin = 1
		self.window = socket.htons(5840)
		self.checksum = 0
		self.urgp = 0
		self.payload = "Experiment!!"
	def pack(self, source, destination):
		#Modify the value here to alter the reserved flags
		data_offset = (self.offset << 4) + 3 # Value added is Reserved Flags
		flags = self.fin + (self.syn << 1) + (self.rst << 2) + (self.psh << 3) + (self.ack << 4) + (self.urg << 5) + (self.ece << 6) + (self.cwr << 7)
		tcp_header = struct.pack('!HHLLBBHHH',
					 self.srcp,
					 self.dstp,
					 self.seqn,
					 self.ackn,
					 data_offset,
					 flags, 
					 self.window,
					 self.checksum,
					 self.urgp)
		#pseudo header fields
		source_ip = source
		destination_ip = destination
		reserved = 0
		protocol = socket.IPPROTO_TCP
		total_length = len(tcp_header) + len(self.payload)
		# Pseudo header
		psh = struct.pack("!4s4sBBH",
			  source_ip,
			  destination_ip,
			  reserved,
			  protocol,
			  total_length)
		psh = psh + tcp_header + self.payload
		tcp_checksum = checksum(psh)
		tcp_header = struct.pack("!HHLLBBH",
				  self.srcp,
				  self.dstp,
				  self.seqn,
				  self.ackn,
				  data_offset,
				  flags,
				  self.window)
		tcp_header+= struct.pack('H', tcp_checksum) + struct.pack('!H', self.urgp)
		return tcp_header


def checksum(data):
	s = 0
	n = len(data) % 2
	for i in range(0, len(data)-n, 2):
		s+= ord(data[i]) + (ord(data[i+1]) << 8)
	if n:
		s+= ord(data[i+1])
	while (s >> 16):
		print("s >> 16: ", s >> 16)
		s = (s & 0xFFFF) + (s >> 16)
	print("sum:", s)
	s = ~s & 0xffff
	return s

class PathTableRow():
    """
    A simple object to store details for packets.
    """
    
    def __init__(self,srcP,srcD,time,switch,prevSwitch,end):
        self.srcP = srcP
        self.srcD = srcD
        self.time = time
        self.currentSwitch = switch
        self.prevSwitch = prevSwitch
        self.endPoint = end
    def getRow(self):
        return [self.srcP,self.srcD,self.time,self.currentSwitch,self.prevSwitch,self.endPoint]
    def getCurrentSwitch(self):
	return self.currentSwitch
    def getEndPoint(self):
	return self.endPoint

def myreceive(self):
        chunks = []
        bytes_recd = 0
        while bytes_recd < MSGLEN:
            chunk = self.sock.recv(min(MSGLEN - bytes_recd, 2048))
            if chunk == '':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return ''.join(chunks)


s = socket.socket(socket.AF_INET,
                  socket.SOCK_RAW,
                  socket.IPPROTO_RAW)
src_host = "192.168.10.5"
dest_host = "192.168.10.1"#socket.gethostbyname("www.reddit.com")
data = "START"
 
# IP Header
ipobj = ip(src_host, dest_host)
#iph = ip_object.pack()
iph = ipobj.pack()
 
# TCP Header
tcpobj = tcp(1234, 1234)
tcpobj.data_length = len(data)  # Used in pseudo header
tcph = tcpobj.pack(ipobj.source,
                   ipobj.destination)
 
# Injection
packet = iph + tcph + data
#pdb.set_trace()
s.sendto(packet, (dest_host, 0))	

# Begin reading in table info
HOST = '192.168.10.4'   # Symbolic name meaning the local host
PORT = 24069    # Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:	
    s.bind((HOST, PORT))
except socket.error , msg:
    print 'Bind failed. Error code: ' + str(msg[0]) + 'Error message: ' + msg[1]
    sys.exit()
s.listen(1)

# Accept the connection once (for starter)
(conn, addr) = s.accept()

data = conn.recv(1024)
path_table = pickle.loads(data)

g = Graph()

# Define the color variables for nodes
colors = {'green':[0,1,0,1], 'red':[1,0,0,1]}
# Define properties for time/pdid, color, and label of nodes
vprop_node_info = g.new_vertex_property('object')
vprop_color = g.new_vertex_property("vector<double>")
vprop_label = g.new_vertex_property('string')
eprop_label = g.new_edge_property("string")
#eprop_color = g.new_edge_property("vector<double>")

vlist = {}
elist = {}
switch_counter = 0

# Define sender and receiver in the default state
sender = g.add_vertex()
vprop_label[sender] = "Sender"
vprop_color[sender] = colors["green"]

receiver = g.add_vertex()
vprop_label[receiver] = "Reciever"
vprop_color[receiver] = colors["red"]
for count, row in enumerate(path_table):
		# Always check if a node already exists, use pdid as unique_id
		#pdb.set_trace()
		if row.currentSwitch not in vlist:
				# If not in list, add vertex and set label/color
				vlist[row.currentSwitch] = g.add_vertex()
				vprop_color[vlist[row.currentSwitch]] = colors["red"]

				curr_switch = "switch%d" % switch_counter
				switch_counter = switch_counter + 1
				vprop_label[vlist[row.currentSwitch]] = curr_switch

		if row.prevSwitch not in vlist:
				#This value will probably change in real file
				if row.prevSwitch == ' "START"':
						pass
				else:
						# If not in list, and not NULL, add vertex and set label/color
						vlist[row.prevSwitch] = g.add_vertex()
						vprop_color[vlist[row.prevSwitch]] = colors["red"]

						curr_switch = "switch%d" % switch_counter
						switch_counter = switch_counter + 1
						vprop_label[vlist[row.prevSwitch]] = curr_switch

		# Ensure that we are not dealing with the sender node
		if row.prevSwitch != " 'START'":
				if row.endPoint == 1:
					curr_edge = "e%d" % count
					elist[curr_edge] = g.add_edge(vlist[row.prevSwitch], vlist[row.currentSwitch])
					eprop_label[elist[curr_edge]] = "END"
				else:
					curr_edge = "e%d" % count
					elist[curr_edge] = g.add_edge(vlist[row.prevSwitch], vlist[row.currentSwitch])
					eprop_label[elist[curr_edge]] = ""
		# Otherwise create edge between two nodes
		else:
				curr_edge = "e%d" % count
				elist[curr_edge] = g.add_edge(sender, vlist[row.currentSwitch])
				eprop_label[elist[curr_edge]] = ""

# vprop_obj = g.new_vertex_property('object')
# vprop_obj[sender] = Node('Sender', '123123')
# vprop_obj[receiver] = Node("Reciever", 'fdsklaj')

graph_draw(g, vertex_text=vprop_label, vertex_font_size=18,
						output_size=(1000, 1000), vertex_fill_color=vprop_color, edge_text=eprop_label, edge_font_size=40, edge_text_distance=20, edge_marker_size=40, output="graph.png")



conn.close() # When we are out of the loop, we're done, close
