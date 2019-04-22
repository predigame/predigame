import random, math, os, sys
from types import ModuleType
from .Globals import Globals
from .Animation import Animation
from .constants import *
from astar import AStar
from functools import partial
from math import ceil
from bresenham import bresenham
import copy

def load_module(path, api):
    src = open(path).read()
    code = compile(src, os.path.basename(path), 'exec', dont_inherit = True)

    name, _ = os.path.splitext(os.path.basename(path))
    mod = ModuleType(name)
    if api is not None:
       mod.__dict__.update(api.__dict__)
    sys.modules[name] = mod

    return code, mod

def import_plugin(plugin_file):
    """ allows other 'plugin' code to be imported into a game. this works a little like load module """
    from . import api
    code, mod = load_module(plugin_file, api)
    exec(code, mod.__dict__)
    mod.__dict__['FILE'] = plugin_file
    return mod

def import_file(plugin_file):
    """ same as `import_plugin` """
    return import_plugin(plugin_file)

def import_plugins(prefix = None):
    """ ones one or more plugins in a given path or with given prefix """
    plugins = []
    files = os.listdir()
    for f in files:
       if prefix is None or f.startswith(prefix):
          plugins.append(import_plugin(f))
    return plugins

def register_cell(pos, s):
    """ helper function that builds the index of all sprites in a given cell """
    area = to_area(s.x, s.y, s.width, s.height)
    for p in area:
        lst = []
        if p in Globals.instance.cells:
            lst = Globals.instance.cells[p]
        else:
            Globals.instance.cells[p] = lst
        lst.append(s)

def register_keydown(key, callback):
    # single key callbacks
    Globals.instance.keys_registered['keydown'][key] = set([callback])
    #if key in Globals.instance.keys_registered['keydown']:
    #    Globals.instance.keys_registered['keydown'][key].add(callback)
    #else:
    #    Globals.instance.keys_registered['keydown'][key] = set([callback])

def register_keyup(key, callback):
    # single key callbacks
    Globals.instance.keys_registered['keyup'][key] = set([callback])

    #if key in Globals.instance.keys_registered['keyup']:
    #    Globals.instance.keys_registered['keyup'][key].add(callback)
    #else:
    #    Globals.instance.keys_registered['keyup'][key] = set([callback])

def has_animation(obj, action=GRAVITY):
    for o in Globals.instance.animations:
        if o.obj == obj and o.action == action:
            return True
    else:
        return False



def get_animation(obj):
    for o in Globals.instance.animations:
        if o.obj == obj:
            return o


def animate(obj, duration = 1, callback = None, abortable=False, action=None, **kwargs):
    Globals.instance.animations.append(Animation(obj, duration, callback, abortable, action, **kwargs))

def at(pos):
    if pos in Globals.instance.cells:
        lst = Globals.instance.cells[pos]
        if len(lst) == 0:
            return None
        elif len(lst) == 1:
            return lst[0]
        else:
            return lst

def to_grid(screen_pos):
    """ converts screen coordinates to grid coordinates """
    if isinstance(screen_pos, list):
        return tuple((int((x / (Globals.instance.GRID_SIZE * 1.0))) for x in screen_pos))
    else:
        return int(screen_pos / (Globals.instance.GRID_SIZE * 1.0))

def to_area(x, y, w, h, bottom_only=False):
    """ takes a upper_left point, width and height and returns full covering area (as list) """
    cover = []
    if bottom_only:
        for i in range(int(ceil(w))):
            cover.append((int(x)+i, int(y+ceil(h)-1)))
    else:
        for i in range(int(ceil(w))):
            for j in range(int(ceil(h))):
                cover.append((int(x)+i, int(y)+j))

    return cover

def is_wall(pos, cells=None):
    """ returns true if a wall is at the desired location, false otherwise """
    atpos = None
    if cells is None:
        atpos = at(pos)
    else:
        atpos = cells
    if atpos is not None:
        if isinstance(atpos, list):
            for x in atpos:
                if x.tag == 'wall':
                    return True
        elif atpos.tag == 'wall':
            return True

    return False

def has_obstacle(lst):
    """ check to see if this list has a sprite that is an obstacle """
    for x in lst:
        if x.tag is not None and x.tag == OBSTACLE:
            return True
    else:
        return False

def max_distance(posA, posB, width, height, skip_up=True):
    """ see if it is possible to move between two points (returns the furthest distance) """
    x, y = posA
    x_dest, y_dest = posB

    cross = list(bresenham(x, y, x_dest, y_dest))[1:]
    x_dest = x_prev = x
    y_dest = y_prev = y
    #print('{} ==> {}'.format(posA, posB))
    #print('cross {}'.format(cross))
    #print('cells {}'.format(Globals.instance.cells))

    for p in cross:
        # see if any the next points will hit an obstacle (coming down)
        next_area = to_area(p[0], p[1], width, height, bottom_only=True)
        #print(' next area {}'.format(next_area))
        clear = True
        if p[1] > y_prev or skip_up is False:
            for pn in next_area:
                if pn in Globals.instance.cells and is_wall(pn, cells=Globals.instance.cells[pn]):
                    #print(' there is something at {}'.format(pn))
                    clear = False
                    break
        if clear:
            x_dest = int(p[0])
            y_dest = int(p[1])
        else:
            break
        x_prev = p[0]
        y_prev = p[1]
    #print('jumping to {}'.format((x_dest,y_dest)))
    return x_dest, y_dest

