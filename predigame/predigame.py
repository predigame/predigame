import sys, os, random, datetime, mimetypes, pygame, json
from numbers import Number
from functools import partial
from time import time as get_time, gmtime, strftime
from pygame.locals import *
from .Globals import Globals
from .utils import load_module, register_cell, register_keydown, rand_maze, rand_pos, rand_color, roundup, animate, score_pos
from .Sprite import Sprite
from .Actor import Actor
from .Level import Level
from .constants import *
import traceback
import io
from zipfile import ZipFile

current_level = None
globs = None
show_grid = False
update_game = True
game_over = False
sounds = {}
images = {}
actors = {}
callbacks = []
DEFAULT_COLOR = (220, 220, 220)
_background_color = _background = DEFAULT_COLOR
DISPLAY_MAIN = '__main__'
displays = {}
display_active = DISPLAY_MAIN

def background(bg = None):
    """ set the background color or image """
    global _background, _background_color
    _background = None
    if bg is None:
        from urllib.request import urlopen
        import io
        image_str = urlopen('http://picsum.photos/'+str(WIDTH)+'/'+str(HEIGHT)+'/?random').read()
        image_file = io.BytesIO(image_str)
        _background = pygame.image.load(image_file).convert()
        return

    if isinstance(bg, str):
        for ext in ['png', 'jpg', 'gif']:
            fname = 'backgrounds/' + bg + '.' + ext
            if os.path.isfile(fname):
                _background = pygame.image.load(fname).convert()
                break
        if _background is None:
            sys.exit('Background image doesn\'t exist. File must be saved in backgounds directory: ' + bg)
        else:
            #size background to fix screen
            _background = pygame.transform.scale(_background, (WIDTH, HEIGHT))
    else :
        _background = _background_color = bg

def display(eventkey, name, wrapper=None):
    """ create a new pygame drawing surface that is triggered when eventkey is pressed.
        any active game is paused when the display is swapped """

    if FULLSCREEN:
        surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
    else:
        surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF | pygame.HWSURFACE)
    surface.fill((0, 0, 0))

    displays[name] = (surface, wrapper)

    if eventkey is not None:
        register_keydown(eventkey, partial(_display_swap, name))

    return surface

def _display_swap(name) :
    """ used to swap display surfaces. pauses any active game """
    global display_active, update_game

    if display_active == name:
        # swap to main
        displays[name][1].destroy()
        display_active = DISPLAY_MAIN
        update_game = not update_game
    else:
        if display_active != DISPLAY_MAIN:
            displays[display_active][1].destroy()
        # swap to something else
        if display_active == DISPLAY_MAIN:
            update_game = not update_game
        display_active = name
        displays[name][1].setup()


def init(path, width = 800, height = 800, title = 'Predigame', bg = (220, 220, 220), fullscreen = False, **kwargs):
    global globs, RUN_PATH, WIDTH, HEIGHT, FPS, GRID_SIZE, SURF, FULLSCREEN, clock, start_time, sounds

    RUN_PATH = path
    WIDTH, HEIGHT = width, height
    FPS = kwargs.get('fps', 60)
    GRID_SIZE = kwargs.get('grid', 50)
    FULLSCREEN = fullscreen
    pygame.mixer.pre_init(22050, -16, 2, 1024) # sound delay fix
    pygame.init()
    pygame.display.set_caption(title)
    SURF = display(None, DISPLAY_MAIN)
    clock = pygame.time.Clock()

    background(bg)

    globs = Globals(WIDTH, HEIGHT, GRID_SIZE)
    Globals.instance = globs



    loading_font = pygame.font.Font(None, 72)
    SURF.blit(loading_font.render('LOADING...', True, (235, 235, 235)), (25, 25))
    pygame.display.update()

    images['__error__'] = pygame.image.load(os.path.join(os.path.dirname(__file__), 'images', 'error.png'))
    images['__screenshot__'] = pygame.image.load(os.path.join(os.path.dirname(__file__), 'images', 'screenshot.png'))

    start_time = get_time()



