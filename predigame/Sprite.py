import sys, random, math, pygame
from functools import partial
from .utils import register_keydown, register_keyup, animate, randrange_float, sign
from .Globals import Globals

class Sprite():
    """

    The Predigame Sprite - a generic two-dimensional object that is integrated with other sprites in a larger scene. A sprite
    can consist of a bitmap (still) image or a basic geometrical shape (circle, rectangle, ellipse). Sprites in PrediGame
    have some fun properties - they can be clicked, collide with other sprites, even fade, spin or pulse.

    """
    def __init__(self, surface, rect, tag=None, abortable=False, name=None):
        if len(Globals.instance.sprites) >= 9000:
            sys.exit('Too many sprites! You\'re trying to spawn over 9,000!')
        self.surface = surface.convert_alpha()
        self.origin_surface = self.surface
        self.rect = rect
        self.virt_rect = [float(self.rect.x), float(self.rect.y), float(self.rect.width), float(self.rect.height)]
        self.surface = pygame.transform.scale(self.origin_surface, rect.size)
        self.needs_rotation = False
        self.move_speed = 5
        self.moving = False
        self.float_vec = (self.rect.x, self.rect.y)
        self.bounce_vec = (0, 0)
        self.sprite_scale_x = self.width
        self.sprite_scale_y = self.height
        self.rotate_angle = 0
        self.collisions = []
        self.clicks = []
        self.lifespan = -1
        self._pixelated = 0
        self._value = 0
        self.event_pos = None
        self.name = name
        self._tag = tag
        self.abortable = abortable


        if tag not in Globals.instance.tags.keys():
            Globals.instance.tags[tag] = [self]
        else:
            Globals.instance.tags[tag].append(self)

    @property
    def pixelated(self):
        return self._pixelated

    @pixelated.setter
    def pixelated(self, value):
        self._pixelated = value
        self.pixelate(math.ceil(value))

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def x(self):
        """
            get the x (left/right) position of the sprite

            :return: the x position of the sprite as an integer
        """
        return int(self.virt_rect[0] /Globals.instance.GRID_SIZE)

    @x.setter
    def x(self, value):
        """
            set the x (left/right) position of the sprite
        """
        self.needs_rotation = True
        self.virt_rect[0] = int(float(value) * Globals.instance.GRID_SIZE)

    @property
    def y(self):
        """
            get the y (up/down) position of the sprite

            :return: the y position of the sprite as an integer
        """
        return int(self.virt_rect[1] / Globals.instance.GRID_SIZE)

    @y.setter
    def y(self, value):
        """
            set the y (up/down) position of the sprite
        """
        self.needs_rotation = True
        self.virt_rect[1] = int(float(value) * Globals.instance.GRID_SIZE)

    @property
    def pos(self):
        """
            get the x and y positions as a tuple (pair of numbers).
            this is basically the same as calling `Sprite.x` and `Spite.y`
            separately.

            :return: a position tuple (x, y)
        """
        return self.x, self.y

    @pos.setter
    def pos(self, value):
        """
            set the x and y positions as a tuple (pair of numbers).
            this is basically the same as calling `Sprite.x = value` and `Sprite.y = value`
            separately.

            :return: a position tuple (x, y)
        """
        self.x = value[0]
        self.y = value[1]

    @property
    def width(self):
        """
            get the width of a sprite in terms of the grid block size.
        """
        return self.virt_rect[2] / Globals.instance.GRID_SIZE

    @property
    def height(self):
        """
            get the width of a sprite in terms of the grid block size.
        """
        return self.virt_rect[3] / Globals.instance.GRID_SIZE

    @property
    def size(self):
        """
            get the size of the sprite. sprites have a default size of 1 grid block.
            they can be increased or decreased as desired. the `Sprite.pulse()` effect
            will call size many times to create the desired effect.

            :todo: this method only returns the size along the x dimension. sprites should maintain separate sizes, one for each dimension.
        """
        return self.sprite_scale_x

    @size.setter
    def size(self, value):
        """
            set the size of the sprite. sprites have a default size of 1 grid block.
            they can be increased or decreased as desired. the `Sprite.pulse()` effect
            will call size many times to create the desired effect.

            :todo: this method applies the same magnification to both x and y dimensions. sprites should maintain separate sizes, one for each dimension.
        """
        self.needs_rotation = True
        self.sprite_scale_x = value
        self.sprite_scale_y = value

    def resize(self, value):
        """
            similar to `Sprite.size()` but callable as a method.
        """
        self.size = value
        return self

    @property
    def angle(self):
        """
            get the current rotated angle of the sprite

            :return: display angle in degrees
        """

        return self.rotate_angle

    @angle.setter
    def angle(self, value):
        """
            rotate the sprite by some `value` of degrees
        """
        self.needs_rotation = True
        self.rotate_angle = value

    @property
    def tag(self):
        """
            sprites can be "tagged" with extra information. for example,
            many zombie sprites can all have the singular tag "zombie".
            :return: the tag of the sprite (can be None if no tag provided)
        """
        return self._tag

    @property
    def center(self):
        x, y, width, height = self.virt_rect[:]
        return (x + width/2.0)/ Globals.instance.GRID_SIZE, (y + height/2.0)/ Globals.instance.GRID_SIZE

    def _update(self, delta):
        if self.needs_rotation:
            self.rotate(0)
            self.needs_rotation = False
        self._handle_collisions()

    def _draw(self, surface):
        surface.blit(self.surface, self.rect)

    def _handle_collisions(self):
        for collision in self.collisions:
            if not collision['sprite'] in Globals.instance.sprites:
                self.collisions.remove(collision)
                continue

            if self.rect.colliderect(collision['sprite'].rect):
                collision['cb'](self, collision['sprite'])
                #break # only handle one collision per frame (for now)

    def _update_float(self, distance, time):
        float_x, float_y = self.float_vec
        time = self._calc_time((distance, distance))

        if self.virt_rect[0] == float_x:
            move_x = randrange_float(-distance, distance, distance * 2)
        else:
            move_x = -distance * sign(self.virt_rect[0] - float_x)

        if self.virt_rect[1] == float_y:
            move_y = randrange_float(-distance, distance, distance * 2)
        else:
            move_y = -distance * sign(self.virt_rect[1] - float_y)

        animate(self, time, partial(self._update_float, distance, time), x = self.x + move_x, y = self.y + move_y)

    def _update_bounce(self):
        if self.virt_rect[0] + self.virt_rect[2] >= Globals.instance.WIDTH and self.bounce_vec[0] > 0:
            self.bounce(True, False)
        elif self.virt_rect[0] <= 0 and self.bounce_vec[0] < 0:
            self.bounce(True, False)
        elif self.virt_rect[1] + self.virt_rect[3] >= Globals.instance.HEIGHT and self.bounce_vec[1] > 0:
            self.bounce(False, True)
        elif self.virt_rect[1] <= 0 and self.bounce_vec[1] < 0:
            self.bounce(False, True)

        x_dist = self.x
        if self.bounce_vec[0] >= 1:
            x_dist = (Globals.instance.WIDTH - (self.virt_rect[0] + self.virt_rect[2])) / (Globals.instance.GRID_SIZE * 1.0)
        y_dist = self.y
        if self.bounce_vec[1] >= 1:
            y_dist = (Globals.instance.HEIGHT - (self.virt_rect[1] + self.virt_rect[3])) / (Globals.instance.GRID_SIZE * 1.0)

        distance = min(x_dist, y_dist)
        time = self._calc_time((distance, distance))
        animate(self, time, self._update_bounce, x = self.x + distance * self.bounce_vec[0], y = self.y + distance * self.bounce_vec[1])

    def _handle_click(self, button, pos):
        for click in self.clicks:
            if button == click['btn']:
                self.event_pos = (1.0*pos[0])/Globals.instance.GRID_SIZE, (1.0*pos[1])/Globals.instance.GRID_SIZE
                click['cb'](self)

    def _calc_time(self, vector, position = None):
        if not position:
            position = self.virt_rect[0:2]
        cur_x, cur_y = position
        new_x = cur_x + vector[0] * Globals.instance.GRID_SIZE
        new_y = cur_y + vector[1] * Globals.instance.GRID_SIZE
        distance = math.sqrt((new_x - cur_x)**2 + (new_y - cur_y)**2)
        time = (abs(distance) / self.move_speed) / 60.0
        return time

    def _complete_move(self, callback = None):
        self.moving = False
        if callback:
            callback()

    def destruct(self, time=1, **kwargs):
        """
            self destruct this sprite after `time` seconds

            :param time: the amount of time (in seconds) to stay alive before self destructing.

            :param callback: optional callback to execute after time is up (you'll need to do your own destructing)
        """

        self.lifespan = 0

        callback = kwargs.get('callback', None)
        if callback is None:
            callback = partial(self.destroy)
        animate(self, time, callback, lifespan=time)
        return self

    def fade(self, time=1, **kwargs):
        """
            make this sprite fade away and automatically self-destruct. this can be slow to run on some computers.

            :param time: the amount of time (in seconds) to run the fade effect.

            :todo: the final effect, like `destroy` should be configurable
        """
        #callback = kwargs.get('callback', None)
        animate(self, time, partial(self.destroy), pixelated = 100, size = 0)
        return self

    def move(self, vector, **kwargs):
        """
            move this sprite along a particular vector to the next grid cell (x and/or y dimensions)

            :param vector: the movement vector (x, y). `x` or `y` can take the values 0 (no movement), 1 (right or down movement), -1 (up or left movement). For example a vector of (1, 0) will move the sprite right and a vector of (1, -1) will move the sprite up and right.

            :param callback: an optional callback function to invoke when movement is complete.

            :param precondition: an optional callback function to invoke prior to a movement. preconditions all the sprite to avoid making a certain move (e.g. to avoid a wall)
        """
        self.moving = True
        callback = kwargs.get('callback', None)
        precondition = kwargs.get('precondition', None)

        x_dest = int(self.x + vector[0])
        y_dest = int(self.y + vector[1])
        time = self._calc_time(vector)
        if precondition == None or precondition('move', self, (x_dest, y_dest)):
            animate(self, time, partial(self._complete_move, callback), abortable=self.abortable, x = x_dest, y = y_dest)
        else:
            animate(self, time, partial(self._complete_move, callback), abortable=self.abortable, x = self.x, y = self.y)
        return self

    def move_to(self, *points, **kwargs):
        """
            move the sprite to a given point or set of points. movement will be set according to the `speed` of the sprite.

            :param points: one or more positions (x, y) pairs.

            :param callback: an optional callback function to invoke when movement is complete.


            Example:

            `s.move_to((0,0), (5,5), (10, 10), callback=s.destroy)`

            will move the sprite to position (0, 0) then (5,5) then (10,10) and then destroy itself.

        """
        #if self.moving:
        #    return self
        self.moving = True

        callback = partial(self._complete_move, kwargs.get('callback', None))
        times = []

        for index, point in enumerate(points):
            if index == 0:
                prev_point = self.pos
            else:
                prev_point = points[index - 1]
            vector = (point[0] - prev_point[0], point[1] - prev_point[1])
            time = self._calc_time(vector, prev_point)
            times.append(time)

        for point in reversed(points):
            time = times.pop(-1)
            callback = partial(animate, self, time, callback, abortable=self.abortable, x = point[0], y = point[1])

        callback()
        return self

    def _continue_key(self, key, distance, **kwargs):
        p = kwargs.get('precondition', None)
        if key in Globals.instance.keys_pressed:
            self.move(distance, callback = partial(self._continue_key, key, distance, precondition = p), precondition = p)

    def keys(self, right = 'right', left = 'left', up = 'up', down = 'down', **kwargs):
        """
            make this sprite move to keyboard events. by default movements will be directional, by grid location -
            meaning that the sprite will move up, down, left, or right by one (default) grid cell.

            :param right: the keyboard button for right direction movement. default is the `right` arrow.

            :param left: the keyboard button for left direction movement. default is the `left` arrow.

            :param up: the keyboard button for up direction movement. default is the `up` arrow.

            :param down: the keyboard button for down direction movement. default is the `down` arrow.

            :param spaces: the number of grid cell. to move for each keyboard event. default is `1` grid cell.

            :param precondition: an optional callback function to invoke prior to a movement. preconditions all the sprite to avoid making a certain move (e.g. to avoid a wall)

            :param direction: the direction of the keyboard button and when to fire the event event. options are `down` for keyboard push down events or `up` for when the keyboard button is released. default is `down`.

        """
        p = kwargs.get('precondition', None)
        distance = kwargs.get('spaces', 1)

        register_key = None
        if kwargs.get('direction', 'down') == 'down':
            register_key = register_keydown
        else:
            register_key = register_keyup

        if right:
            register_key(right, partial(self.move, (1 * distance, 0), callback = partial(self._continue_key, right, (1 * distance, 0), precondition = p), precondition = p))
        if left:
            register_key(left, partial(self.move, (-1 * distance, 0), callback = partial(self._continue_key, left, (-1 * distance, 0), precondition = p), precondition = p))
        if up:
            register_key(up, partial(self.move, (0, -1 * distance), callback = partial(self._continue_key, up, (0, -1 * distance), precondition = p), precondition = p))
        if down:
            register_key(down, partial(self.move, (0, 1 * distance), callback = partial(self._continue_key, down, (0, 1 * distance), precondition = p), precondition = p))

        return self

    def follow(self):
        """
            tell the sprite to follow the mouse cursor as it moves around the screen
        """
        if self not in Globals.instance.mouse_motion:
            Globals.instance.mouse_motion.append(self)
        return self

    def speed(self, speed = 5):
        """
            set the speed of the sprite for movement actions. by default the sprite will move five grid cells per second.

            :param speed: the speed for movement actions. default is `5`.

        """
        self.move_speed = abs(speed)

        return self

    def float(self, distance = 0.25):
        """
            make the sprite float around on the screen. this provides a simple movement animation.

            :param distance: the amount of grid cell distance a sprite should float. default is `0.25`.

        """

        if self.moving:
            return self
        self.moving = True

        self.float_vec = (self.virt_rect[0], self.virt_rect[1])
        time = self._calc_time((distance, distance))

        animate(self, 0.016, partial(self._update_float, distance, time))

        return self

    def collides(self, sprites, callback):
        """
            register a callback function for when this sprite collides with another sprite. collision checks will occur as part of each update invocation.

            :param sprites: one (single object) or more (a list) of sprites to check for collisions.

            :param callback: the callback function to invoke when a collision is detected.

            :todo: confirm that collides are bi-directional events.

        """
        if not isinstance(sprites, list):
            sprites = [sprites]

        for sprite in sprites:
            if sprite == self:
                continue
            if sprite in self.collisions:
                self.collisions.remove(sprite)
            self.collisions.append({ 'sprite': sprite, 'cb': callback })

        return self

    def clicked(self, callback, button = 1):
        """
            register a callback function for when this sprite is clicked with a mouse button.

            :param callback: the callback function to invoke when a mouse click event is detected on this sprite.

            :param button: the mouse button to register for click events. options are left button `1` (default), right button `3` or middle button/track wheel `2`.

            :todo: confirm that collides are bi-directional events.

        """
        self.clicks.append({'btn': button, 'cb': callback})

        return self

    def pixelate(self, pixel_size = 10):
        """
            a simple effect for blurring or `pixelating` a sprite.

            :param pixel_size: the size of the pixels. default is `10`.
        """

        x_start = 0
        x_range = int(self.virt_rect[2])
        y_start = 0
        y_range = int(self.virt_rect[3])

        for x_offset in range(x_start, x_range, pixel_size):
            for y_offset in range(y_start, y_range, pixel_size):
                avg_color = pygame.transform.average_color(self.surface, (x_offset, y_offset, pixel_size, pixel_size))
                pygame.draw.rect(self.surface, avg_color, (x_offset, y_offset, pixel_size, pixel_size))

        return self

    def rotate(self, angle):
        """
            rotate the sprite by some angle (in degrees)

            :param angle: the directional angle (in degrees) to rotate this sprite.

        """
        self.rotate_angle += angle
        if self.rotate_angle > 360:
            self.rotate_angle -= 360

        x, y, width, height = self.virt_rect[:]
        center = (x + width/2), (y + height/2)

        scale_width = self.sprite_scale_x * Globals.instance.GRID_SIZE
        scale_height = self.sprite_scale_y * Globals.instance.GRID_SIZE
        self.surface = pygame.transform.scale(self.origin_surface, (int(scale_width), int(scale_height)))
        self.surface = pygame.transform.rotate(self.surface, self.rotate_angle)

        self.rect = self.surface.get_rect(center=center)
        new_rect = self.surface.get_rect()
        self.virt_rect[2] = new_rect[2]
        self.virt_rect[3] = new_rect[3]

        return self

    def flip(self, flip_x = True, flip_y = False):
        """
            flip the sprite image along x axis - left/right (default) or y axis - up/down.

            :param flip_x: flip the sprite along the x axis. default is `True`.

            :param flip_y: flip the sprite along the y axis. default is `False`.

        """

        self.origin_surface = pygame.transform.flip(self.origin_surface, flip_x, flip_y)
        self.surface = pygame.transform.flip(self.surface, flip_x, flip_y)

        return self

    def scale(self, size):
        """
            scale (increase or decrease) the size of the sprite. applies to both with and height.

            :param size: multiplier for modifying sprite scale. if greater than 1 sprite will increase in scale. if less than one (a decimal) sprite will decrease in case. if value is 1 sprite will left intact.

            :todo: scale needs to be applied separately to x and y axis.
        """

        if self.virt_rect[2] > Globals.instance.WIDTH and self.virt_rect[3] > Globals.instance.HEIGHT:
            return self
        width = self.virt_rect[2] * size
        height = self.virt_rect[3] * size

        self.virt_rect[2] = width
        self.virt_rect[3] = height
        self.sprite_scale_x = self.sprite_scale_x * size
        self.sprite_scale_y = self.sprite_scale_y * size

        self.surface = pygame.transform.smoothscale(self.origin_surface, (int(self.virt_rect[2]), int(self.virt_rect[3]))).convert_alpha()

        return self

    def bounce(self, bounce_x = True, bounce_y = True):
        x_dir, y_dir = self.bounce_vec
        if bounce_x:
            x_dir = -x_dir
        if bounce_y:
            y_dir = -y_dir
        self.bounce_vec = x_dir, y_dir

        return self

    def bouncy(self):
        """
            make this sprite a little bouncy. the `speed` attribute will control the speed of movement.
        """
        if self.moving:
            return self
        self.moving = True

        self.bounce_vec = (random.choice([-1, 1]), random.choice([-1, 1]))
        animate(self, 0.016, self._update_bounce)

        return self

    def pulse(self, time = 1, size = None):
        """
            add a pulsing effect. make the sprite simultaneously increase then decrease in size.

            :param time: the amount of time (in seconds) to complete a pulse. default is `1` second.

            :param size: the maximum size to pulse. default is to pulse until the size is doubled and then contract back to original size.

        """
        if not size:
            size = self.size * 2
        animate(self, time, partial(self.pulse, time, self.size), size = size)

        return self

    def spin(self, time = 1, rotations = None, **kwargs):
        """
            make this sprite spin.

            :param time: the amount of time (in seconds) to complete a revolution. default is `1` second.

            :param rotations: the amount of time (in seconds) to run the spin effect. default will run forever.

            :param callback: a function to call back when done spinning (rotations must be specified)

        """


        #if self.moving and not kwargs.get('spinning', False):
        #    return self
        callback = kwargs.get('callback', None)
        self.moving = True
        if rotations is not None:
            if rotations > 0:
                animate(self, time, partial(self.spin, time, rotations-1, spinning = True, callback=callback), angle = self.angle + 360)
            else:
                self.angle = 0
                if callback is not None:
                    callback()

        else:
            animate(self, time, partial(self.spin, time, spinning = True), angle = self.angle + 360)

        return self

    def destroy(self, *args):
        """
            destroy this sprite and remove from the game canvas.
        """
        if self in Globals.instance.sprites:
           Globals.instance.sprites.remove(self)
           Globals.instance.tags[self._tag].remove(self)
        return self

    def wander(self, callback, time = 1):
        """
            turn your sprite into a bot by allowing the sprite to wander around. how the sprite "wanders" is based on the `callback` function.

            :param callback: the callback function to determine how the sprite should wander. this function should call a move operation.

            :param time: the frequency (in seconds) in order to call the wander function. default is `1` second.

        """
        callback()

        animate(self, time, partial(self.wander, callback, time))
        return self
