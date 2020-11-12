
import tkinter as tk
import pandas as pd 
from tkinter import messagebox
import Client as NC
import json
import Board as T3Board
import queue 
import threading
import time
from Config import Protocol


########################################################################
# Class : GameController 
# @author: Neelesh Kamkolkar
#  
########################################################################

"""
	Provides command and control between GUI and the backend data model on server 

	Design Goal: status for UI needs to be updated as the remote players update the state 
	of the board. The polling network calls shall be done asyncrhonously in a separate thread outside 
	the main GUI thread so the player GUI is not blocked. This is done  via a queue for polling requests 
		1. self.recv_from_server_queue : polling queue - command/data coming back from server

	The server writes are done on the GUI thread as they are light weight and allow a responsive UX

	Design Choice: Choosing a polling mechanism for this simple 2 player game for simplicity. This makes 
	the application a bit chatty, but provides a good user experience where the player 
	always sees the shared state of the game across the remote players. The alternate was to do 
	server notifications to all clients (aka broadcast). This added complexity and additional UX than the original
	goal of this exercise called for.

"""

class GameController():

	def __init__(self):
		self.player_turn = True  #Is it my turn?
		self.player_name = None  #The name user types in to register. The UI updates this field 
		self.player_mark = ""    #The player mark. Defaults assigned in server. Read on client side
		self.winner = "NO_ONE"   #Who is the winner of this game? 
		self.in_progress = False #Is the game ready to be played or are we waiting for players to arrive?
		self.game_over = False   #Is the game over? 

		# Client should know which player it is so it can update the UI with the correct marks
		self.isPlayerRegistered = False  
		self.server_state = None
		self.recv_from_server_queue = queue.Queue()


	"""
	start_Game: create the board, create the network proxy to communicate with server 
	and launch the UI and the network client proxy. 
	"""
	def start_Game(self):
		self.root = tk.Tk()
		self.gameBoard = T3Board.Board(self.root, self, 3, 3)
		self.game_server = NC.GameNetworkClient(self) #pass in the controller
		self.game_server.start()
		self.running = 1
		self.iothread = threading.Thread(target=self.processMessages)
		self.iothread.start()
		self.periodicCall()
		self.gameBoard.mainloop()
	

	def reset_Game(self):
		self.player_turn = True
		self.player_name = None
		self.isPlayerRegistered = False 
		self.winner = "NO_ONE"
		self.in_progress = False
		self.game_over = False
		self.server_state = None
		self.recv_from_server_queue = queue.Queue()
		self.game_server.reset() #reset server state
		self.gameBoard.init_Board(3, 3) #reset board
		self.running = 1
		self.iothread = threading.Thread(target=self.processMessages)
		self.iothread.start()
		self.periodicCall()	


	def exitApplication(self):
		self.running = 0
		self.master.destroy()


	"""
	processMessage: while the player doesn't quit and there is no win,
	do asynch poll to server to get model state and 
	add a message in queue to allow UI thread to pick up work to update 
	UI to reflect up to date model state on the server state 

	"""
	def processMessages(self):
		msg = " .. "
		#print(f"thread: processMessage()")
		while self.running: 
			if(not self.in_progress): # less chatty to cache the in_progress state in UI
				r = self.game_server.check_for_ready()
				#print(f"processMessages() : &&&&&&&&&&& check_for_ready r : {r} r.type: {type(r)}")				
				if(r == 'True'):
					print(f"game started, please play....")
					#cache the game state
					self.in_progress = True 
				else: 
					#cache the game state
					self.in_progress = False
					print(f"waiting for players to register....")
			else:
				print("Checking for winner.....")		
				win = self.game_server.check_for_win()
				if(len(win) > 0):
					#we got a winner name send this to the UI thread 
					msg = {"check_for_win":win}	
					self.put_msg_recv_from_server_queue(msg)

				res = self.game_server.get_model()
				#print(f"processMessage() : got model update from server: {res} type: {type(res)}")
				if(res is not None):
					cmp = b'["0", "0", ""]'
					if(res != cmp): #Ignore the first state check (bug)
						msg = {"get_model":res}	
						#print(f"got model event: adding to queue: {msg}::{type(msg)}")
						self.put_msg_recv_from_server_queue(msg)		
					else:
						pass
						#print("DEBUG: ignore first check failed")
				else:
					pass
					#print(f"DEBUG2 ***** {res}")
		
			time.sleep(2)

	"""
	From the UI, do a periodic call in the GUI thread to process any command/data from server
	"""
	def periodicCall(self):
		"""
		Check every 500 ms if there is something new in the queue.
		"""
		self.gameBoard.update_UI()
		if not self.running:
			# we don't expect this unless the player presses "Quit"
			import sys
			sys.exit(1)
		self.gameBoard.after(500, self.periodicCall)



	"""
	get/put methods for the "recv_to_server_queue"
	this queue has messages from the asych IO 
	thread that is reading server state and polling

	"""
	def get_msg_recv_from_server_queue(self):
		msg = None 
		try:
			msg = self.recv_from_server_queue.get(0)
			#print(f"recv_from_server_queue : {msg}")
		except queue.Empty:
			#print("recv_from_server_queue is empty")
			pass

		return msg

	def put_msg_recv_from_server_queue(self, msg):
		self.recv_from_server_queue.put(msg)
		#print(f"PUT_msg_recv_from_server_queue : {msg}")


	#update the complete game state including server. 
	def update_GameState(self, row, col):
		#print(f"main.update_GameState: start")
		if(self.in_progress):
			self.game_server.update_model(self.gameBoard.get_PlayerName(), row, col)
			#print(f"main.update_GameState: {self.gameBoard.get_PlayerName()} turn completed")
		else:
			print("update_GameState(): waiting for players...not calling backend")

		

	def register_user(self, name):
		#print(f"main.py: register_user name: {name}")
		res = self.game_server.check_for_ready()
		#print(f"*********checking if server is ready {res} type: {type(res)}")
		if(res == 'False'):
			#print(f"main.py: register_user(): calling server register_user")
			self.player_mark = self.game_server.register_user(name)
			print(f"Player {name} is registered with server. Your player_mark is {self.player_mark}")
			self.player_turn = True 
		else: 
			print(f"main.py: register_user failed - reset game: {name} ")

	def is_game_over(self):
		return self.is_game_over

	#Get the player marks (TODO: State is already on server, get it once at start/reset)
	def get_player_mark(self):
		return self.player_mark 

gc = GameController()
gc.start_Game()





