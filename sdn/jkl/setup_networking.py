#!/usr/bin/python
import os
import subprocess
import pdb

safe_ips = ["10.10.19.2","10.10.20.2","10.10.21.2","10.10.22.2","10.10.23.2","10.10.24.2","10.10.25.2","10.10.26.2","10.10.27.2","10.10.28.2","10.10.29.2","10.10.30.2","10.10.31.2"]
ips_mod = []
ip_pox = ""

#os.system("ls -l ")
eth_number = 1
while (True):
	eth = "eth"+str(eth_number)
	cmd = "ip addr show "+eth+" | awk '/inet/ {print $2}' | cut -d/ -f1"
	#print cmd
	process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	output, error = process.communicate()

	parsed_ips = []

	if not error:
		#pdb.set_trace()
		
			
		
		parsed_ips = output.split("\n")
		ip = parsed_ips[0].strip()
		print ip
		if ip in safe_ips:
			ip_pox = ip
			ip_pox=ip_pox[0:len(ip_pox)-1]+str(1)
		else:
			ips_mod.append(eth)
		eth_number = eth_number + 1
	else : 
		break


print ips_mod

cmd = "sudo ovs-vsctl add-br br0"

process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
output,error = process.communicate()

if not error:
	print "Added the bridge"
else:
	print "Failed adding bridge"
	print error



for eth in ips_mod:
	cmd = "sudo ifconfig "+eth+" 0"
	#print cmd
	process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	output, error = process.communicate()

	if not error:
		print output

	else:
		print "Failed bringing down interface"
		print error


	cmd = "sudo ovs-vsctl add-port br0 "+eth
	#print cmd
	process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	output, error = process.communicate()

	if not error:
		print output
	else:
		print "Failed briding interface"
		print error


cmd = "sudo ovs-vsctl set-controller br0 tcp:"+ip_pox+":6633"
	#print cmd
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
output, error = process.communicate()

if not error:
	print output

else:
	print "Failed setting pox server location"
	print error

