
import tkinter as tk
import pandas as pd 
from tkinter import messagebox
import Client as NC
import json
from tkinter import StringVar
import queue


########################################################################
# Class : Board extends tk.Frame 
# @author: Neelesh Kamkolkar
########################################################################		

"""
The Board contains a player name and registration capability 
In addition it contains an active play area consisting of buttons.
This is a grid of NxN (3x3) in this case where a player can chose to place their mark. 
The active play grid is disabled until there are enough players registered to play a game. 
The active play grid is enabled when there are enough players (2) for TicTacToe 
The Board also gives the player the abiltiy to "Reset" a completed game so they can restart the game.
The Board also gives the player the abiltiy to Quit the game which cleans up all the resources

TODO: Improvements/Bugs - each client should track their turn and the active play grid should 
disable itself after a users turn is completed so multiple back to back plays by same player are 
not possible. Currently, this is allowed although the server checks for this, clients don't handle in UI

"""
class Board(tk.Frame):
	
	def __init__(self, master=None, game_controller=None, rows=3, cols=3):
		super().__init__(master)
		self.controller = game_controller
		self.master.title("TicTacToe")
		self.row_count = rows
		self.col_count = cols
		self.init_Board(self.row_count, self.col_count)
		self.pack(fill='both')		

	"""
	initialize the board. 
	"""

	def init_Board(self, row_count, col_count):
		#Some userfriendly messaging and name gathering
		#print(f"Board.init_Board(): ")
		self.var_player = StringVar()	
		self.button_grid = {}
		self.controller.game_over=False
		#Flag to optimize refresh of playgrid only once afte game ready
		self.active_playgrid_updated = False 

		self.helpText = "Enter name, Play to begin"
		self.lbl = tk.Label(self, text="Welcome To Tic Tac Toe!")
		self.lbl.grid(row=0, column=1, sticky='NWSE')

		self.lbl_player = tk.Label(self, text="Player Name:")
		self.lbl_player.grid(row=1, column=0, sticky='W')		
		self.txt_player_name = tk.Entry(self, textvariable=self.var_player)
		self.txt_player_name.grid(row=1, column=1, sticky='NWSE')
		self.var_player.set(self.helpText)

		#create a 3x3 grid of buttons for active play area
		self.active_playgrid = self.create_active_playgrid()
		self.active_playgrid.grid(row=3, column=1)
		self.update_active_play_grid()
	
		self.goBtn = tk.Button(self, text="  Play ", height=2, width=8, bg='black', fg='green', command=self.get_PlayerName)
		self.goBtn.grid(row=1, column=2)

		self.quitBtn = tk.Button(self, text="Quit!", height=2, width=8, bg='black', fg='red', command=self.exitApp)
		self.quitBtn.grid(row=7, column=1, stick="NWSE")
	
		self.restartBtn = tk.Button(self, text="Reset", height=2, width=8, fg='orange', command=self.controller.reset_Game)
		self.restartBtn.grid(row=6, column=1, sticky="NWSE")
	

	def get_PlayerName(self):
		#print(f"main.get_Players(): P1: {self.controller.player_name}")
		self.controller.player_name = self.txt_player_name.get()
		if(not self.controller.isPlayerRegistered):
			self.controller.register_user(self.controller.player_name)
			self.controller.isPlayerRegistered = True
		#print(f"get_PlayerName(): {self.txt_player_name.get()}")

		
	
	"""
	exitApp : ensure the worker threads are stopped and destroy the main app window 
	"""
	def exitApp(self):
		self.controller.running = 0
		self.master.destroy()

	
	#state can be "normal" or "disabled"
	#update_board disables or enables the active button grid
	#to allow players to play when it is their turn
	def update_active_play_grid(self):
		if (self.controller.in_progress):
			state = "normal"
		else:
			state = "disabled"

		for r in ['0', '1', '2']:
			row_btns = self.button_grid.get(r)
			if(row_btns):
				for c in ['0', '1', '2']:
					this_btn = row_btns.get(c)
					#print(f"update_board %%%%%%%%%%%% this_btn.type : {type(this_btn)}")
					if(isinstance(this_btn, tictac_square)):
						#print(f"update_board %%%%%%%%%%%% {state} btn at: ({r},{c})")
						this_btn["state"] = state
					else:
						print(f"update_board : BUG {this_btn}")

					
	#update UI 
	def update_UI(self):
		#print(f"gameBoard: update_UI(): entering. QSize: {self.controller.recv_from_server_queue.qsize()}")

		#Locally manage UI state
		if(not self.controller.in_progress):
			#nothing to update
			#print(f"update_UI() nothing to update: {self.controller.in_progress}")
			return
		else: 
			#once there are two registered players and game state is ready, enable the active play grid
			if(self.active_playgrid_updated == False):
				self.update_active_play_grid()
				#we want to update the active grid only once, flip the flag to avoid repainting
				self.active_playgrid_updated = True
	
		if(self.controller.game_over == True):		
			print("GAME OVER")
			tk.messagebox.showinfo("TicTacToe - Game Over", "Winner is: " + self.controller.winner + "! Congratulations! Game will now reset")
			self.controller.reset_Game()
			return
			
		## While there are messages from the Asynch IO thread, process them 
		## and react to messages by updating UI components.
		while (self.controller.recv_from_server_queue.qsize()):
			try:
				msg = self.controller.recv_from_server_queue.get(0)
				#print(f"******updateUI(): command: {msg} : type: {type(msg)}")
				
				#we expect a dict of function and result 
				#eg: {check_for_win: "winner_name"}
				#eg: {"get_model":([0], [4], [X])} See function for details of return value
				if isinstance(msg, dict):
					for key in msg:
						if key == "get_model":
							#update UI state given model changes from server
							self.controller.server_state = msg[key]
							if(self.controller.server_state is None):
								print(f"gameBoard: update_UI(): check if server is running")
								return

							if(self.controller.server_state is not None):
								print(f"update_UI: Server returned model change at {(self.controller.server_state)}")
								#self.controller.server_state = json.loads(self.controller.server_state)
								#print(f"update_UI() ModeChangeEvent.Type: {type(self.controller.server_state)}")
							else:
								pass
								#print(f"update_UI: Server returned no change in data model")

							#build a tuple from server state of (row, column, mark) for comparison
							source = (self.controller.server_state[0], self.controller.server_state[1])
							remote_player_mark = self.controller.server_state[2]	
					
							#magic number 
							if(source == (-1, -1)):
								print(f"MODEL_EVENT: No changes to model to update. Skipping...")
								return
							
							#button_grid is a dict of dicts. 
							#print(f"button_grid : {self.button_grid}")
							#find the button in the button grid for which 
							#there is a model update event from the server
							#update the state of the button in UI so all 
							#users see the current state of the board after
							#any remote play
							for r in ['0', '1', '2']:
								row_btns = self.button_grid.get(r)
								if(row_btns):
									for c in ['0', '1', '2']:
										this_btn = row_btns.get(c)
										#print(f"%%%%%%%%%%%%  found btn: {this_btn}")
										if(isinstance(this_btn, tictac_square)):
											id = this_btn.get_id()
											#print(f"%%%%%%%%%%%%%  button id: {id} : source: {source}")
											if (id == source ):
												#print(f"%%%%%%%%%%%%%  FOUND a button that matches the grid source {id}")
												this_btn["text"] = remote_player_mark 
												this_btn.set_mark(remote_player_mark)
												this_btn["state"] = "disabled"
										
							#print(f"gameBoard: update_UI(): : {self.controller.server_state}")
							#print(f"gameBoard: update_UI() exiting")
						elif key=="check_for_win":
							if(self.controller.game_over == True):
								print("GAME OVER")
								self.winner_name = str(msg[key])
								self.controller.running = 0
						else:
							print("ERROR in UI/NETWORK QUEUE MESSAGE")	


			except queue.Empty:
				print("queue is empty")
				pass



	"""
	create the active play grid. For TicTacToe this is a 3x3 grid of buttons
	top row has 3 buttons. 
	middle row has 3 buttons
	bottom row has 3 buttons

	This layout is important to coincide with the data model data structure which is 
	a 3x3 matrix. 

	"""

	def create_active_playgrid(self):

		#Initialize the interactive play area button grid 
		active_playgrid = tk.Frame(self)

		top_frame = tk.Frame(active_playgrid)
		top_frame.grid(row=3, column=1)


		row_count  = 3
		col_count = 3	

		x=0
		row = {}
		for y in range(col_count):
			#(0,1)(0,2)(0,3)
			btn = tictac_square(top_frame, x, y, self.controller)
			btn.grid(row=3, column=y)
			row[str(y)] = btn	
		self.button_grid[str(x)] = row


		middle_frame = tk.Frame(active_playgrid)
		middle_frame.grid(row=4, column=1)
		x = 1
		row = {}
		for y in range(col_count):
			#(1,0)(1,1)(1,2)
			btn = tictac_square(middle_frame, x, y, self.controller)
			btn.grid(row=4, column=y)
			row[str(y)] = btn	
		self.button_grid[str(x)] = row

		bottom_frame = tk.Frame(active_playgrid)
		bottom_frame.grid(row=5, column=1)
		x=2
		row = {}
		for y in range(col_count):
			#(2,0)(2,1)(2,2)
			btn = tictac_square(bottom_frame, x, y, self.controller)
			btn.grid(row=5, column=y)
			row[str(y)] = btn	
		self.button_grid[str(x)] = row	


		return active_playgrid

