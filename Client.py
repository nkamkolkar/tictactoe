import socket 
import json
import numpy as np
from Config import Protocol 
import queue
import Player as plyr
import Util

########################################################################
# Class : GameNetworkClient is a client proxy that handles all the 
# server communication and client/server identification via client id

# @author: Neelesh Kamkolkar
########################################################################		

"""
Client Server Communication Design: 
Client Server communicate over a TCP socket. The server is connected to Protocol.SERVER_HOST
and listening and accepting connections on Protocol.SERVER_PORT 

The game implements a custom command/data protocol between client server

All commands are described in Protocol.py 
Eg: Protocol.COMMAND_UPDATE_MODEL

The client shall construct a command and data message as a dict.
Eg: {'COMMAND' : Protocol.COMMAND_GET_MODEL, 'client_id' : self.client_id}
Each client command can have additional key/value paris in dict as required by game design 

The client/server use the json serialization to serialize and de-serialize the commands over TCP 
sockets

"""
class GameNetworkClient:
	

	def __init__(self, controller):
		self.client_id = -1
		self.server_host = None
		self.port = 0
		self.controller = controller 

	def start(self):
		#print("GameNetworkClient.start(): starting client...")
		if (self.client_id == -1):
			#self.server_host = socket.gethostname() #assign to server host
			self.server_host = Protocol.SERVER_IP # connect to this server
			self.port = Protocol.SERVER_PORT 	  # on this port
			self.client_id = np.floor(np.random.rand()*10000) #Unique ID for client
			self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.client_socket.connect((self.server_host, self.port))


	#write server model state with X/O and the corresponding row/column where 
	#the user placed their marker.
	def update_model(self, player_marker, row, column):
		#print(f"update_model: player_marker: {player_marker} : row : {row} : column : {column}")
		server_command = {'COMMAND' : Protocol.COMMAND_UPDATE_MODEL, 'client_id' : self.client_id, 'player_marker' : player_marker, 'row' : row , 'column' : column}
		self.proxy_server_call(server_command)
	
	# read the server model state 
	def get_model(self):
		#print(f"Client.py: get_model()")
		server_command = {'COMMAND' : Protocol.COMMAND_GET_MODEL, 'client_id' : self.client_id}
		result = self.proxy_server_call(server_command)
		result = self.msg_from_bytes(result)
		result = result.get(str(Protocol.COMMAND_GET_MODEL))
		print(f"Client received model change event: {result}")
		return result

	# un_register a user (implemented but not used)
	def un_register_user(self, player_name, player_marker):
		server_command = {'COMMAND' : Protocol.COMMAND_UN_REGISTER_USER, 'client_id' : self.client_id, 'player_marker' : player_marker, 'player_name':player_name}
		self.proxy_server_call(server_command)
	
	# register a player (user) with the server given the name the player chooses in the UI 
	def register_user(self, player_name):
		#print(f"Client.py: register_user(): name: {player_name}")
		server_command = {'COMMAND' : Protocol.COMMAND_REGISTER_USER, 'client_id' : self.client_id, 'player_name': player_name}
		#print(f"Client.py: register_user(): CALLING SERVER")
		res = self.proxy_server_call(server_command)
		#print(f"Client.py: register_user(): result = {res} res.type: {type(res)}")
		res = self.msg_from_bytes(res)
		res = res.get(str(Protocol.COMMAND_REGISTER_USER))
		#print(f"Client.py: register_user(): {res}:{type(res)}")
		return res

	
	# calls reset on server so any server reset reinitialization can happen. 
	def reset(self):
		#print("client.py.reset: start")
		server_command = {'COMMAND' : Protocol.COMMAND_RESET, 'client_id' : self.client_id}
		self.proxy_server_call(server_command)


	#check if there is a winner 
	#in case where there is no winner, construct an empty player instance 
	#so the client can process the special instance. 
	#This is needed so the network protocol is preserved and no special casing is needed 
	#on the client/server network layer
	#The client should handle the "no winner" situation by processing the special instance 
	#of player (see below)
	def check_for_win(self):
		#print("client.py.check_for_win: start")
		server_command = {'COMMAND' : Protocol.COMMAND_CHECK_FOR_WIN, 'client_id' : self.client_id}
		winner = self.proxy_server_call(server_command)		
		#print(f"client.py: check_for_winner() : winner is : {winner}")
		#winner is  b'{"4": {"id": "2083.0", "name": "DFDFDF", "mark": "X", "is_registered": "True"}}'
		win_result = self.msg_from_bytes(winner)
		
		# winning_player is : b'{"id": "9366.0", "name": "NK", "mark": "X", "is_registered": "True"}'
		winning_player = win_result.get(str(Protocol.COMMAND_CHECK_FOR_WIN))
		
		#print(f"winner: {winning_player} type : {type(winning_player)}")
		
		if(winning_player is not None and isinstance(winning_player, dict)):
			#print(f"*************winning player is : {winning_player}")
			## if no winner yet, server constructs a dummy player
			## {'id': '000', 'name': 'No Winner', 'mark': '--', 'is_registered': 'False'}
			if(winning_player['is_registered'] == 'True'):	
				winner_name = winning_player["name"]
				self.controller.game_over = True
				self.controller.in_progress = False
			else: 
				winner_name = "No Winner Yet"
			
		self.controller.winner = winner_name
		return self.controller.winner

	#is the game over? 
	def is_game_over(self):
		return self.controller.game_over

	#Implemented (but not used yet)
	#TODO: Simplify and abstract a player turn to hide update model calls 
	#Also can be used to prevent players from playing multiple turns (TODO)
	def next_turn(self, next_player):
		#print("client.py.next_turn: start")
		server_command = {'COMMAND' : Protocol.COMMAND_NEXT_TURN, 'client_id' : self.client_id, 'player_name' : next_player}
		self.proxy_server_call(server_command)			

	#check if two players are registered. 
	def check_for_ready(self):
		#print("client.py.check_for_ready: start")
		status = "None"
		server_command = {'COMMAND' : Protocol.COMMAND_CHECK_FOR_READY, 'client_id' : self.client_id}
		res = self.proxy_server_call(server_command)			
		#print(f"client.py: check_for_ready: {res}")
		#convert bytes to boolean
		#res = self.msg_from_bytes(res)
		if(res is not None and res != b''):
			res = Util.msg_from_bytes(res)
			#print(f"client.py: check_for_ready: CONVERTED FROM BYTES {res}  : {type(res)}")
			status = res.get(str(Protocol.COMMAND_CHECK_FOR_READY)) #json converts to int. use str
			#print(status)
		return (status)


	#supporting function to proxy a command to the server from the client
	#per protocol, expects a dict with command and client_id always present. 
	#rest can be custom. 
	def proxy_server_call(self, data_dict):
		status = None
		#print("Client.py: proxy_server_call()...entering")
		try: 
			#self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			#self.client_socket.connect((self.server_host, self.port))
			#data_dict_encoded = json.dumps(data_dict).encode('utf-8')
			data_dict_encoded = Util.msg_to_bytes(data_dict)
			#print(f"proxy_server_call.data_dict_encoded: {data_dict_encoded}")
			res = self.client_socket.sendall(data_dict_encoded)
			#print(f"proxy_server_call.sendall.result {res}")

			try:
				status = self.client_socket.recv(4096)
			except Exception as e: #TODO : Manage exceptions 
				#print(f"Client.py: trying to read from server errored: {status}")	
				raise e
				
		
			if(status is not None):
				##print("Client.py: status call return : {status}")
				status = json.loads(status).decode('utf-8')
			else: 
				#print("Read socket returned nothing")
				status = "NONE"

			#print(f"proxy_server_call.recv() {status}")

		except:
			#print(f"exception network error: client id: {self.client_id} socket : {self.client_socket}")
			#recreate connection?
			pass
		
		#print("Client.py:proxy_server_call()...exiting")
		return status 

	#function
	#return client_id - a unique client side id for each client
	def get_client_id(self):
		return self.client_id

	#getter for server host
	def get_server_host(self):
		return self.server_host

	#getter for server port
	def get_server_port(self):
		return self.port

	#setter for server host
	def set_server_host(self, host):
		self.server_host = host

	#setter for server port
	def set_server_port(self, port_num):
		self.port = port_num

	#TODO: BUG: When using the Util version of the method json exceptions are occuring
	#although the methods are same, need to debug. For now, leave this here
	#Decode to byte array
	def msg_from_bytes(self, msg):
		return json.loads(msg.decode('utf-8'))
	
	#Encode to byte array 
	def msg_to_bytes(self, msg):
		return json.dumps(msg).encode('utf-8')	

