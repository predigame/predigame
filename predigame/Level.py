# Predigame Levels
from copy import copy
from .Globals import Globals
from .utils import import_plugins
import sys

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

	   a function `completed` that indicates if the objective of the level has been completed

	   a function  `setup` that builds the scene and starts game play

    """
    levels = import_plugins('level')
    print('Found and loaded {} levels'.format(len(levels)))
    for l in levels:
       if 'LEVEL' not in l.__dict__:
          sys.exit('ERROR: Level file {} is missing the variable LEVEL'.format(l.__dict__['FILE']))

       if 'setup' not in l.__dict__:
          sys.exit('ERROR: Level file {} is missing the function setup'.format(l.__dict__['FILE']))

       if 'completed' not in l.__dict__:
          sys.exit('ERROR: Level file {} is missing the function completed'.format(l.__dict__['FILE']))
    print('All levels verified for completeness')

    levels.sort(key=lambda x: x.LEVEL, reverse=False)
    #first_level = None
    #prev_level = None
    #for l in levels:
    #    next_level = Level()
    #    next_level.setup = l.setup
    #    next_level.completed = l.completed

    #    if first_level is None:
    #        first_level = next_level

    #    if prev_level is not None:
    #        nl = copy(next_level)
    #        prev_level.next= lambda: nl
    #    prev_level = next_level
    print('Returning {} validated levels of type {}.'.format(len(levels), type(levels)))
    return levels
