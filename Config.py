#
# Config : class for client/server protocol 
# The idea was for this to be a protocol specific file. 
# Keeping some additional config here. Refactor when there are
# many other configs to track, if necessary. 

class Protocol:
	#Protocol Commands
	# DO NOT CHANGE - CLIENT DEPENDENCIES
	COMMAND_REGISTER_USER = 0
	COMMAND_UN_REGISTER_USER = 1
	COMMAND_UPDATE_MODEL = 2
	COMMAND_RESET = 3
	COMMAND_CHECK_FOR_WIN = 4
	COMMAND_NEXT_TURN = 5
	COMMAND_GET_MODEL = 6
	COMMAND_CHECK_FOR_READY = 7 
	
	SERVER_IP = "10.0.0.117"
	SERVER_PORT = 12345
	BUFFER_SIZE = 4096

	def __init__():
		pass
