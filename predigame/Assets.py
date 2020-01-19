from pathlib import Path, PurePath
from urllib.request import urlopen
from PIL import Image
from zipfile import ZipFile
import io, pygame, os, random, sys, traceback

# globally manages assets across the platform, fetching from the internet as needed
# business rules for retrieving assets
# - 1. check a project's asset directory
# - 2. check the system cache
# - 3. check online
# - 4. error out
class Assets:
    def __init__(self):
        self.url_prefix = 'http://predigame.io/assets'

        self.global_cache = Path.home() / '.predigame'
        Path(self.global_cache / 'actors').mkdir(parents=True, exist_ok=True)
        Path(self.global_cache / 'backgrounds').mkdir(parents=True, exist_ok=True)
        Path(self.global_cache / 'images').mkdir(parents=True, exist_ok=True)
        Path(self.global_cache / 'sounds').mkdir(parents=True, exist_ok=True)
        Path(self.global_cache / 'pyfonts').mkdir(parents=True, exist_ok=True)

        self.fonts_loaded = {}
        self.local_cache = Path.cwd()
        self.images_loaded = {}
        self.actors_loaded = {}
        self.background_index = self.fetch_index('backgrounds')

    def font(self, size):
        if size in self.fonts_loaded:
            return self.fonts_loaded[size]

        file = self.find('pyfonts', 'freesansbold')
        if file is not None:
            self.fonts_loaded[size] = pygame.font.Font(str(file), size)
            return self.fonts_loaded[size]
        else:
            self.fetch('pyfonts', 'freesansbold.ttf')
            return self.font(size)

    def fetch(self, type, item):
        """
            fetches file remotely (if exists) otherwise returns error
            successfully fetched files are persisted in the global cache
        """
        # download
        try:
            print('Attempting to fetch ' + str(self.url_prefix + '/' + type + '/' + item))
            item_bytes = io.BytesIO(urlopen(self.url_prefix + '/' + type + '/' + item).read())
        except:
            traceback.print_exc(file=sys.stdout)
            sys.exit('Unable to find %s with the name %s' % (type, item))
        else:
            # save a local copy
            cached_file = io.FileIO(self.global_cache / type  / item, 'w')
            writer = io.BufferedWriter(cached_file)
            writer.write(item_bytes.getvalue())
            writer.flush()
            writer.close()
            return item_bytes

    def fetch_index(self, type, fetch_remote=False):
        """
            fetches the index file of available assets for a given type
        """
        if fetch_remote:
            try:
                #print('Attempting to fetch index ' + str(self.url_prefix + '/' + type + '/index.txt'))
                index = io.BytesIO(urlopen(self.url_prefix + '/' + type + '/index.txt').read())
                return str(index.getvalue(), 'utf-8').splitlines()
            except:
                #traceback.print_exc(file=sys.stdout)
                print('Unable to find %s directory index. Access will be limited to cache.')
                return self.fetch_index(type, fetch_remote=False)
        else:
            return fetch_index_cache(Path(self.local_cache / type)) + fetch_index_cache(Path(self.global_cache / type))


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
            sys.exit('At least one image must be able in the local or global cache. Existing.')
        else:

            if not has_suffix(name):
                name = name + '.'

            # check local
            if local_cache.exists() and local_cache.is_dir():
                for file in local_cache.iterdir():
                    if file.name.lower().startswith(name):
                        print('found local file ' + str(file))
                        return file

            # check global
            if global_cache.exists() and global_cache.is_dir():
                for file in global_cache.iterdir():
                    if file.name.lower().startswith(name):
                        print('found global file ' + str(file))
                        return file

            return None

    def background(self, name, width=800, height=600):
        if name is "" or name is None:
            return self.background(random.choice(self.background_index), width, height)
        else:
            file = self.find('backgrounds', name)
            if file is not None:
                #print('loading file ' + str(file))
                return load(io.BytesIO(file.read_bytes()), width, height)
            else:
                if not has_suffix(name):
                    name = name + '.png'
                return load(self.fetch('backgrounds', name), width, height)

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
                if not has_suffix(name):
                    name = name + '.png'
                self.images_loaded[name] = load(self.fetch('images', name))

            return self.images_loaded[name]

    def actor(self, name):
        local_actors = Path(self.local_cache / 'actors')
        global_actors = Path(self.global_cache / 'actors')

        name = name.lower()

        if name is "" or name is None:
            return load(io.BytesIO(self.find('actors', None).read_bytes()))
        else:
            # check loaded cache
            if name in self.actors_loaded:
                return self.actors_loaded[name]

            file = self.find('actors', name)
            if file is None:
                if not has_suffix(name):
                    name = name + '.pga'
                file = self.fetch('actors', name)

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
        sys.exit('Error attempting to load image. Exiting.')

def has_suffix(file):
    extensions = ['.jpg', '.jpeg', '.png', '.pga', '.bmp']
    file = file.lower()
    for x in extensions:
        if file.endswith(x):
            return True
    return False

def fetch_index_cache(cache_path):
    """
        fetches an index based on the provided cache_path
    """
    idx = []
    if cache_path.exists() and cache_path.is_dir():
        for file in cache_path.iterdir():
            idx.append(file.stem.lower())
    return idx

def resource_path():
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = PurePath(str(sys._MEIPASS))
    except Exception:
        #traceback.print_exc(file=sys.stdout)
        base_path = PurePath(__file__).parent
    #print('resource path is %s' % str(base_path))
    return base_path
