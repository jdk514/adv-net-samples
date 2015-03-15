# Copyright 2014 Tim Wood and James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This is a really simple POX program that just prints info about
any packets it receives.
"""
import pox
from pox.core import core
import pox.openflow.libopenflow_01 as of
from datetime import datetime
import pickle
import pdb
import socket


log = core.getLogger()

pathTable = []

def mysend(self, msg):
	totalsent = 0
	while totalsent < MSGLEN:
		sent = self.sock.send(msg[totalsent:])
		if sent == 0:
			raise RuntimeError("socket connection broken")
		totalsent = totalsent + sent

def create_graph(path_table):
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



def printPacket():
	global pathTable
	for i in range(len(pathTable)):
		print pathTable[i].getRow()

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

class SuperSimple (object):
  """
  A SuperSimple object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """
  def __init__ (self, connection):
	# Keep track of the connection to the switch so that we can
	# send it messages!
	self.connection = connection
	
	# This binds our PacketIn event listener
	connection.addListeners(self)


  def _handle_PacketIn (self, event):
	"""
	Handles packet in messages from the switch.
	"""
	
	global pathTable
	packet = event.parsed # This is the parsed packet data.
	tcp_packet = None # Declare variable
	if not packet.parsed:
	  log.warning("Ignoring incomplete packet")
	  return

	packet_in = event.ofp # The actual ofp_packet_in message.
	#print "path table"
	#printPacket()
	#print "Packet type is %d",packet.type
	
	# only care about IP packets
	if packet.type == packet.IP_TYPE:
		ipv4_packet = event.parsed.find("ipv4")
		tcp_packet = event.parsed.find("tcp") #pull out info if tcp packet

	if (tcp_packet is not None):
	# tcp_packet.res accesses TCP reserved flags - set to 3 on our packets
		if (tcp_packet is not None and tcp_packet.res == 3):
			# Set paramaters for the pathTable
			time = datetime.now().strftime('%H:%M:%S:%f')
			dpid = pox.lib.util.dpid_to_str(self.connection.dpid)
			prevSwitch = ""
			#print "Current Dpid is "+str(dpid)
			for i in range(len(pathTable)):
				if pox.lib.util.dpid_to_str(self.connection.dpid) == pathTable[i].getCurrentSwitch():
					# If switch has already seen the packet drop it
					pathTable.append(PathTableRow(packet_in.in_port, "", time, dpid, tcp_packet.payload,1))
					msg = of.ofp_packet_out()
					msg.buffer_id = event.ofp.buffer_id
					msg.in_port = event.port
					msg.actions.append(of.ofp_action_output(port = of.OFPP_NONE))
					self.connection.send(msg)
					print "Current Packet Table:"
					printPacket()
					if len(pathTable) >= 15:
						create_graph(pathTable)
					return

			# Not found in table, append with 0 value            

			pathTable.append(PathTableRow(packet_in.in_port,"",time,dpid,tcp_packet.payload,0))
			#print "new table here"
			#printPacket()	
			
			#print packet.payload.payload.payload
			packet.payload.payload.payload = str(dpid) #packet.message = dpid
			#print packet.payload.payload.payload #print packet.message	
			msg = of.ofp_packet_out()
			msg.actions.append(of.ofp_action_output(port = of.OFPP_ALL))
			msg.data = packet #event.ofp
			
			msg.in_port = event.port
			event.connection.send(msg)

			# If this is the last socket we need to send out the information for the last packet
			# if (last_packet):
			# 	s_pathTable = pickle.dumps(pathTable)
			# 	mysend(s_pathTable)
			print "Current Packet Table:"
			printPacket()
			if len(pathTable) >= 15:
				create_graph(pathTable)
			return

	### Ask the switch to setup a rule so all packets in the flow will be
	### flooded out
	#print "other type of packet encountered..." +str(packet.type)
	#msg = of.ofp_flow_mod()
	msg = of.ofp_packet_out()
#	msg.match = of.ofp_match.from_packet(packet, event.port)
	msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
	msg.data = event.ofp 
	msg.in_port = event.port
#	msg.idle_timeout = 10
#	msg.hard_timeout = 30
	event.connection.send(msg)
	

def launch ():
  """
  Starts the component. Run when Pox starts.
  """
  def start_switch (event):
	log.debug("Controlling %s" % (event.connection,))
	SuperSimple(event.connection)

  core.openflow.addListenerByName("ConnectionUp", start_switch)
