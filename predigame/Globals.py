class Globals:
    instance = None
    MAX_SIZE=35
    cache = {}
    def __init__(self, width, height, grid_size):
        self.WIDTH = width
        self.HEIGHT = height
        self.GRID_SIZE = grid_size

        self.sprites = []
        self.cells = {}
        self.tags = {}
        self.animations = []
        self.keys_registered = {
            'keydown': {},
            'keyup': {}
        }
        self.keys_pressed = []
        self.mouse_motion = []
