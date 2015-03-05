#!/usr/bin/python
import os
import subprocess
import pdb




cmd = "hostname -s"

process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
output,error = process.communicate()

if not error:
	output = output.rstrip()
	print "["+output+"]"
else:
	print "Failed getting hostname"
	print error



cmd ="ifconfig | awk '/HWaddr/ {print $5}' | cut -d/ -f1"

process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
output,error = process.communicate()

if not error:
	output = output.rstrip()
	print output	
else:
	print "Failed getting macs"
	print error


#ipconfig| awk '/HWaddr/ {print $5}' | cut -d/ -f1

