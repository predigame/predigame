# something an Actor can use
from functools import partial
from .utils import register_keydown as keydown, at, get, has_tag, sprites
from .constants import *

class Thing:
    def __init__(self, call=None):
        self.name = None
        self.image = None
        self.lethality = 100
        self.energy = 1
        self.quantity = 1
        self.actor = None
        self.cost = 1000

        if call is not None:
            keydown(call, self.use)

    def use(self):
        raise NotImplementedError('base class cannot be called directly')

    def __str__(self):
        return '{} {}'.format(self.name, self.quantity)
