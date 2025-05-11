import esper
from components import *

class RenderSystem(esper.Processor):
    def __init__(self, screen, camera, background = None):
        super().__init__()
        self.screen = screen
        self.camera = camera
        self.background = background

    def process(self, dt):
        if self.background:
            self.screen.blit(self.background, (0, 0))

        entities = esper.get_components(Position, Renderable)

        entities.sort(key=lambda ent: ent[1][1].z)

        for entity, (position, renderable) in entities:
            image = renderable.image

            x = position.x * self.camera.zoom + self.camera.offset_x
            y = position.y * self.camera.zoom + self.camera.offset_y - position.z
            if image:
                self.screen.blit(image, (x, y))
