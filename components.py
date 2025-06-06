class Player:
    def __init__(self, images):
        self.images = images
        self.direction = 'left'
        self.frame = 0
        self.last_frame_time = 0


class Terrain:
    def __init__(self, type):
        self.type = type


class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.z = 0


class Moveable:
    def __init__(self):
        self.speed = 3
        self.target_x = None
        self.target_y = None
        self.moved = False
        self.velocity_y = 0
        self.on_ground = True


class Renderable:
    def __init__(self, image, z):
        self.image = image
        self.z = z
