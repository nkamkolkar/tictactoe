"""
Server.py : The Tic Tac Toe Server. Built using the TCPServer SockerServer.
Custom Protocol for commands defined in Config.py
@author : Neelesh Kamkolkar
"""

import socket
import select 
import pandas as pd 
import Player as plyr 
from Config import Protocol 
import socketserver 
import Util
import threading
import time

DEBUG = 1 #debug flag
def pdebug(msg):
	if(DEBUG):
		print("DEBUG:" + msg)

"""
Global variables
"""
clientCount = 0  # global reference count for clients
CLIENTS = [] 	 # global list of client sockets
shared_message = {'SERVER_BROADCAST' : 'Message'}  #shared message buffer
threadLock = threading.Lock()

########################################################################
# Class : ModelChangeEvent - shared across client server to update
#         which row/column/player the player chose for his/her turn
#
# Light weight model udpate event only sends whats changed last play
#
########################################################################
class ModelChangeEvent:

	def __init__(self, arow, acol, amark):
		self.row = arow
		self.col = acol
		self.mark = amark 

	def get_row(self):
		return self.row

	def get_col(self):
		return self.col

	def get_mark(self):
		return self.mark

	def get_event(self):
		return (self.row, self.col, self.mark)

	def to_string(self):
		return (str(self.row), str(self.col),str(self.mark))


########################################################################
# Class : ServerRequestHandler - Request Handler for TCPServer
#         Overrides handle() to (1) process request and (2) send results
#         back to client. Uses json serialization/deserialization for 
#		  command and data to be transported over TCP sockets
#         A single instance of this class is created per client connection
#
########################################################################
class ServerRequestHandler(socketserver.BaseRequestHandler):


	def handle(self):
		#print(f"ServerRequestHandler: handle()")

		while True:
			try:
				client_data = self.request.recv(4096).strip()  
				status = "ERROR"
				if(client_data):
					#there is data 
					#print(f"client_data: {client_data}")
					client_data_decoded = Util.msg_from_bytes(client_data)
					#print(f"converted dict: {client_data_decoded}. client_data_decoded.type: {type(client_data_decoded)}")
					if(client_data_decoded is not None):
						status = self.server.process_server_commands(client_data_decoded['COMMAND'], client_data_decoded)
				

					#Send result of command processing
					#response to client in format dict
					#{COMMAND:<RESULT>}
					#COMMAND is from Config.py and <RESULT> is an object custom to the command
					#Client proxy Client.py should parse this correctly.
					msg = {client_data_decoded['COMMAND']:status}
					if(status is not None and isinstance(status, plyr.Player) and len(status.get_name()) > 0):
						#print(f"server..check for winner result")
						msg = {client_data_decoded['COMMAND']:status.to_string()} #get winning player details (dict of player information)
					elif(status is not None and isinstance(status, pd.DataFrame)):
						#print(f"****SERVER:************* got a dataframe")
						msg = {client_data_decoded['COMMAND']:status.to_dict()}
						#update model returns the data frame
						#print(msg)
					elif(status is not None and isinstance(status, ModelChangeEvent)):
						#print(f"****SERVER:************* got a model change event")
						#get_model returns model change event
						msg = {client_data_decoded['COMMAND']:status.to_string()}
					elif(status is not None and isinstance(status, str)): 
						#check for ready return string
						#print(f"status : {status}")
						msg = {client_data_decoded['COMMAND']:status}


					#result_for_client = json.dumps(msg).encode('utf-8')	
					result_for_client = Util.msg_to_bytes(msg)
					#print(f"Sending server results {result_for_client}")
					self.request.sendall(result_for_client)
					#self.request.sendto(result_for_client, ('<broadcast>', 12345))
			except Exception as e:
				#print(e)
				pass
			



