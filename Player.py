########################################################################
# Class : Player represents a player in the game. Uniquely identified 
# by a client ID created by the client, holds additional attributes 
# for a the player. 
#
# @author: Neelesh Kamkolkar
########################################################################		


class Player:
	def __init__(self, name, mark, id, isRegistered):
		self.name = name
		self.mark = mark
		self.id = id
		self.isRegistered = isRegistered

	def set_name(self, new_name):
		self.name = new_name 

	def get_name(self):
		return self.name

	#The mark current is an "X" or "O"
	#Future versions could support custom icons etc. 
	def set_mark(self, new_mark):
		self.mark = new_mark 

	def get_mark(self):
		return self.mark 	

	def set_id(self, new_id):
		#can set only once. 
		if(self.id == -1111):
			self.id = new_id 

	def get_id(self):
		return self.id 	

	def register_player(self):
		self.isRegistered = True

	def un_register_player(self):
		self.isRegistered = False

	def get_reg_status(self):
		return self.isRegistered

	def to_string(self):
		msg = {"id" : str(self.get_id()), "name":self.get_name(), "mark": self.get_mark(),  "is_registered" : str(self.get_reg_status())}
		return msg