########################################################################
# Class : tictac_square extends a Tkinter Button 
# This button uses a mark to select the players tic tac toe plays
# and disables it self once the button is clicked preventing another
# turn
########################################################################
class tictac_square(tk.Button):
   
    def __init__(self, parent, row, col, game_controller):
        super().__init__(parent)
        self.root = parent
        self["height"] = 3
        self["width"] = 8
        self["text"] = "___"  # what is displayed on button 
        self["command"] = self.on_click
        self["state"] = "disabled"  #disabling button until play can start with remote player
        self.row = row
        self.column = col 
        self.controller = game_controller
        self.mark = "88" 		# a player's mark can change 
        self.id = (str(self.row), str(self.column))

    def set_mark(self, mark):
    	self.mark = mark 
    	self["text"] = self.mark  

    def get_mark(self):
    	return self.mark

    def to_string(self):
    	return "mark: " + str(self.mark) + " " + self["text"] + " at (r:c): " + str(self.row) + str(self.column)

    def get_id(self):
    	#print(f"tictac_square id: {id}")
    	return self.id

    def on_click(self):
        if self["text"] == "___":
            self["text"] = self.controller.get_player_mark()
            self["state"] = "disabled"


        #print(f"tictac_square.on_click(): player commited spot: {self.row}x{self.column} with {self.mark} and is now {self['state']}") 
        self.controller.update_GameState(self.row, self.column)
