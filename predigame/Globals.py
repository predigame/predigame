from .Assets import Assets
class Globals:
    instance = None
    MAX_SIZE=35
    cache = {}
    def __init__(self, width, height, grid_size, collisions):
        self.WIDTH = width
        self.HEIGHT = height
        self.GRID_SIZE = grid_size
        self.GRID_WIDTH = width / grid_size
        self.GRID_HEIGHT = height / grid_size
        self.PIXEL_COLLISIONS = collisions

        self.sprites = []
        self.backgrounds = [] #sprites/scene things that are in the background
        self.cells = {}
        self.tags = {}
        self.animations = []
        self.keys_registered = {
            'keydown': {},
            'keyup': {}
        }
        self.keys_pressed = []
        self.mouse_motion = []
        self.register_collisions = []
        self.assets = Assets()
