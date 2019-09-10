# Brennan Hall - 861198641
# CS 164 Final Project - Protocol
import sys
import socket
import commands
import time
import threading
from thread import *
from uuid import getnode as get_mac

sockList = []
IPTable = [0, '10.0.0.1', '10.0.0.2', '10.0.0.3', '10.0.0.4']
NDTable = []
nodeIP = commands.getoutput("/sbin/ifconfig | grep -i \"inet\" | awk '{print $2}'")[5:13]
nodeMac = get_mac()
longMac = commands.getoutput("/sbin/ifconfig | grep -i \"HWaddr\" | awk '{print $5}'")

amRoot = True
nodeID = 0
priority = 32768
bridgeTable = []
bridgeID = str(priority) + ' ' + str(nodeMac) + ' ' + str(longMac)

rootID = bridgeID
rootDist = 0
rootPriority = priority
rootMac = nodeMac
rootLongMac = longMac

# NODE IDENTIFICATION
while IPTable[nodeID] != nodeIP:
	nodeID = nodeID + 1
print 'Welcome to Bridge ' + str(nodeID) + '!'

def socketConfig(IP, PORT):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	
	try:
		s.bind(('', PORT))
	except socket.error , msg:
		print 'Bind failed. Error Code: ' + str(msg[0]) + ' Message ' + msg[1]
		sys.exit()

	s.listen(10)
	print 'Listening on port ' + str(PORT)
	return s
	

def programConfig():
	global nodeID
	global nodeIP
	global IPTable
	global NDTable
	global bridgeTable
	global sockList
		
	# TABLE CONFIGURATION
	if nodeID == 1:
		NDTable = [['10.0.0.2', 8000], ['10.0.0.4', 8001], ['10.0.0.3', 8002]]
	elif nodeID == 2:
		NDTable = [['10.0.0.1', 8000], ['10.0.0.3', 8001], ['10.0.0.4', 8002]]
	elif nodeID == 3:
		NDTable = [['10.0.0.4', 8000], ['10.0.0.2', 8001], ['10.0.0.1', 8002]]
	elif nodeID == 4:
		NDTable = [['10.0.0.3', 8000], ['10.0.0.1', 8001], ['10.0.0.2', 8002]]
	
	bridgeTable = [['', NDTable[0][1], 'DP'], ['', NDTable[1][1], 'DP'], ['', NDTable[2][1], 'DP']]
		
	# SOCKET CONFIGURATION
	for address in NDTable:
		sockList.append(socketConfig(address[0], address[1]))
		
def newRoot(newDist, newMac, newLongMac, newPriority):
	global amRoot
	global rootID
	global rootDist
	global rootPriority
	global rootMac
	global rootLongMac
	
	rootID = str(newPriority) + ' ' + str(newMac) + ' ' + str(newLongMac)
	rootDist = newDist
	rootPriority = newPriority
	rootMac = newMac
	rootLongMac = newLongMac
	
	#print 'New Root ID: ' + rootID
	#print 'New root distance: ' + str(rootDist)
	
	if rootID == bridgeID:
		amRoot = True
		rootDist = 0
		for b in bridgeTable:
			b[2] = 'DP'
	else:
		amRoot = False
		for b in bridgeTable:
			if b[0] == rootLongMac:
				b[2] = 'RP'
			else:
				b[2] = 'DP' 
	

def sendMessage(msg, IP, PORT):
	for b in bridgeTable:
		if b[1] == PORT:
			if b[2] == 'RP':
				return
			
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((IP, PORT))
	
	msg = str(nodeIP) + ' ' + str(PORT) + ',' + msg
	
	try:
		s.sendall(msg)
	except socket.error:
		print 'SOCKET: msg failed to send'
		return
		
def blockPort(senderPort):
	global bridgeTable
	global amRoot
	
	if amRoot:
		return
		
	for b in bridgeTable:
		if b[1] == int(senderPort):
			b[2] = 'BP'

def homeThread(conn):
	global amRoot
	global bridgeID
	global bridgeTable
	global rootID
	global rootDist
	global rootMac
	global rootLongMac
	global rootPriority
	
	while True:
		data = conn.recv(1024)
		if not data:
			break
		
		blockedPort = False
		senderAddr, nRootID, nRootDist, senderID = data.split(',')
		senderIP, senderPort = senderAddr.split(' ')
		nRootPriority, nRootMac, nRootLongMac = nRootID.split(' ')
		senderPriority, senderMac, senderLongMac = senderID.split(' ')
		
		nRootDist = int(nRootDist) + 1
		nRootMac = int(nRootMac)
		nRootPriority = int(nRootPriority)
		senderPriority = int(senderPriority)
		senderMac = int(senderMac)
		senderPort = int(senderPort)
		
		for b in bridgeTable:
			if int(senderPort) == b[1]:
				b[0] = senderLongMac
				if b[2] == 'BP':
					blockedPort = True
		
		if not blockedPort:
			print 'Recieved BPDU from ' + str(senderIP) + '. Port: ' + str(senderPort)
			print data
			if nRootPriority > rootPriority:
				newRoot(int(nRootDist), nRootMac, nRootLongMac, nRootPriority)
				print 'Forwarding BPDU.'
				msg = str(rootID) + ',' + str(rootDist) + ',' + str(bridgeID)
				for nd in NDTable:
					sendMessage(msg, nd[0], nd[1])
			elif nRootPriority == rootPriority:
				if nRootMac < rootMac:
					newRoot(int(nRootDist), nRootMac, nRootLongMac, nRootPriority)
					print 'Forwarding BPDU.'
					msg = str(rootID) + ',' + str(rootDist) + ',' + str(bridgeID)
					for nd in NDTable:
						sendMessage(msg, nd[0], nd[1])
				elif nRootMac == rootMac:
					if nRootDist < rootDist:
						newRoot(int(nRootDist), nRootMac, nRootLongMac, nRootPriority)
						print 'Forwarding BPDU.'
						msg = str(rootID) + ',' + str(rootDist) + ',' + str(bridgeID)
						for nd in NDTable:
							sendMessage(msg, nd[0], nd[1])
					elif nRootDist > rootDist:
						blockPort(senderPort)
					elif bridgeID != nRootID:
						print 'Forwarding BPDU.'
						msg = str(rootID) + ',' + str(rootDist) + ',' + str(bridgeID)
						for nd in NDTable:
							sendMessage(msg, nd[0], nd[1])
				else:
					blockPort(senderPort)
			else:
				blockPort(senderPort)
		
		#print bridgeTable
			
		
	conn.close()
	
def BPDUBroadcast():
	global treeBuilt
	global nodeIP
	global nodeMac
	global NDTable
	global bridgeTable
	
	threading.Timer(5.0,BPDUBroadcast).start()
	if amRoot:
		msg = str(rootID) + ',' + str(rootDist) + ',' + str(bridgeID)
		print 'Sending: ' + msg
		for nd in NDTable:
			sendMessage(msg, nd[0], nd[1])
		print bridgeTable
	else:
		print bridgeTable
		
	# if the tree hasn't been made, send a BPDU to all IPs that aren't you
		# use sendMessage
	# if the tree is already established, only send BPDU if you are the root
	
programConfig()
time.sleep(0.25)

# INITIAL PRINT
print bridgeTable

# SENDING BPDUs
threading.Timer(5.0,BPDUBroadcast).start()

# RECIEVING BPUDs
while 1:
	for s in sockList:
		conn, addr = s.accept()
		start_new_thread(homeThread , (conn,))

for s in sockList:
	s.close()