def get(name):
    if name in Globals.instance.tags:
        return copy.copy(Globals.instance.tags[name])
    else:
        return []

def has_tag(lst, tag):
    """ checks if a list contains a sprite with a given tag """
    if not isinstance(lst, list):
        lst = [lst]
    for l in lst:
        if l.tag == tag:
            return True
    else:
        return False

def rand_pos(x_padding = 0, y_padding = 0, empty=False):
    grid_width = (Globals.instance.WIDTH / Globals.instance.GRID_SIZE) - math.ceil(x_padding)
    grid_height = (Globals.instance.HEIGHT / Globals.instance.GRID_SIZE) - math.ceil(y_padding)
    x = 0
    y = 0
    while True:
        x = random.randrange(0, grid_width)
        y = random.randrange(0, grid_height)

        if len(Globals.instance.sprites) >= grid_width * grid_height:
            break

        if at((x, y)) is None:
            break

    return x, y

def rand_maze(callback):
    from .Maze import Maze
    w = int(Globals.instance.WIDTH/Globals.instance.GRID_SIZE)
    h = int(Globals.instance.HEIGHT/Globals.instance.GRID_SIZE)
    nw = int((w-1)/2)
    nh = int((h-1)/2)
    maze = Maze.generate(nw, nh)
    rows = maze._to_str_matrix()
    for rnum in range(len(rows)):
        row = rows[rnum]
        for cnum in range(len(row)):
            if row[cnum] == 'O':
                s = callback(pos=(cnum,rnum), tag=OBSTACLE)
                register_cell((cnum, rnum), s)

def rand_color():
    r = random.randrange(0, 255)
    g = random.randrange(0, 255)
    b = random.randrange(0, 255)
    #if (r, g, b) == globs.BACKGROUND:
    #    r, g, b = rand_color()
    return r, g, b

def rand_arc():
    p1 = rand_pos(1,4)
    p2 = rand_pos(1,4)
    mid_x = (p1[0] + p2[0]) / 2
    return (p1[0], (Globals.instance.HEIGHT/Globals.instance.GRID_SIZE)+1), (int(mid_x), 1), (p2[0], (Globals.instance.HEIGHT/Globals.instance.GRID_SIZE)+1)

def roundup(num, step):
    return int(math.ceil(num / float(step))) * step

def randrange_float(start, stop, step):
    return random.randint(0, int((stop - start) / step)) * step + start

def sign(num):
    return (1, -1)[num < 0]

def distance(p1, p2):
    return math.sqrt(sum([(a - b) ** 2 for a, b in zip(p1, p2)]))

def visible(p1):
    if p1[0] >= 0 and p1[1] >= 0 and p1[0] < (Globals.instance.WIDTH/Globals.instance.GRID_SIZE) and p1[1] < (Globals.instance.HEIGHT/Globals.instance.GRID_SIZE):
        return True
    else:
        return False

def score_pos(pos = UPPER_LEFT):
    """ return the grid position of the score sprite """
    return {
        UPPER_LEFT : (0.5, 0.5),
        UPPER_RIGHT: ((Globals.instance.WIDTH/Globals.instance.GRID_SIZE) - 0.5, 0.5),
        LOWER_LEFT:  (0.5, (Globals.instance.HEIGHT/Globals.instance.GRID_SIZE) - 1),
        LOWER_RIGHT: ((Globals.instance.WIDTH/Globals.instance.GRID_SIZE) - 0.5, (Globals.instance.HEIGHT/Globals.instance.GRID_SIZE) - 1)
    }.get(pos, UPPER_LEFT)

def sprites():
    """ return a list of all loaded sprites """
    return Globals.instance.sprites

def graze(sprite) :
    """ a sprite.wander() operation. randomly move around """
    x, y = sprite.pos
    choices    = [(x,y), (x, y-1), (x, y+1), (x+1, y), (x-1, y)]
    random.shuffle(choices)
    obstacles  = [at(p) for p in choices]
    visibility = [visible(p) for p in choices]

    for i in range(len(choices)):
        if obstacles[i] is None and visibility[i]:
            if choices[i] != (x, y):
                sprite.move((choices[i][0] - x, choices[i][1] - y))
                break

