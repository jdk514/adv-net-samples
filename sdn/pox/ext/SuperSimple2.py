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

from pox.core import core
import pox.openflow.libopenflow_01 as of
from datetime import datetime
import pdb


log = core.getLogger()

pathTable = []

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

    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return
    packet_in = event.ofp # The actual ofp_packet_in message.
    #log.debug("OF packet: %s", packet_in)
    #log.debug("Parsed packet: %s", packet)
    #pdb.set_trace()
    print "path table"
    printPacket()
    #pdb.set_trace()
    print "Packet type is %d",packet.type
    if packet.type == packet.IP_TYPE:
        ipv4_packet = event.parsed.find("ipv4")
        tcp_packet = event.parsed.find("tcp")
        if tcp_packet is None:
            msg = of.ofp_packet_out()
            msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
            msg.data = event.ofp
            msg.in_port = event.port
            self.connection.send(msg)
            return
        if (tcp_packet.SYN != True or tcp_packet.ACK != True):
            msg = of.ofp_packet_out()
            msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
            msg.data = event.ofp
            msg.in_port = event.port
            self.connection.send(msg)
            return
        print "Current DPID is %s, Previous dpid is %s",str(self.connection.dpid),tcp_packet.payload
        print tcp_packet
        time = datetime.now().strftime('%H:%M:%S:%f')
        dpid = self.connection.dpid
        prevSwitch = ""
        #tcp_packet = event.parsed.find("tcp")
        #print tcp_packet
        #pdb.set_trace()
        #print "Flags are %d ",tcp_packet.flags
        #print "All Flags"
        #print [tcp_packet.FIN,tcp_packet.SYN,tcp_packet.RST,tcp_packet.PSH,tcp_packet.ACK,tcp_packet.URG,tcp_packet.ECN,tcp_packet.CWR]
        #print "Offset is %d",tcp_packet.off
        checker = None       
        #pdb.set_trace()
        for i in range(len(pathTable)):
            if self.connection.dpid == pathTable[i].getCurrentSwitch():
                print "test drop"
                if pathTable[i].getEndPoint() == 1:
                    checker = True
                else:
                    checker = False
        if checker is False:
            pathTable.append(PathTableRow(packet_in.in_port,"",time,dpid,tcp_packet.payload,1))
            #msg = of.ofp_packet_out()
            #msg.buffer_id = event.ofp.buffer_id
            #msg.in_port = event.port
            #self.connection.send(msg)
            return
        elif checker is True:
            #tcp_packet.payload = str(self.connection.dpid)
            #msg = of.ofp_packet_out()
            #msg.buffer_id = event.ofp.buffer_id
            #msg.in_port = event.port
            #self.connection.send(msg)
            return
        
        #msg = of.ofp_packet_out()
        pathTable.append(PathTableRow(packet_in.in_port,"",time,dpid,tcp_packet.payload,0))
	#pathTable.append(PathTableRow(packet_in.in_port,packet.dst,time,ipv4_packet.srcip))
        tcp_packet.payload = str(self.connection.dpid)
        ### Ask the switch to flood the packet out. Do not setup a rule
        msg = of.ofp_packet_out()
        msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
        msg.data = event.ofp
        msg.in_port = event.port
        self.connection.send(msg)
    ### Ask the switch to setup a rule so all packets in the flow will be
    ### flooded out
    msg = of.ofp_flow_mod()
    msg.match = of.ofp_match.from_packet(packet, event.port)
    msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
    msg.idle_timeout = 10
    msg.hard_timeout = 30
    self.connection.send(msg)


def launch ():
  """
  Starts the component. Run when Pox starts.
  """
  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    SuperSimple(event.connection)

  core.openflow.addListenerByName("ConnectionUp", start_switch)
