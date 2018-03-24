import sys, os
from types import ModuleType
from . import predigame
from .utils import load_module
from predigame.constants import *

def err():
    print('Error: Invalid Python file provided')
    sys.exit()

def main():
    try:
        run_mod = sys.argv[1:][0]
    except:
        err()

    path = os.path.join(os.getcwd(), run_mod)
    from . import api
    code, mod = load_module(path, api)

    dummy_mod = ModuleType('dummy')

    try:
        exec(code, dummy_mod.__dict__)
    except:
        pass
    finally:
        WIDTH = getattr(dummy_mod, 'WIDTH', 16)
        HEIGHT = getattr(dummy_mod, 'HEIGHT', 16)
        TITLE = getattr(dummy_mod, 'TITLE', 'PrediGame')
        SIZE = getattr(dummy_mod, 'SIZE', 50)
        BACKGROUND = getattr(dummy_mod, 'BACKGROUND', (220, 220, 220))
        FULLSCREEN = getattr(dummy_mod, 'FULLSCREEN', False)

    predigame.init(path, WIDTH * SIZE, HEIGHT * SIZE, TITLE, grid = SIZE, bg = BACKGROUND, fullscreen = FULLSCREEN)

    exec(code, mod.__dict__)

    while True:
        predigame.main_loop()