class __GridSolver__(AStar):
    def __init__(self):
        self.xx = 1

    def heuristic_cost_estimate(self, n1, n2):
        (x1, y1) = n1
        (x2, y2) = n2
        return math.hypot(x2 - x1, y2 - y1)

    def distance_between(self, n1, n2):
        return 1

    def neighbors(self, node):
        x, y = node
        choices = [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
        valid = [visible(p) is True and is_wall(p) is False for p in choices]
        ret = []
        for i in range(len(valid)):
            if valid[i] is True :
               ret.append(choices[i])
        return ret

def track_astar(sprite, find_tags, pabort=-1):
    enemies = []
    for t in find_tags:
       enemies.extend(get(t))

    if len(enemies) == 0:
       sprite.act(IDLE, FOREVER)
       return

    enemy = random.choice(enemies)
    x, y = sprite.pos
    path = __GridSolver__().astar(sprite.pos,enemy.pos)
    if path is not None:
        lst = list(path)
        if len(lst) > 0:
           sprite.move_to(*lst, pabort=pabort)
        else:
           sprite.act(IDLE, FOREVER)
    else:
        sprite.act(IDLE, FOREVER)

def track(sprite, find_tags, pbad = 0.1) :
    """
        a sprite.wander() operation. attempt to a path that moves sprite closer to player_sprite.

        :param sprite: the sprite to automate movements.

        :param find_tags: the tags to track

        :param pbad: the probability to make a bad move. some number of bad moves are needed to

    """

    enemies = []
    for t in find_tags:
       enemies.extend(get(t))

    distances = [distance(e.pos, sprite.pos) for e in enemies]

    enemy = enemies[distances.index(min(distances))]
    x, y = sprite.pos

    choices    = [(x, y), (x, y-1), (x, y+1), (x+1, y), (x-1, y)]
    distances  = [distance(p, enemy.pos) for p in choices]
    visibility = [visible(p) for p in choices]

    best = None
    min_dist = 999999
    for i in range(len(choices)):
        if is_wall(choices[i]) or not visibility[i]:
            continue

        #every now and then make a random "bad" move
        rnd = random.uniform(0, 1)
        if rnd <= pbad:
            best = choices[i]
            break
        elif distances[i] < min_dist:
            best = choices[i]
            min_dist = distances[i]
    if best is not None and best != (x,y):
        sprite.move((best[0] - x, best[1] - y))

def player_physics(action, sprite, vector):
    """ simple physical model that keep a player from walking into obstacles """
    area = []
    if ceil(sprite.width) > 1 or ceil(sprite.height) > 1:
        area = to_area(sprite.x, sprite.y, sprite.width, sprite.height)
    else:
        area.append(sprite.pos)

    # shift each point by the vector
    area = list((x + vector[0], y + vector[1]) for x,y in area)

    for pos in area:
        obj = at(pos)
        if obj and isinstance(obj, list):
            for x in obj:
                if x.tag == OBSTACLE:
                    return False
        elif obj and obj.tag == OBSTACLE:
            return False
        elif not visible(pos):
            return False
    return True

def fill(obj, prob = 1, collide_obj = None, collide_callback = None) :
    """
        fills some amount white space with an object. object can be set to collide with something (collide_obj) in which case a callback would be invoked (collide_callback).

        :param prob: the probability of filling a given square with an object.

        :param obj: a callback (or partial) to a sprite to create in whitespace.

        :param collide_obj: an object or (list of objects) to check for collisions

        :param collide_callback: a callback function to invoke when collide_obj collides with obj.

    """
    for x in range(int(Globals.instance.WIDTH/Globals.instance.GRID_SIZE)):
        for y in range(int(Globals.instance.HEIGHT/Globals.instance.GRID_SIZE)):
             if random.uniform(0, 1) > prob:
                continue
             if at((x,y)) is None:
                o = obj(pos=(x,y))
                if collide_obj and collide_callback:
                    if isinstance(collide_obj, (list, tuple)):
                        for obj in collide_obj:
                            o.collides(obj, collide_callback)
                    else:
                        o.collides(collide_obj, collide_callback)

def load_state(actor, sfile):
    """
        save the state of an actor in an encoded file

        :param actor: actor class reference to load state into

        :param sfile: encoded file containing state information
    """
    import os.path, json, base64
    if os.path.isfile(sfile):
        state_file = open(sfile, 'rb')
        state = json.loads(base64.b64decode(state_file.read()).decode("ascii"))
        actor.load_state(state)
        return True
    return False

def save_state(actor, sfile):
    """
        loads previously saved actor state from encoded file

        :param actor: actor class to dump state from

        :param sfile: encoded file used to write state information
    """
    import json, base64
    state_file = open(sfile, 'wb')
    state_file.write(base64.b64encode(json.dumps(actor.dump_state()).encode()))

def vadd(x,y):
    return [x[0]+y[0],x[1]+y[1]]

def vsub(x,y):
    return [x[0]-y[0],x[1]-y[1]]

def vdot(x,y):
    return x[0]*y[0]+x[1]*y[1]
