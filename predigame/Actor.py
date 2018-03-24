import sys, random, math, pygame
from time import time
from .Sprite import Sprite
from .constants import *
from .Globals import Globals
from .utils import at, get, is_wall
from .Inventory import *
from functools import partial

# actor class for four directional movement
class Actor(Sprite):
    MAX_WEALTH = 500000
    def __init__(self, actions, rect, tag=None, abortable=False, name=None):
        # - scale images
        self.actions = {}
        for action in actions:
            self.actions[action] = []
            for img in actions[action]:
                img = img.convert_alpha()
                img = pygame.transform.scale(img, rect.size)
                self.actions[action].append(img)

        self.index = 0
        self.action_iterations = 0
        self.action = IDLE
        self.action_loop = FOREVER

        self._stop = False
        self.frame_count = 0
        self.frame_rate = 1
        self.prev_vector = None
        self.direction = LEFT

        self._defend = None
        self._health = 100.0
        self._wealth = 500.0
        self._energy = 100.0
        self._inventory = None

        if tag is not None and tag in Globals.cache:
            self._inventory = Globals.cache[tag]
        else:
            self._inventory = Inventory()
            Globals.cache[tag] = self._inventory
        self._inventory.actor = self

        surface = actions[self.action][self.index]
        Sprite.__init__(self, surface, rect, tag, abortable, name)

    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, value):
        if value >= 0 and value < 100:
            self._health = value
        if self.health == 0:
            self.act(DIE, loop=1)

    @property
    def energy(self):
        return self._energy

    @energy.setter
    def energy(self, value):
        self._energy += value
        if self._energy < 0: self._energy = 0
        if self._energy > 100: self._energy = 100

    @property
    def wealth(self):
        return self._wealth

    @wealth.setter
    def wealth(self, value):
        self._wealth += value
        if self._wealth > Actor.MAX_WEALTH: self._wealth = Actor.MAX_WEALTH

    @property
    def defend(self):
        return self._defend

    @defend.setter
    def defend(self, callback):
        self._defend = callback

    def stop(self):
        self._stop = True

    def move(self, vector, **kwargs):

        if self.health == 0:
            return

        direction = LEFT
        if vector[0] == 1:
            direction = RIGHT
        elif vector[0] == -1:
            direction = LEFT
        elif vector[1] == 1:
            direction = FRONT
        elif vector[1] == -1:
            direction = BACK

        if direction != self.direction:
            self.index = 0

        self.direction = direction

        self.act(WALK + '_' + direction, FOREVER)
        Sprite.move(self, vector, **kwargs)

    def move_to(self, *points, **kwargs):
        callback = kwargs.get('callback', None)
        pabort = kwargs.get('pabort', -1)

        if self._stop:
           self._stop = False
        elif len(points) == 0:
           self.act(IDLE, FOREVER)
        elif random.uniform(0, 1) <= pabort:
           self.act(IDLE, FOREVER)
        else:
           if len(points) > 1:
              head, *tail = points
              if is_wall(head):
                 self.act(IDLE, FOREVER)
              else:
                 self.move((head[0]-self.x, head[1]-self.y), callback=partial(self.move_to, *tail, **kwargs))
           else:
              head = points[0]
              if is_wall(head):
                 self.act(IDLE, FOREVER)
              else:
                 if callback is not None:
                    self.move((head[0]-self.x, head[1]-self.y), callback=callback)
                 else:
                    self.move((head[0]-self.x, head[1]-self.y), callback=partial(self.act, IDLE, FOREVER))

    def _complete_move(self, callback = None):
        if self.health == 0:
            return

        self.act(IDLE + '_' + self.direction, FOREVER)
        Sprite._complete_move(self, callback)

    def _update(self, delta):

        # check to see if we need to activate self defense
        if self._defend is not None:
            self._defend(self)

        img = self.actions[self.action][self.index]
        self.surface = img
        self.origin_surface = img
        Sprite._update(self, delta)
        if self.action_loop == FOREVER or self.action_iterations < self.action_loop:
            self.frame_count = self.frame_count + 1
            if self.frame_count >= self.frame_rate:
                self.index = self.index + 1
                self.frame_count = 0
            if self.index >= len(self.actions[self.action]):
                self.action_iterations = self.action_iterations + 1
                if self.action_loop == FOREVER or self.action_iterations < self.action_loop:
                    self.index = 0
                else:
                    self.index = self.index - 1
        elif self.health > 0:
            self.index = 0
            self.action = IDLE + '_' + self.direction
            self.action_loop = FOREVER

    def get_actions(self):
        """ return all actions that this actor can perform """
        return list(self.actions.keys())


    def take(self, obj):
        """ take this object and add to inventory """
        self._inventory.add(obj)
        obj.actor = self
        return self

    # TODO: this needs to be merged with act
    def actit(self, action, loop=FOREVER):
        if not action in self.actions:
            print('Unsupported action ' + str(action) + '. Going to IDLE')
            self.act(IDLE, loop)
            return self
            #print('Unsupported action ' + str(action) + '. Valid options are:')
            #for action in self.actions:
            #    print(action.upper())
            #sys.exit(0)
        self.index = 0
        self.action = action
        self.action_loop = loop
        self.action_iterations = 0
        return self

    def act(self, action, loop=FOREVER):
        if self.health > 0 or action.startswith(DIE):
            if action in self.actions:
                self.actit(action, loop)
            else:
                # infer the action based on direction
                if str(action + '_' + self.direction) in self.actions:
                    self.actit(str(action + '_' + self.direction), loop)
                else:
                    self.actit(action, loop)
        return self

    def kill(self, delay=1.25):
        """ used to kill this actor """
        if self.health > 0:
            self.health = 0
            self.destruct(delay)

    def rate(self, frame_rate):
        """ the rate to swap animation frames, default is 1 per update call """
        if frame_rate < 0:
            frame_rate = 1
        if frame_rate > 60:
            frame_rate = 60
        self.frame_rate = frame_rate
        return self

    def facing(self, distance=100):
        """ returns a position (off the screen) where this actor is facing """
        if self.direction == BACK:
            return self.x, self.y - distance
        elif self.direction == FRONT:
            return self.x, self.y + distance
        elif self.direction == LEFT:
            return self.x - distance, self.y
        elif self.direction == RIGHT:
            return distance + self.x, self.y

    def next(self):
        return next(self.direction)

    def next(self, direction):
        """ the next position (in the current direction or relative board position) """
        if direction == BACK:
            return self.x, self.y - 1
        elif direction == FRONT:
            return self.x, self.y + 1
        elif direction == LEFT:
            return self.x - 1, self.y
        elif direction == RIGHT:
            return self.x + 1, self.y

    def _check_next_object(self, pos):
        lst = at(pos)
        if lst is not None:
            if isinstance(lst, list):
                for x in lst:
                    if x != self and isinstance(x, Actor):
                        if x.health > 0:
                            return x
                    elif x != self and isinstance(x, Sprite):
                        return x
            elif lst != self and isinstance(lst, Actor):
                if lst.health > 0:
                    return lst
            elif lst != self and isinstance(lst, Sprite):
                return lst

    def next_object(self, direction=None, distance=50):
        """ returns the next thing along the path where this actor is facing,
            up to a certain distance. if the next thing is an Actor, it must be alive.
        """
        if direction is None: direction = self.direction
        if direction == BACK:
            for y in range(self.y, self.y - distance, -1):
                obj = self._check_next_object((self.x, y))
                if obj is not None:
                    return obj
        elif direction == FRONT:
            for y in range(self.y, self.y + distance, 1):
                obj = self._check_next_object((self.x, y))
                if obj is not None:
                    return obj
        elif direction == LEFT:
            for x in range(self.x, self.x - distance, -1):
                obj = self._check_next_object((x, self.y))
                if obj is not None:
                    return obj
        elif direction == RIGHT:
            for x in range(self.x+1, self.x + distance, 1):
                obj = self._check_next_object((x, self.y))
                if obj is not None:
                    return obj

    def dump_state(self):
        """ extract wealth, health, energy, inventory """
        d = {}
        d['wealth'] = self._wealth
        d['health'] = self._health
        d['energy'] = self._energy
        d['inventory'] = self._inventory.dump_state()
        return d

    def load_state(self, state):
        """ load saved state values """
        if 'wealth' in state:
            self._wealth = state['wealth']
        if 'health' in state:
            self._health = state['health']
        if 'energy' in state:
            self._energy = state['energy']
        if 'inventory' in state:
            self._inventory.load_state(state['inventory'])
