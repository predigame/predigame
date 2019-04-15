# Predigame Levels
from copy import deepcopy
from .Globals import Globals
from .utils import import_plugins

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

def load_levels():
    """
       loads a directory of files that start with the prefix `level`.
       files have a few conventions:

	   a variable `LEVEL` that numbers each game levels

	   a function `completed` that indicates of the objective of the level has been completed

	   a function  `setup` that builds the scene and starts game play

    """
    levels = import_plugins('level')

    #TODO validate Levels
    levels.sort(key=lambda x: x.LEVEL, reverse=False)

    first_level = None
    prev_level = None
    for l in levels:
        print(l)
        next_level = Level()
        next_level.setup = l.setup
        next_level.completed = l.completed

        if first_level is None:
            first_level = prev_level

        if prev_level is not None:
            def def_next():
                return next_level
            prev_level.next = def_next

        prev_level = next_level
        print(l.LEVEL)
    return first_level
