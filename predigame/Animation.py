from .Globals import Globals
import math
class Animation:
    def __init__(self, obj, duration, callback, abortable=False, **kwargs):
        self.obj = obj
        self.start = {}
        self.attributes = kwargs
        for attribute in self.attributes:
            self.start[attribute] = getattr(obj, attribute)
        self.time = float(0)
        self.duration = float(duration)

        # prevent div by 0
        if self.duration == 0.0:
            self.duration = 0.00001

        self.callback = callback
        self.finished = False
        self.abortable = abortable

    def update(self, delta):
        self.time += delta / 1000
        n = self.time / self.duration

        if n >= 1:
            self.finished = True
            n = 1

        for attribute in self.attributes:
            step = self.attributes[attribute] - self.start[attribute]
            setattr(self.obj, attribute, n * step + self.start[attribute])

    def abort(self):
        if self.abortable:
            self.finished = True
            if self.progress() > 50:
                for attribute in self.attributes:
                    setattr(self.obj, attribute, self.attributes[attribute])

    def progress(self):
        min_progress = 100.0

        for attribute in self.attributes:
            if self.attributes[attribute] == 0:
                continue
            progress = math.fabs(100.0 - ((self.attributes[attribute] - getattr(self.obj, attribute))/(self.attributes[attribute])))
            if progress < min_progress:
                min_progress = progress
        return min_progress

    def finish(self):
        if not self.obj in Globals.instance.sprites:
            return

        if self.callback:
            self.callback()
