import esper
import pygame

# Game Constants
TILE_SIZE = 16
MAP_FILE = 'dad_map.png'
TILES = {
    'green': 'grass.png',
    'blue': 'water.png',
    'gray': 'mountain_1.png',
    'brown': 'town.png',
    'unknown': 'tree.png'
}
PLAYER_FILE = 'poochi.png'

# Colors
COLORS = {
    'green': (0, 249, 0),
    'blue': (4, 51, 255),
    'gray': (192, 192, 192),
    'darkgreen': (0, 100, 0),
    'brown': (148, 82, 0),
    'pink': (255, 0, 255)
}

# Components
class Renderable:
    def __init__(self, image, z):
        self.image = image
        self.z = z

class Movable:
    pass

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# Systems
class RenderSystem(esper.Processor):
    def __init__(self, screen):
        super().__init__()
        self.screen = screen

    def process(self):
        entities = [(ent, *comp) for ent, comp in esper.get_components(Position, Renderable)]
        entities.sort(key=lambda x: x[-1].z if len(x) == 3 else 0)
        for ent, position, renderable in entities:
            self.screen.blit(renderable.image, (position.x, position.y))

class MovementSystem(esper.Processor):
    def __init__(self, world_map, world_size):
        super().__init__()
        self.world_map = world_map
        self.world_size = world_size
        self.move_map = {
            pygame.K_LEFT: (-1, 0),
            pygame.K_RIGHT: (1, 0),
            pygame.K_UP: (0, -1),
            pygame.K_DOWN: (0, 1),
        }

    def process(self):
        keys = pygame.key.get_pressed()
        for entity, (movable, position) in esper.get_components(Movable, Position):
            for key, (dx, dy) in self.move_map.items():
                if keys[key]:
                    new_x = max(0, min(position.x + dx * TILE_SIZE, (self.world_size[0] - 1) * TILE_SIZE))
                    new_y = max(0, min(position.y + dy * TILE_SIZE, (self.world_size[1] - 1) * TILE_SIZE))
                    position.x, position.y = new_x, new_y


# Initialize Pygame
pygame.init()

# Load World Map
world_map = pygame.image.load(MAP_FILE)
world_size = world_map.get_size()
tiles = {color: pygame.image.load(file) for color, file in TILES.items()}

# Load Player
player_img_ = pygame.image.load(PLAYER_FILE)
player_img = pygame.Surface((16, 16))
player_img.blit(player_img_, (0, 0), (0, 0, 16, 16))
player_pos = [0, 0]

# Create Game Window
screen = pygame.display.set_mode((world_size[0]*TILE_SIZE, world_size[1]*TILE_SIZE))
pygame.display.set_caption('Adventures of Poochi')

# Setup ECS
render_system = RenderSystem(screen)
movement_system = MovementSystem(world_map, world_size)
esper.add_processor(render_system)
esper.add_processor(movement_system)

# Create Player Entity
player_entity = esper.create_entity()
esper.add_component(player_entity, Renderable(player_img, 1))
esper.add_component(player_entity, Movable())
esper.add_component(player_entity, Position(*player_pos))

def get_tile(color):
    for key, value in COLORS.items():
        if value == color:
            return tiles.get(key, tiles['unknown'])
        else:
            return tiles['unknown']


# Create Tile Entities
for x in range(world_size[0]):
    for y in range(world_size[1]):
        tile_entity = esper.create_entity()
        tile_color = world_map.get_at((x, y))
        tile = get_tile(tile_color)
        esper.add_component(tile_entity, Renderable(tile, 0))
        esper.add_component(tile_entity, Position(x * TILE_SIZE, y * TILE_SIZE))

def game_loop():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update ECS world
        esper.process()

        # Flip display
        pygame.display.flip()

    pygame.quit()

# Start the game
game_loop()
