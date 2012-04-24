from scapy.all import *

###### Websocket stuff ########

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.websocket import WebSocketHandler

# Totally inefficient. Going for simpliciy.
outbound_packets = []
connection = None

class PacketSniffer(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self) 

	def run(self):
		global connection
		while (True):
			pkt = sniff(iface="eth0", count=1)
			pkt = pkt[0][IP]
			
			for outbound_packet in outbound_packets:
				if outbound_packet.dst == pkt.src:
					if outbound_packet.dport == pkt.sport:
						
						pkt.dst = "10.0.0.1"
						del ipPacket[TCP].chksum
						del ipPacket[IP].chksum
						pkt.show2() # Force recompute the checksum
			
						if connection:
							connection.write_message(str(pkt).encode('base64'))
			

class Handler(WebSocketHandler):
	def open(self):
		global connection
		print "New connection opened."
		connection = self

	def manipulate_outgoing_packet(self, message):
		global outbound_packets
		ipPacket = IP(message)
		outbound_packets.append(ipPacket)
		print "outbound packets is " + outbound_packets
		ipPacket.src = "10.202.43.31"
		del ipPacket[TCP].chksum
		del ipPacket[IP].chksum
		send(ipPacket)
		
	def on_message(self, message):
		print "Received message from web socket: " + message
		decodedMsg = message.decode('base64')
		manipulate_outgoing_packet(decodedMsg)

	def on_close(self):
		global connection
		print "Connection closed."
		connection = None

	def allow_draft76(self):
		return True

sniffingThread = PacketSniffer()
sniffingThread.daemon = True
sniffingThread.start()

## TESTING
ipPacket = IP("RQAAQIPkQABABpLwCgAAAUWs1DbV5QBQiZA2PgAAAACwAv//Cp8AAAIEBbQBAwMBAQEICl1UFSYAAAAABAIAAA==".decode('base64'))
outbound_packets.append(ipPacket)
print "outbound packets is " + outbound_packets
ipPacket.src = "10.202.43.31"
del ipPacket[TCP].chksum
del ipPacket[IP].chksum
send(ipPacket)
			
wsServer = HTTPServer(Application([("/websocket/", Handler)]))
print "Server started."
wsServer.listen(8080)
IOLoop.instance().start()