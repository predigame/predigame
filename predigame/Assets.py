from pathlib import Path, PurePath
from urllib.request import urlopen
from PIL import Image
from zipfile import ZipFile
import io, pygame, os, random, re, sys, traceback

# globally manages assets across the platform, fetching from the internet as needed
# business rules for retrieving assets
# - 1. check a project's asset directory
# - 2. check the system cache
# - 3. check online
# - 4. return an error asset
class Assets:
    def __init__(self):
        self.url_prefix = 'http://predigame.io/assets'

        self.global_cache = Path.home() / '.predigame'
        Path(self.global_cache / 'actors').mkdir(parents=True, exist_ok=True)
        Path(self.global_cache / 'backgrounds').mkdir(parents=True, exist_ok=True)
        Path(self.global_cache / 'images').mkdir(parents=True, exist_ok=True)
        Path(self.global_cache / 'sounds').mkdir(parents=True, exist_ok=True)

        self.local_cache = Path.cwd()
        self.images_loaded = {}
        self.actors_loaded = {}

    def fetch(self, type, item):
        """
            fetches file remotely (if exists) otherwise returns error
            successfully fetched files are persisted in the global cache
        """
        # download
        try:
            item_bytes = io.BytesIO(urlopen(self.url_prefix + '/' + type + '/' + item).read())
        except:
            traceback.print_exc(file=sys.stdout)
            return error(type)
        else:
            # save a local copy
            cached_file = io.FileIO(self.global_cache / type  / item, 'w')
            writer = io.BufferedWriter(cached_file)
            writer.write(item_bytes.getvalue())
            writer.flush()
            writer.close()
            return item_bytes

    def find(self, type, name):
        """
            fetches files that are in the local (per game) or global (per system) cache
            returns None if prefix name of that given type does not exist otherwise returns a
            file-like object
        """
        local_cache = Path(self.local_cache / type)
        global_cache = Path(self.global_cache / type)
        if name is "" or name is None:
            # pick a random file from the local (if any) or global cache (if any)
            # use error if not
            if local_cache.exists() and local_cache.is_dir() and len(list(local_cache.iterdir())) > 0:
                return random.choice(list(local_cache.iterdir()))
            if global_cache.exists() and global_cache.is_dir() and len(list(global_cache.iterdir())) > 0:
                return random.choice(list(global_cache.iterdir()))
            return error(type)
        else:
            # check local
            if local_cache.exists() and local_cache.is_dir():
                for file in local_cache.iterdir():
                    if re.match(name, file.name, re.I):
                        return file

            # check global
            if global_cache.exists() and global_cache.is_dir():
                for file in global_cache.iterdir():
                    if re.match(name, file.name, re.I):
                        return file

            return None

    def background(self, name, width=800, height=600):
        if name is "" or name is None:
            try:
                return load(io.BytesIO(urlopen('http://picsum.photos/800/?random').read()), width, height)
            except:
                traceback.print_exc(file=sys.stdout)
                return load(error('backgrounds'), width, height)
        else:
            file = self.find('backgrounds', name)
            if file is not None:
                return load(io.BytesIO(file.read_bytes()), width, height)
            else:
                return load(self.fetch('backgrounds', name + '.png'), width, height)

    def image(self, name):
        local_images = Path(self.local_cache / 'images')
        global_images = Path(self.global_cache / 'images')

        if name is "" or name is None:
            return load(io.BytesIO(self.find('images', None).read_bytes()))
        else:
            # check loaded cache
            if name in self.images_loaded:
                return self.images_loaded[name]

            file = self.find('images', name)
            if file is not None:
                reduce_size(file)
                self.images_loaded[name] = load(io.BytesIO(file.read_bytes()))
            else:
                self.images_loaded[name] = load(self.fetch('images', name + '.png'))

            return self.images_loaded[name]

    def actor(self, name):
        local_actors = Path(self.local_cache / 'actors')
        global_actors = Path(self.global_cache / 'actors')

        if name is "" or name is None:
            return load(io.BytesIO(self.find('actors', None).read_bytes()))
        else:
            # check loaded cache
            if name in self.actors_loaded:
                return self.actors_loaded[name]

            file = self.find('actors', name)
            if file is None:
                file = self.fetch('actors', name + '.pga')

            # extract states from actor file
            try:
                states = {}
                with ZipFile(file) as pga:
                    lst = pga.namelist()
                    for f in lst:
                        if f.endswith('.png'):
                            state = f.split('/')[0]
                            if not state in states:
                                states[state] = []
                            with pga.open(f) as afile:
                                states[state].append(pygame.image.load(io.BytesIO(afile.read())))

                self.actors_loaded[name] = states
            except:
                traceback.print_exc(file=sys.stdout)
                sys.exit('Unable to find or load actor ' + str(name) + '. actors/' + str(name) + '.pga. may be bad!')

            return self.actors_loaded[name]

def reduce_size(ifile):
    """ make sure we don't load humongo images """
    img = Image.open(ifile)
    basewidth = 1024
    if img.size[0] > basewidth or img.size[1] > basewidth:
        print('checking image (' + str(ifile) + ') size --> ' + str(img.size))
        wpercent = (basewidth/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        img = img.resize((basewidth,hsize), Image.ANTIALIAS)
        img.save(ifile)

def load(bytes, width=None, height=None):
    try:
        asset = pygame.image.load(bytes)
        if width is not None and height is not None:
            asset = pygame.transform.scale(asset, (width, height))
        return asset
    except:
        traceback.print_exc(file=sys.stdout)
        return load(error('images'))

def error(type):
    # TODO: find better images for errors
    if type == 'actors':
        return io.FileIO(PurePath(__file__).parent / 'actors' / 'error.pga')
    else:
        return io.FileIO(PurePath(__file__).parent / 'images' / 'error.png')