def _create_image(name, pos, center, size, tag):
    img = images[name]
    rect = img.get_rect()
    new_width = 0
    new_height = 0
    if size > Globals.MAX_SIZE:
        size = Globals.MAX_SIZE
    if rect.width >= rect.height:
        new_width = size * float(globs.GRID_SIZE)
        new_height = rect.height * (new_width / rect.width)
    elif rect.width < rect.height:
        new_height = size * float(globs.GRID_SIZE)
        new_width = rect.width * (new_height / rect.height)
    rect.size = new_width, new_height
    if center is not None:
        rect.topleft = (center[0] * float(globs.GRID_SIZE)) - rect.width/2.0, (center[1] * float(globs.GRID_SIZE)) - rect.height/2.0
    else:
        rect.topleft = pos[0] * float(globs.GRID_SIZE), pos[1] * float(globs.GRID_SIZE)

    s = Sprite(img, rect, tag, name=name)
    return s

def _create_actor(actions, name, pos, center, size, abortable, tag):
    img = actions['idle'][0]
    rect = img.get_rect()
    new_width = 0
    new_height = 0
    if rect.width >= rect.height:
        new_width = size * float(globs.GRID_SIZE)
        new_height = rect.height * (new_width / rect.width)
    elif rect.width < rect.height:
        new_height = size * float(globs.GRID_SIZE)
        new_width = rect.width * (new_height / rect.height)
    rect.size = new_width, new_height
    if center is not None:
        rect.topleft = (center[0] * float(globs.GRID_SIZE)) - rect.width/2.0, (center[1] * float(globs.GRID_SIZE)) - rect.height/2.0
    else:
        rect.topleft = pos[0] * float(globs.GRID_SIZE), pos[1] * float(globs.GRID_SIZE)

    s = Actor(actions, rect, tag, abortable, name=name)
    return s

def _create_rectangle(color, pos, size, outline, tag):
    rect = pygame.Rect(pos[0] * globs.GRID_SIZE, pos[1] * globs.GRID_SIZE, size[0] * globs.GRID_SIZE, size[1] * globs.GRID_SIZE)
    surface = pygame.Surface(rect.size)
    surface.fill(_background_color)
    surface.set_colorkey(_background_color)
    pygame.draw.rect(surface, color, (0, 0, rect.width, rect.height), outline)

    return Sprite(surface, rect, tag)

