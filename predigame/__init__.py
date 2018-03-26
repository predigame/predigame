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

def bootstrap():
    if len(sys.argv) == 1:
        print('Predigame Instructional Platform\n')
        print('Running a Game:')
        print('   pred some_file.py\n')
        print('Create a New Game:')
        print('   pred new some_game\n')
        print('List Available Game Downloads:')
        print('   pred list\n')
        print('Download a Game:')
        print('   pred pull some_game\n')
        sys.exit()
    if sys.argv[1] == 'new':
        new_game()
    elif sys.argv[1] == 'list':
        get_games()
    elif sys.argv[1] == 'pull':
        pull_game()
    else:
        main()

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

def pull_game():
    if len(sys.argv) != 3:
        print('Usage: pred pull <game>')
        sys.exit()
    game = sys.argv[2]

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
            print('Fetching game {} from {}'.format(game, tag_url))
            with urllib.request.urlopen(tag_url) as response:
                data = response.read()
                with ZipFile(BytesIO(data)) as dnld:
                    prefix = dnld.namelist()[0].split('/')[0]
                    dnld.extractall()
                    os.rename(prefix, game)
            print('Download Complete!')
    except:
        print('Unable to pull game {}. Does it exist?'.format(game))
        traceback.print_exc()

def get_games():
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


def new_game():
    if len(sys.argv) != 3:
        print('Usage: pred new <game>')
        sys.exit()
    game = sys.argv[2]
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
    file.write('TITLE = \'Simple Game\'\n')
    file.close()
