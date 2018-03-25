import sys, os, shutil, json
import urllib.request, traceback
from io import BytesIO
from github import Github
from zipfile import ZipFile
from types import ModuleType
from . import predigame
from .utils import load_module
from predigame.constants import *

from pkg_resources import get_distribution
__version__ = get_distribution('predigame').version

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

def pull():
    if len(sys.argv) != 2:
        print('Usage: predpull <game>')
        sys.exit()
    game = sys.argv[1]

    if os.path.exists(game):
        prompt = input('{} already exists. Overwrite? (Y or N): '.format(game))
        if prompt.upper() == 'Y':
            shutil.rmtree(game)
        else:
            sys.exit()
    try:
        g = Github()
        repo = g.get_organization('predigame').get_repo(game)
        tags = repo.get_tags()
        tag_url = None
        for tag in tags:
            tag_name = tag.name
            tag_url = tag.zipball_url
            if tag_name == __version__:
                tag_url

        if tag_url is not None:
            with urllib.request.urlopen(tag_url) as response:
                data = response.read()
                with ZipFile(BytesIO(data)) as dnld:
                    prefix = dnld.namelist()[0].split('/')[0]
                    dnld.extractall()
                    os.rename(prefix, game)
    except:
        print('Unable to pull game {}. Does it exist?'.format(game))
        traceback.print_exc()
def list():
    g = Github()

    repos = g.get_organization('predigame').get_repos()
    for repo in repos:
        name = repo.full_name.replace('predigame/', '')
        if name == 'predigame':
            continue
        desc = repo.description
        tags = repo.get_tags()
        version_match = False
        for tag in tags:
            tag_name = tag.name
            tag_url = tag.zipball_url
            if tag_name == __version__:
                version_match = True
            #print('  {} \t {}'.format(tag_name, tag_url))
        if version_match:
            print('{0:10} \t {1}'.format(name, desc))


def create():
    if len(sys.argv) != 2:
        print('Usage: predcreate <game>')
        sys.exit()
    game = sys.argv[1]
    if os.path.exists(game):
        prompt = input('{} already exists. Overwrite? (Y or N): '.format(game))
        if prompt.upper() == 'Y':
            shutil.rmtree(game)
        else:
            sys.exit()
    os.mkdir(game)
    os.mkdir(game + '/backgrounds')
    os.mkdir(game + '/images')
    os.mkdir(game + '/sounds')
    os.mkdir(game + '/actors')
    file = open(game + '/game.py', 'w')
    file.write('WIDTH = 30\n')
    file.write('HEIGHT = 20\n')
    file.write('TITLE = \'Simple Two Level Example\'\n')
    file.close()
