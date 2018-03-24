# Predigame Levels
from copy import deepcopy
from .Globals import Globals
class Level:
	def __init__(self):
		self.globals = None

	def setup(self):
		""" setup all the sprites needed for this level """
		raise NotImplementedError('Level.setup() cannot be called directly')

	def completed(self):
		""" execute an objective function to determine if this level is complete """
		return False

	def next(self):
		""" return the next level """
		return None
