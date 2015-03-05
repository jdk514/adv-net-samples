#!/usr/bin/python
import sys
macs = {}
fileName = "macs_list"


def help():
	print "\n\nUse: python identify_switch mac_address"
	print "Example:\n\tpython identify_switch 0219b603e50a"
	print "Example with custome_mac_list_file:\n"
	print "\tpython identify_switch 0219b603e50a mac_dict_file"
	print "Functions are as follows:"
	print "(h) Call this help menu"
	print "(m) Use a list of macs"
	print "\tEX1:\n\t\tpython identify_switch m Mac_list"
	print "\tEX2:\n\t\tpython identify_switch m Mac_list mac_dict_file"
	#print "(b) Build Dictionary"


#identify macs and print out
def identifyMac(macAddr):
	global macs
	#macAddr = raw_input("Enter a mac address: ")
	macAddr = macAddr.replace(':','')
	macAddr = macAddr.replace('-','')
	#macs = {'0219b603e50a':'sender','024d9d4d125a':'sender'}
	try:
		print macAddr+" : "+macs[macAddr]
	except KeyError:
		print "ERROR: Key Error, Key does not exist"
		#help()
		#print macs


#def buildDict(fileName):
#	f = open(fileName,"rw")

#	value = "NULL"
#	print "{"

#	for line in f:
#		line = line.rstrip()
##			pass
#		elif "[" in line and "]" in line:
#			line = line.replace("[","")
#			line = line.replace("]","")
#			value = line
#			#print value
#		else:
##	print "'null':'null'}"
		#print line





#build dict from mac address
def buildDict():
	global macs
	global fileName
	try:
		f = open(fileName,"r")
	except IOError:
		print "ERROR: File not found"
		return

	value = "NULL"
	
	for line in f:
		line = line.rstrip()
		line = line.replace(':','')
		line = line.replace('-','')
		if line == "":
			pass
		elif "[" in line and "]" in line:
			line = line.replace("[","")
			line = line.replace("]","")
			value = line
		else:
			macs[line] = value
	#print macs




## IF provided a list iterate through and call identify func
def identify_mac_list(file):
	try:
		f = open(file,"r")
	except IOError:
		print "ERROR: File not found"
		return

	for line in f:
		line = line.rstrip()
		identifyMac(line)






if len(sys.argv) == 1:
	help()
elif len(sys.argv) == 2:
	buildDict()
	identifyMac(sys.argv[1])
elif sys.argv[1] == "m":
	if len(sys.argv) == 4:
		filename = sys.argv[3]
	buildDict()
	identify_mac_list(sys.argv[2])
elif len(sys.argv) == 3:
	fileName = sys.argv[2]
	buildDict()
	identifyMac(sys.argv[1])
else:
 	help()














