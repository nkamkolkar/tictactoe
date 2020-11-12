import json

########################################################################
# Class : Util - utility functions for serializing commands/data between
# client and server 
# @author: Neelesh Kamkolkar
########################################################################	

#Decode to byte array
def msg_from_bytes(msg):
	return json.loads(msg.decode('utf-8'))

#Encode to byte array 
def msg_to_bytes(msg):
	return json.dumps(msg).encode('utf-8')
