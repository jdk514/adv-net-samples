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
    #print "path table"
    #printPacket()
    #print "Packet type is %d",packet.type

    # only care about IP packets
    if packet.type == packet.IP_TYPE:
        ipv4_packet = event.parsed.find("ipv4")
        tcp_packet = event.parsed.find("tcp") #pull out info if tcp packet

	if (tcp_packet is not None):
		pdb.set_trace(
	# tcp_packet.res accesses TCP reserved flags - set to 3 on our packets
        if (tcp_packet is not None and tcp_packet.res == 3):
            # Set paramaters for the pathTable
            time = datetime.now().strftime('%H:%M:%S:%f')
            dpid = self.connection.dpid
            prevSwitch = ""

            for i in range(len(pathTable)):
                if self.connection.dpid == pathTable[i].getCurrentSwitch():
                    # If switch has already seen the packet drop it
                    pathTable.append(PathTableRow(packet_in.in_port, "", time, dpid, tcp_packet.payload,1))
                    msg = of.ofp_packet_out()
                    msg.buffer_id = event.ofp.buffer_id
                    msg.in_port = event.port
                    self.connection.send(msg)

                    if (len(pathTable) >= 8):
                        printPacket()
                        sys.exit()
                    return

            # Not found in table, append with 0 value            
            pathTable.append(PathTableRow(packet_in.in_port,"",time,dpid,tcp_packet.payload,0))
            msg = of.ofp_packet_out()
            msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
            msg.data = event.ofp
            msg.in_port = event.port
            self.connection.send(msg)
            if (len(pathTable) >= 8):
                printPacket()
                sys.exit()
            return

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