########################################################################
# Class : Server - Subclass for TCPServer for custom handling 
#         Overrides handle() to (1) process request and (2) send results
#         back to client
#
########################################################################
class Server(socketserver.ThreadingMixIn, socketserver.TCPServer):

	
	def __init__(self):
		super().__init__((Protocol.SERVER_IP, Protocol.SERVER_PORT), ServerRequestHandler)
		print(f"starting tic tac toe server on : {Protocol.SERVER_IP}:{Protocol.SERVER_PORT}")
		self.master_game_state = pd.DataFrame(([[0,0,0],[0,0,0],[0,0,0]])) # A data frame 
		self.player_1 = None  # first player 
		self.player_2 = None  # second player 
		self.whose_turn = None  #which players turn is it? 
		self.previous_turn = None #who played the previous turn? 
		self.winner = None
		self.this_turn = None
		self.registered_player_count = 0 # number of registered players 
		self.begin_game = False 
		#initialize the model_event as a special event client 
		#so can handle early calls to get model state before player registreation
		#client can be smarter to avoid this special case handling
		self.model_event = ModelChangeEvent(-1,-1,"") 
		self.player_list = []

	# start the server 
	def start(self):
		self.serve_forever()

	#Over ride get_request so we can track the client sockets
	#There were no examples on internet showing this for doing
	#Broadcasts across multiple clients using TCP
	def get_request(self):
		pdebug("get_request")
		try:
			client, addr = self.socket.accept()
			global clientCount # global reference count for clients
			global CLIENTS     # global list of client sockets
			clientCount += 1 
			pdebug("clientCount " + str(clientCount))
			if(client not in CLIENTS):
				CLIENTS.append((client,addr))
				print(f"Added new client from: {client}")
		except socket.error as msg: 
			msg = "GameServer.get_request: " + msg
			pdebug(msg)

		return(client, addr)

	def broadcast(self, a_dict):
		global clientCount
		global CLIENTS
		for client, address in CLIENTS: 
			try:
				#append the client address to the broad cast message 
				#client can verify with it's own copy or ignore
				a_dict['client_address'] = address
				msg = json.dumps(a_dict).encode('utf-8')
				client.sendall(msg)
			except Exception as e:
				#This client died or closed connection, remove the client socket from list
				#and decrement reference count
				CLIENTS.remove((client, address))
				client.close()
				clientCount -= 1 
				pass

	#Message processor 
	#protocol for client server communication and command parsing 
	def process_server_commands(self, command, client_data):
		#print(f"Server.py: process_server_commands() ***** : {command}")
		msg = "Server Process Request"
		mark = ""	#Assign a marker for each player
		if(command == Protocol.COMMAND_REGISTER_USER):
			print("server: command recieved REGISTER USER")
			#First ever registration this session
			if(len(self.player_list) == 0):
				print(f"Registering as player 1 by default {client_data['client_id']}")
				self.player_1 = plyr.Player(client_data['player_name'],"X",client_data['client_id'],True)
				self.player_1.register_player()
				#self.registered_player_count += 1 
				self.player_list.append(self.player_1)
				mark = self.player_1.get_mark()
				print(f"server.register_player(): {self.player_1.to_string()}")
			elif(len(self.player_list) == 1):
				#check if player is already registered
				p = self.player_list[0]
				if (p.get_id() == client_data['client_id']):
					print(f"Player : {p.get_name()} already registered with client id: {p.get_id()}")
				else: 
					print(f"Register SECOND Player: Registering {client_data['client_id']}")
					self.player_2 = plyr.Player(client_data['player_name'],"O",client_data['client_id'],True)
					self.player_2.register_player()
					mark = self.player_2.get_mark()
					self.player_list.append(self.player_2)				
			else:
				print("REGISTER_USER: user already registerd or game in progress")
			#print(f"server.py register_player(): {self.player_list}")
			return mark
		
		#As UX develops, should be tested. Implemented but not used by client
		if(command == Protocol.COMMAND_UN_REGISTER_USER):
			print("server: command recieved UN REGISTER USER")
			for p in player_list: 
				if (p.get_id() == client_data['client_id']):
					printf(f"Found a player : {p.get_name()} Unregistering client: {p.get_id()}")
					player_list.remove(p)
					self.registered_player_count -= 1 #decrement registered user count by 1

			print(f"server.un_register_player(): client_id: {client_data['client_id']}")

		
		if(command == Protocol.COMMAND_UPDATE_MODEL):
			print("server: command recieved  COMMAND_UPDATE_MODEL")
		
			if(len(self.player_list) < 2):
				msg = "Not enough players " + str(self.registered_player_count) + " waiting for others to join"
				print(msg)
				return msg	

			if(self.begin_game):
				self.update_data_model(client_data)
			else:				
				print(f"server.update_model(): not enough players {self.registered_player_count} wait for others to join")


		if(command == Protocol.COMMAND_GET_MODEL):	
			print("server: command recieved COMMAND_GET_MODEL")
			return self.get_model()

		#check if any player has won the game
		#if so return the player name 
		#else return the "No Winner"
		if(command == Protocol.COMMAND_CHECK_FOR_WIN):	
			print("server: command recieved COMMAND_CHECK_FOR_WIN")
			if(self.begin_game):
				self.winner =  self.checkForWin()
			else:
				self.winner = plyr.Player("No Winner", "--", "000", False)
			return self.winner

		if(command == Protocol.COMMAND_RESET):
			print("server: command recieved COMMAND_RESET ")
			self.reset()

		if(command == Protocol.COMMAND_NEXT_TURN):
			print("server: command recieved to NEXT_TURN game")
			if(self.begin_game):
				return self.next_turn(client_data)		

		if(command == Protocol.COMMAND_CHECK_FOR_READY):
			return self.check_for_ready()


	
	# server call to check if game is ready to begin 
	# precondition is two players have to register 
	def check_for_ready(self):
		##if we have 2 registerd players, the clients can begin the game
		print(f"server.py: check for ready: self.begin_game : {self.begin_game}")
		if (len(self.player_list) == 2):		
			self.begin_game = True
		return str(self.begin_game)


	def next_turn(self, command_details):
		id = 0000
		if command_details is not None:
			self.this_turn = command_details['client_id']
			id = self.this_turn
			#print(f"server.next_turn: Player Turn: {self.this_turn}")
		return id

    # Return row, col and mark in a model change event
	def get_model(self):
		return self.model_event


	#Reset the play state 
	def reset(self):
		self.master_game_state = pd.DataFrame(([[0,0,0],[0,0,0],[0,0,0]])) # A data frame 
		self.player_1 = None  # first player 
		self.player_2 = None  # second player 
		self.whose_turn = None  #which players turn is it? 
		self.previous_turn = None #who played the previous turn? 
		self.winner = None
		self.this_turn = None
		self.registered_player_count = 0 # number of registered players 
		self.begin_game = False 
		#initialize the model_event as a special event client 
		#so can handle early calls to get model state before player registreation
		#client can be smarter to avoid this special case handling
		self.model_event = ModelChangeEvent(-1,-1,"") 
		self.player_list = []

	#update server side data model - single version of truth
	def update_data_model(self, new_data):
		#print("update_data_model")
		
		if(self.begin_game == False):
			return 

		if not type(new_data) == dict:
			print(f"Server.py update_data_model(): data model format error. dict expected, received: {type(new_data)}")
			return 
		
		#print(f"update_data_model {self.whose_turn}")
		#TODO: Prevent same player from playing back to back
		if  new_data['client_id'] == self.player_1.get_id():
			self.whose_turn = self.player_1
		else:
			self.whose_turn = self.player_2


		if((self.previous_turn is not None) and (self.previous_turn.get_id() == self.whose_turn.get_id())):
			#same player is trying to play again, ignore it. 
			print(f"player {self.previous_turn.get_name()} with id {self.previous_turn.get_id()} is attempting to paly out of turn")
			return 

		print(f"current turn for player: {self.whose_turn.get_name()} and client_id: {self.whose_turn.get_id()} and player mark : {self.whose_turn.get_mark()}")

		#update the data frame 
		self.master_game_state.iloc[new_data['row'], new_data['column']] = self.whose_turn.get_mark()

		#create a model event based on changes 
		self.model_event = ModelChangeEvent(new_data['row'], new_data['column'], self.whose_turn.get_mark())

		self.previous_turn = self.whose_turn
		#print(f"update_data_model: model updated: {self.master_game_state}")
		print(f"update_data_model: model event: {self.model_event.to_string()}")


	# Check if we have Tic Tac Toe
	# Return the winning player
	# TODO: This is unnecessarily complex. Simplify using matrix checks
	def checkForWin(self):
		
		#print(f"sever.py - checkForWin...master_game_state: {self.master_game_state}")

		if self.player_1 is not None:
			P1 = self.player_1.get_mark()

		if self.player_2 is not None:
			P2 = self.player_2.get_mark()

		for x in range(3):
			for y in range(1):
				#print(f"Loop1: x: {x}, y: {y}")
				if ( (self.master_game_state.iloc[x,y] == P1) & (self.master_game_state.iloc[x,y+1] == P1) & (self.master_game_state.iloc[x,y+2] == P1)):
					print(f"server.py - checkForWin: Winner is {self.player_1.get_name()}")
					return self.player_1
				if ( (self.master_game_state.iloc[x,y] == P2) & (self.master_game_state.iloc[x,y+1] == P2) & (self.master_game_state.iloc[x,y+2] == P2)):
					print(f"server.py - checkForWin: Winner is {self.player_2.get_name()}")
					return self.player_2

		#Columns
		for y in range(3):
			for x in range(1):
				#print(f"Loop2: x: {x}, y: {y}")
				if ( (self.master_game_state.iloc[x,y] == P1) & (self.master_game_state.iloc[x+1,y] == P1) & (self.master_game_state.iloc[x+2,y] == P1)):
					print(f"server.py - checkForWin: Winner is {self.player_1.get_name()}")
					return self.player_1
				if ( (self.master_game_state.iloc[x,y] == P2) & (self.master_game_state.iloc[x+1,y] == P2) & (self.master_game_state.iloc[x+2,y] == P2)):
					print(f"server.py - checkForWin: Winner is {self.player_2.get_name()}")
					return self.player_2

		x = 0	
		y = 0
		#print(f"Checking Diagonals: x: {x}, y: {y}")
		if ( (self.master_game_state.iloc[x,y] == P1) & (self.master_game_state.iloc[x+1,y+1] == P1) & (self.master_game_state.iloc[x+2,y+2] == P1)):

			print(f"server.py - checkForWin: Winner is {self.player_1.get_name()}")
			return self.player_1
		if ( (self.master_game_state.iloc[x,y+2] == P1) & (self.master_game_state.iloc[x+1,y+1] == P1) & (self.master_game_state.iloc[x+2,y] == P1)):

			print(f"server.py - checkForWin: Winner is {self.player_1.get_name()}")
			return self.player_1

		if ( (self.master_game_state.iloc[x,y] == P2) & (self.master_game_state.iloc[x+1,y+1] == P2) & (self.master_game_state.iloc[x+2,y+2] == P2)):
		
			print(f"server.py - checkForWin: Winner is {self.player_2.get_name()}")
			return self.player_2
		if ( (self.master_game_state.iloc[x,y+2] == P2) & (self.master_game_state.iloc[x+1,y+1] == P2) & (self.master_game_state.iloc[x+2,y] == P2)):

			print(f"server.py - checkForWin: Winner is {self.player_2.get_name()}")
			return self.player_2	

		print(f"server.py - checkForWin: No one Yet")	
		p = (plyr.Player("No Winner", "--", "000", False))
		print(f"server.py checkForWin() : {p.to_string()}")
		return p


if __name__ == "__main__":

	#create a threaded TCP server with a request handler which is instantiated for each client
	server = Server()
	ip, port = server.server_address

	# Start a thread with the server -- that thread will then start one
    # more thread for each request
	server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
	server_thread.setDaemon(True)
	server_thread.start()
	print("Server main loop running in thread:", server_thread.getName())

	#Server simply broadcasts the shared buffer to all clients. 
	#TODO: Brodcast only when there is something new
	while True:
		print(f"Clients:\n {CLIENTS}\n******")
		#BUG : There is a bug that when broadcasting the socket 
		# resets. This works in prototype at https://github.com/nkamkolkar/multithreaded-client-server
		# Needs investigations as to why this is breaking
		#server.broadcast(shared_message)
		time.sleep(5)

	server.shutdown()


