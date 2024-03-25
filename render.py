import esper
from components import *

class RenderSystem(esper.Processor):
    def __init__(self, screen, camera):
        super().__init__()
        self.screen = screen
        self.camera = camera

    def process(self, dt):
        self.screen.fill((0,0,0))

        entities = esper.get_components(Position, Renderable)

        entities.sort(key=lambda ent: ent[1][1].z)

        for entity, (position, renderable) in entities:
            image = renderable.image

            x = position.x * self.camera.zoom + self.camera.offset_x
            y = position.y * self.camera.zoom + self.camera.offset_y - position.z
            if image:
                self.screen.blit(image, (x, y))
