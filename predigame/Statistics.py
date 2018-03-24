# Generic Statistics Class
from pygame.locals import *
from .constants import *
from .Globals import Globals
from functools import partial
from .Thing import *
class Statistics:
    def __init__(self):
        self.dict = {}
        self.display_things = []

    def exists(self, key):
        return key in self.dict

    def add(self, key, value):
        if key not in self.dict:
            self.dict[key] = 0
        self.dict[key] += value

    def get(self, key):
        if key in self.dict:
            return self.dict[key]

    def list(self):
        return self.dict.items()

    def __str__(self):
        return str(self.dict)

    def dump_state(self):
        return self.dict

    def load_state(self, state):
        self.dict = state

    def update(self, delta):
        """ update something """
        for dthing in self.display_things:
            dthing._update(delta)

    def setup(self):
        """ build all the things """
        from . import predigame as p

        self.display_things.append(p.text('Game Statistics', YELLOW, (13,1)))

        offset = 5
        for key, value in sorted(self.dict.items()):
            self.display_things.append(p.text(str(key), RED, (10, offset)))
            self.display_things.append(p.text(str(value), RED, (20, offset)))
            offset += 1

    def draw(self,SURF):
        """ draw the inventory on a surface """
        SURF.fill((0,0,0))
        for dthing in self.display_things:
            dthing._draw(SURF)

    def destroy(self):
        """ tear it all down """
        for dthing in self.display_things:
            dthing.destroy()
        self.display_things = []
        from . import predigame as p
        p.garbagecollect()
