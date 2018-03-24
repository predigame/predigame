# an Inventory of things an actor can use
from pygame.locals import *
from .constants import *
from .Globals import Globals
from functools import partial
from .Thing import *
class Inventory:

    def __init__(self):
        self.things = {}
        self.display_things = {}
        self.title = None
        self.actor = None

    def add(self, thing):
        """ add something to our inventory """
        if thing.name in self.things:
            thing.quantity = self.things[thing.name].quantity
        self.things[thing.name] = thing

    def update(self, delta):
        """ update something """
        for key, dthing in self.display_things.items():
            dthing._update(delta)

    def buy(self, thing, offset, button):
        from . import predigame as p

        if thing.cost == 'n/a':
            return
        if thing.cost <= self.actor.wealth:
            if thing.quantity != 'unlimited':
                thing.quantity += 1
            self.actor.wealth = -1 * thing.cost
            if thing.energy > 0:
                self.actor.energy = thing.energy
        self.display_things['q_' + thing.name].destroy()
        self.display_things['q_' + thing.name] = p.text(thing.quantity, RED, (18, offset))
        self.display_things['p_w'].destroy()
        self.display_things['p_w'] = p.text("{:3d}".format(int(self.actor.wealth)), GREEN, (4,7))
        self.display_things['p_e'].destroy()
        self.display_things['p_e'] = p.text("{:3d}".format(int(self.actor.energy)), GREEN, (4,5))

    def setup(self):
        """ build all the things """
        from . import predigame as p

        if not self.title:
            self.display_things['title'] = p.text('Actor Inventory', YELLOW, (13,1))

        offset = 4
        self.display_things['i'] = p.text('item', BLUE, (12, offset))
        self.display_things['q'] = p.text('quantity', BLUE, (18, offset))
        self.display_things['c'] = p.text('cost', BLUE, (22, offset))
        self.display_things['e'] = p.text('energy', BLUE, (26, offset))
        offset = 5
        for key, thing in sorted(self.things.items()):
            buyit = p.image('buy', RED, (11, offset+0.35))
            self.display_things['b_' + thing.name] = buyit
            self.display_things['n_' + thing.name] = p.text(thing.name, RED, (12, offset))
            self.display_things['q_' + thing.name] = p.text(thing.quantity, RED, (18, offset))
            self.display_things['c_' + thing.name] = p.text(thing.cost, RED, (22, offset))
            self.display_things['e_' + thing.name] = p.text(thing.energy, RED, (26, offset))
            buyit.clicked(partial(self.buy, thing, offset))
            offset += 1

        player = p.actor(self.actor.name, pos=(2,2), size=3)
        player.act(IDLE_FRONT, FOREVER)
        self.display_things['player'] = player
        self.display_things['p_el']= p.text('energy', GREEN, (1, 5))
        self.display_things['p_e'] = p.text("{:3d}".format(int(self.actor.energy)), GREEN, (4,5))
        self.display_things['p_hl'] = p.text('health', GREEN, (1, 6))
        self.display_things['p_h'] = p.text("{:3d}".format(int(self.actor.health)), GREEN, (4,6))
        self.display_things['p_wl'] = p.text('wealth', GREEN, (1, 7))
        self.display_things['p_w'] = p.text("{:3d}".format(int(self.actor.wealth)), GREEN, (4,7))

    def destroy(self):
        """ tear it all down """
        for key, dthing in self.display_things.items():
            dthing.destroy()
        self.display_things = {}
        from . import predigame as p
        p.garbagecollect()

    def draw(self,SURF):
        """ draw the inventory on a surface """
        SURF.fill((0,0,0))
        for key, dthing in self.display_things.items():
            dthing._draw(SURF)

    def __str__(self):
        r = 'Inventory: \n'
        for thing in self.things:
            r += '  ' + str(self.things[thing]) + '\n'
        return r

    def dump_state(self):
        """ extract the things and values """
        d = {}
        for key, thing in self.things.items():
            d[thing.name] = thing.quantity
        return d

    def load_state(self, state):
        """ load quantities from dump state """
        for key, value in state.items():
            if key in self.things:
                self.things[key].quantity = value