def _create_circle(color, pos, size, outline, tag):
    rect = pygame.Rect(pos[0] * globs.GRID_SIZE, pos[1] * globs.GRID_SIZE, size * globs.GRID_SIZE, size * globs.GRID_SIZE)
    surface = pygame.Surface(rect.size)
    surface.fill(_background_color)
    surface.set_colorkey(_background_color)
    pygame.draw.circle(surface, color, (rect.width // 2, rect.height // 2), rect.width // 2, outline)

    return Sprite(surface, rect, tag)

def _create_ellipse(color, pos, size, outline, tag):
    rect = pygame.Rect(pos[0] * globs.GRID_SIZE, pos[1] * globs.GRID_SIZE, size[0] * globs.GRID_SIZE, size[1] * globs.GRID_SIZE)
    surface = pygame.Surface(rect.size)
    surface.fill(_background_color)
    surface.set_colorkey(_background_color)
    pygame.draw.ellipse(surface, color, (0, 0, rect.width, rect.height), outline)

    return Sprite(surface, rect, tag)

def _check_image_size(ifile):
    """ make sure we don't load humongo images """
    from PIL import Image
    img = Image.open(ifile)
    basewidth = 250
    if img.size[0] > basewidth or img.size[1] > basewidth:
        print('checking image (' + ifile + ') size --> ' + str(img.size))
        wpercent = (basewidth/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        img = img.resize((basewidth,hsize), Image.ANTIALIAS)
        img.save(ifile)


def level(_level):
    """ create a game with levels """
    if _level is None:
        return
    if not isinstance(_level, Level):
        sys.exit('Levels must be subclases of the Level class --> ' + str(_level))
    global current_level, globs
    current_level = _level
    globs = Globals(WIDTH, HEIGHT, GRID_SIZE)
    Globals.instance = globs
    current_level.setup()

def image(name = None, pos = None, center = None, size = 1, tag = ''):
    if not name:
        if os.path.isdir('images/'):
            imgs = []
            mime_types = ('image/png', 'image/jpeg', 'image/gif')
            for img in os.listdir('images/'):
                if mimetypes.guess_type(img)[0] in mime_types:
                    imgs.append(img)
            if len(imgs):
                name = os.path.splitext(random.choice(imgs))[0]
            else:
                name = '__error__'
        else:
            name = '__error__'

    if not name in images:
        if os.path.isdir('images/'):
            for img in os.listdir('images/'):
                if os.path.splitext(img)[0] == name:
                    try:
                        ifile = os.path.join('images', img)
                        _check_image_size(ifile)
                        img = pygame.image.load(ifile)
                        images[name] = img
                    except:
                        traceback.print_exc(file=sys.stdout)
                        continue

                    break
            else: # if no image is found and the loop continues ubroken
                name = '__error__'
        else:
            name = '__error__'

    if not center and not pos:
        pos = rand_pos(size - 1, size - 1)

    img = _create_image(name, pos, center, size, tag)
    globs.sprites.append(img)
    if center:
        register_cell(center, img)
    else:
        register_cell(pos, img)

    return globs.sprites[-1]

def actor(name = None, pos = None, center = None, size = 1, abortable = False, tag = ''):
    if not name:
        sys.exit('Actor name is missing!')

    loaded = False
    states = {}

    if name in actors:
        loaded = True
        states = actors[name]
    else:
        pga_file = 'actors/' + name + '.pga'
        try:
            with ZipFile(pga_file) as pga:
                lst = pga.namelist()
                for f in lst:
                    if f.endswith('.png'):
                        state = f.split('/')[0]
                        if not state in states:
                            states[state] = []
                        with pga.open(f) as afile:
                            states[state].append(pygame.image.load(io.BytesIO(afile.read())))
                            loaded = True
        except:
            traceback.print_exc(file=sys.stdout)
            sys.exit('Unable to find or load actor ' + str(name) + '. actors/' + str(name) + '.pga. may be bad!')

        actors[name] = states

    if not loaded:
        sys.exit('Unable to find or load actor ' + str(name) + '. Does actors/' + str(name) + '.pga exist?')

    if not center and not pos:
        pos = rand_pos(size - 1, size - 1)

    img = _create_actor(states, name, pos, center, size, abortable, tag)
    globs.sprites.append(img)
    if center:
        register_cell(center, img)
    else:
        register_cell(pos, img)
    return globs.sprites[-1]

def maze(name=None, callback=None):

    if not callback:
        callback = partial(shape, RECT)

    if not name:
        return rand_maze(callback)

    path = 'mazes/' + name + '.json'

    cells = json.load(open(path, 'r'))

    for cell in cells:
        s = callback(pos=(cell[0], cell[1]), tag='wall')
        register_cell(s.pos, s)


def shape(shape = None, color = None, pos = None, size = (1, 1), tag = '', **kwargs):
    if not shape:
        shape = random.choice(['circle', 'rect', 'ellipse'])

    if not color:
        color = rand_color()

    if isinstance(size, (int, float)):
        size = (size, size)

    if not pos:
        pos = rand_pos(size[0] - 1, size[1] - 1)

    outline = kwargs.get('outline', 0)

    if shape == 'circle':
        shape = _create_circle(color, pos, size[0], outline, tag)
    elif shape == 'rect':
        shape = _create_rectangle(color, pos, size, outline, tag)
    elif shape == 'ellipse':
        shape = _create_ellipse(color, pos, size, outline, tag)
    else:
        print('Shape, ' + shape + ', is not a valid shape name')
        return False

    globs.sprites.append(shape)
    register_cell(pos, shape)
    return globs.sprites[-1]

def text(string, color = None, pos = None, size = 1, tag = ''):
    """
        draw a text sprite

        :param string: the text to display

        :param color: the color to use to display (default is to select a random color)

        :param pos: the position of the sprite in grid coordinates (default is on center of game canvas)

        :param size: the size of the text font (default is 1)
    """
    string = str(string)
    size = int(size * globs.GRID_SIZE)
    font = pygame.font.Font(None, size)
    font_width, font_height = font.size(string)

    if not color:
        color = rand_color()

    if not pos:
        pos = (globs.WIDTH / 2 -  font_width / 2) / globs.GRID_SIZE, (globs.HEIGHT / 2 - font_height / 2) / globs.GRID_SIZE

    pos = pos[0] * GRID_SIZE, pos[1] * GRID_SIZE

    surface = font.render(string, True, color)
    text = Sprite(surface, pygame.Rect(pos[0], pos[1], font_width, font_height), tag)

    globs.sprites.append(text)
    return globs.sprites[-1]

def sound(name = None, plays = 1, duration = 0):
    """
        play a sound (wav or ogg file). Sounds must be stored in the `sounds/` directory.

        :param name: the name of the sound to play

        :param plays: the number of times to play the sound (default is 1)

        :param duration: the amount of time (in seconds) to play the sound clip (default plays the entire clip)
    """
    plays = plays - 1
    duration = int(duration * 1000)

    path = None
    snd_exts = ('wav', 'ogg')
    if name:
        path = 'sounds/' + name + '.'
        for ext in snd_exts:
            if os.path.isfile(path + ext.lower()):
                path += ext.lower()
                break

            if os.path.isfile(path + ext.upper()):
                path += ext.upper()
                break
        else:
            print('Error: Sound ' + name + ' not found')
    else:
        if os.path.isdir('sounds/'):
            snds = []
            for snd in os.listdir('sounds/'):
                for ext in snd_exts:
                    if snd.lower().endswith(ext):
                        snds.append(snd)
            if len(snds):
                path = 'sounds/' + random.choice(snds)
                name = path[7:-4]
            else:
                print('Error: No sound files found')
        else:
            print('Error: Sounds directory does not exist')

    if not name in sounds:
        snd = pygame.mixer.Sound(path)
        sounds[name] = snd

    sounds[name].play(plays, duration)

def grid():
    """
        show the grid cells on the game canvas
    """
    global show_grid
    show_grid = True

def time():
    """
        returns the time (in seconds) since the start of the game
    """
    return float('%.3f'%(get_time() - start_time))

def callback(function, wait, repeat=0):
    """
        register a time based callback function

        :param function: pointer to a callback function

        :param wait: the amount of time to **wait** for the callback to execute.

        :param repeat: the number of times this callback should repeat (default 0)
    """
    callbacks.append({'cb': function, 'time': get_time() + wait, 'wait': wait, 'repeat' : repeat})

def reset_score(**kwargs):
    """
        forces a reset for a given scoreboard element

        :param pos: the corner position of the scoreboard. Default is `UPPER_LEFT`. Options inclue `UPPER_RIGHT`, `LOWER_LEFT`, and `LOWER_RIGHT`.
    """
    pos = kwargs.get('pos', UPPER_LEFT)
    global score_dict
    try:
        globs.sprites.remove(score_dict[pos]['sprite'])
        del score_dict[pos]
        score(**kwargs)
    except:
        return

def score(value = 0, **kwargs):
    """
        Predigame scoring functions. Any game may have four separate
        scoreboards on the game - one in each corner. *NOTE:* all parameters,
        besides value, are only applied at scoreboard construction time.

        :param value: some scoring value (default is 0). the semantics of the value depends on the scoring `method`

        :param pos: the corner position of the scoreboard. Default is `UPPER_LEFT`. Options inclue `UPPER_RIGHT`, `LOWER_LEFT`, and `LOWER_RIGHT`.

        :param color: the color of the scoring block (default is (25, 25, 25)).

        :param size: the size (in grid cells) of the scoreboard text (default is 0.75).

        :param method: the type of scoreboard to create. options include `ACCUMULATE` (value added/subtracted to score), `VALUE` (simply display the current value), `TIMER` (count time as defined by `step`)

        :param step: applies to `method=TIMER` and sets the operation of the timer. Default is -1 (count up by seconds).

        :param goal: applies to `method=TIMER`. a goal metric of the scoreboard. If the goal is reached a `callback` will be invoked.

        :param prefix: optional text that can be provided to the start of the scoreboard.

        :param callback: optional callback to invoke when the `method=TIMER` reaches a goal.

    """
    if isinstance(value, Number):
        if value > 1000 or value < -1000:
            print('Mean scoring rejected value %s'%str(value))
            value = 0

    color = kwargs.get('color', None)
    size = kwargs.get('size', 0.75)
    pos = kwargs.get('pos', UPPER_LEFT)
    method = kwargs.get('method', ACCUMULATE)
    cb = kwargs.get('callback', None)
    sformat = kwargs.get('format', '%H:%M:%S')
    goal = kwargs.get('goal', 0)
    step = kwargs.get('step', -1)
    prefix = kwargs.get('prefix', None)
    grid_position = score_pos(pos)

    global score_dict
    try:
        score_dict
    except:
        score_dict = {}

    scoreboard = None
    try:
        scoreboard = score_dict[pos]
        if scoreboard['sprite']:
            globs.sprites.remove(scoreboard['sprite'])
    except:
        scoreboard = {
            'value': value,
            'step' : step,
            'sprite': None,
            'size': size,
            'color': (25,25,25),
            'pos': grid_position,
            'method' : method,
            'callback' : cb,
            'format' : sformat,
            'goal' : goal,
            'prefix' : prefix
        }


    scoreboard['size'] = int(size * globs.GRID_SIZE)

    if scoreboard['method'] == TIMER:
        scoreboard['value'] += scoreboard['step']
        if (scoreboard['step'] > 0 and scoreboard['value'] < scoreboard['goal']) or (scoreboard['step'] < 0 and scoreboard['value'] > scoreboard['goal']):
            callback(partial(score, pos=pos), 1)
        elif scoreboard['callback'] is not None:
            scoreboard['callback']()
    elif scoreboard['method'] == ACCUMULATE:
        if isinstance(value, Number):
            scoreboard['value'] += value
        else:
            scoreboard['value'] = value
    elif scoreboard['method'] == VALUE:
        scoreboard['value'] = value

    string = str(scoreboard['value'])
    if scoreboard['method'] == TIMER:
        string = strftime(scoreboard['format'], gmtime(scoreboard['value']))

    if scoreboard['prefix']:
        string = scoreboard['prefix'] + ' ' + string
    font = pygame.font.Font(None, scoreboard['size'])
    font_width, font_height = font.size(string)
    if color:
        scoreboard['color'] = color
    surface = font.render(string, True, scoreboard['color'])
    scoreboard['pos'] = grid_position[0] * globs.GRID_SIZE, grid_position[1] * globs.GRID_SIZE
    if pos == UPPER_RIGHT or pos == LOWER_RIGHT:
        scoreboard['sprite'] = Sprite(surface, pygame.Rect(scoreboard['pos'][0]-font_width, scoreboard['pos'][1], font_width, font_height), globs)
    else:
        scoreboard['sprite'] = Sprite(surface, pygame.Rect(scoreboard['pos'][0], scoreboard['pos'][1], font_width, font_height), globs)
    globs.sprites.append(scoreboard['sprite'])
    score_dict[pos] = scoreboard
    return scoreboard['value']

def timer(value=30, pos=LOWER_RIGHT, color=BLACK, prefix='Time Remaining: ', callback=None):
    if callback is None:
        def __gameover__():
           text('GAME OVER')
           gameover(0.5)
        callback = __gameover__
    score(pos=pos, method=TIMER, value=value, color=color, prefix=prefix, step=-1, goal=0,callback=callback)

def stopwatch(value=0, goal=999, pos=LOWER_LEFT, color=BLACK, prefix='Duration: ', callback=None):
    if callback is None:
        def __gameover__():
           text('GAME OVER')
           gameover(0.5)
        callback = __gameover__
    score(pos=pos, color=color, value=value, method=TIMER,
          step=1, goal=goal, prefix=prefix)

def destroyall():
    del globs.sprites[:]

def pause():
    pygame.event.post(pygame.event.Event(USEREVENT, action = 'pause'))

def resume():
    global update_game
    update_game = True

def gameover(delay=0.5):
    """
        end the current game

        :param delay: the amount of time to wait before ending
    """
    def _gameover():
        global game_over
        game_over = True
    callback(_gameover, delay)

def garbagecollect():
    import gc
    gc.collect(0)
    gc.collect(1)
    gc.collect(2)

def reset(**kwargs):
    global game_over, current_level, score_dict
    game_over = False
    current_level = None
    score_dict = {}

    destroyall()
    globs.keys_registered['keydown'] = {}
    globs.keys_registered['keyup'] = {}
    globs.tags = {}
    del globs.animations[:]
    del callbacks[:]
    if not kwargs.get('soft', False):
        Globals.cache = {}
        from . import api
        code, mod = load_module(RUN_PATH, api)
        exec(code, mod.__dict__)

    garbagecollect()

    global start_time
    start_time = get_time()
    resume()

def quit():
    pygame.quit()
    sys.exit()

def screenshot(directory = 'screenshots', filename = None):
    if not os.path.isdir(directory):
        os.makedirs(directory)
    if not filename:
        filename = pygame.display.get_caption()[0] + ' - ' + str(datetime.datetime.today()) + '.jpg'
    pygame.image.save(SURF, os.path.join(directory, filename))

    size = 100 / globs.GRID_SIZE
    pos = (globs.WIDTH / globs.GRID_SIZE) / 2 - size / 2, (globs.HEIGHT / globs.GRID_SIZE) / 2 - (size / 1.36) / 2

    img = _create_image('__screenshot__', pos, None, size, '')
    globs.sprites.append(img)
    camera = globs.sprites[-1]
    animate(camera, 0.45, camera.destroy, size = size / 1.5)

def _draw_grid():
    for x in range(0, globs.WIDTH, globs.GRID_SIZE):
        pygame.draw.line(SURF, (0, 0, 0), (x, 0), (x, globs.HEIGHT))
    for y in range(0, globs.HEIGHT, globs.GRID_SIZE):
        pygame.draw.line(SURF, (0, 0, 0), (0, y), (globs.WIDTH, y))

def _update_animation(animation, delta):
    animation.update(delta)

def _update(delta):
    time = get_time()
    for sprite in globs.sprites:
        sprite._update(delta)

    animations = globs.animations

    for animation in animations:
        animation.update(delta + 1000 * (get_time() - time))

    for index, animation in enumerate(animations):
        if animation.finished:
            del globs.animations[index]
            animation.finish()

    for _callback in callbacks:
        if _callback['time'] <= get_time():
            _callback['cb']()
            if _callback['repeat'] > 1:
                callback(_callback['cb'], _callback['wait'], _callback['repeat']-1)
            elif _callback['repeat'] == FOREVER:
                callback(_callback['cb'], _callback['wait'], FOREVER)
            callbacks.remove(_callback)

    if current_level is not None:
        if current_level.completed():
            next_level = current_level.next()
            if next_level is not None:
                reset(soft=True)
                level(next_level)

def _draw(SURF):

    if isinstance(_background, pygame.Surface) :
        SURF.blit(_background, (0,0))
    else:
        SURF.fill(_background_color)

    globs.cells = {}
    for sprite in globs.sprites:
        register_cell(sprite.pos, sprite)
        sprite._draw(SURF)

    if show_grid:
        _draw_grid()

def main_loop():
    global update_game
    for event in pygame.event.get():

        if event.type == QUIT:
            pygame.quit()
            sys.exit()

        # lost focus
        #if event.type == ACTIVEEVENT and event.gain == 0:
        #    pause()
        #elif event.type == ACTIVEEVENT:
        #    resume()

        if event.type == KEYDOWN:

            # ignore all the other key presses
            # complete any in process animations
            # TODO: there should be restrictions on
            #       on how this can be used
            for key in globs.keys_pressed:
                globs.keys_pressed.remove(key)

            for animation in globs.animations:
                animation.abort()

            key = pygame.key.name(event.key)
            if key in globs.keys_registered['keydown']:
                for callback in globs.keys_registered['keydown'][key]:
                    callback()

            if not key in globs.keys_pressed:
                globs.keys_pressed.append(key)

            if key == 'escape':
                pygame.event.post(pygame.event.Event(QUIT))

            if key == 'f12':
                screenshot()

        if event.type == KEYUP:
            key = pygame.key.name(event.key)
            if key in globs.keys_registered['keyup']:
                for callback in globs.keys_registered['keyup'][key]:
                    callback()

            if key in globs.keys_pressed:
                globs.keys_pressed.remove(key)

        if event.type == MOUSEBUTTONDOWN:
            for sprite in globs.sprites:
                if sprite.rect.collidepoint(event.pos):
                    sprite._handle_click(event.button, event.pos)

        if event.type == USEREVENT:
            if event.action == 'pause' and update_game and not game_over:
                update_game = False
                _update(clock.get_time())
                _draw(SURF)

    if display_active == DISPLAY_MAIN and (update_game and not game_over):
        mx, my = pygame.mouse.get_pos()
        for sprite in globs.mouse_motion:
                sprite.pos = (mx/globs.GRID_SIZE - sprite.width/2,
                    my/globs.GRID_SIZE - sprite.height/2)
        _update(clock.get_time())
        _draw(SURF)

    if display_active != DISPLAY_MAIN:
        displays[display_active][1].update(clock.get_time())
        displays[display_active][1].draw(displays[display_active][0])



    pygame.display.flip()
    clock.tick(FPS)
