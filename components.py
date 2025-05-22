class Player:
    def __init__(self, images):
        self.images = images
        self.direction = 'left'
        self.frame = 0
        self.last_frame_time = 0
        self.firing_start_time = None
        self.flute = True
        self.fluffy = 0

class Terrain:
    def __init__(self, type):
        self.type = type


class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.z = 0


class Moveable:
    def __init__(self, speed):
        self.speed = speed
        self.target_x = None
        self.target_y = None
        self.moved = False
        self.velocity_y = 0
        self.on_ground = True


class Renderable:
    def __init__(self, image, z):
        self.image = image
        self.z = z


class PathConnections:
    def __init__(self):
        self.up = False
        self.down = False
        self.left = False
        self.right = False


class TrackConnections:
    def __init__(self):
        self.up = False
        self.down = False
        self.left = False
        self.right = False