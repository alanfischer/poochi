import esper
import pygame
import random

# Game Constants
TILE_SIZE = 16
MAP_FILE = 'dad_map.png'
TILES = {
    'grass': ['grass.png'],
    'water': ['water.png'],
    'mountain': ['mountain_1.png', 'mountain_2.png', 'mountain_3.png'],
    'town': ['town.png'],
    'forest': ['tree.png'],
    'hill': ['hill_1.png', 'hill_2.png'],
    'unknown': ['water.png']
}
PLAYER_FILE = 'poochi.png'

# Colors
COLORS = {
    'grass': (0, 249, 0, 255),
    'water': (4, 51, 255, 255),
    'mountain': (192, 192, 192, 255),
    'forest': (0, 143, 0, 255),
    'hill': (146, 144, 0, 255),
    'town': (148, 82, 0, 255),
    'start': (255, 0, 255, 255)
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
    def __init__(self, world_map, world_size, move_speed=8):
        super().__init__()
        self.world_map = world_map
        self.world_size = world_size
        self.move_speed = move_speed  # Smaller value for smoother movement
        self.move_map = {
            pygame.K_LEFT: (-TILE_SIZE, 0),
            pygame.K_RIGHT: (TILE_SIZE, 0),
            pygame.K_UP: (0, -TILE_SIZE),
            pygame.K_DOWN: (0, TILE_SIZE),
        }
        self.target_positions = {}

    def process(self):
        keys = pygame.key.get_pressed()
        for entity, (movable, position) in esper.get_components(Movable, Position):
            if entity not in self.target_positions:
                self.target_positions[entity] = (position.x, position.y)

            target_x, target_y = self.target_positions[entity]
            for key, (dx, dy) in self.move_map.items():
                if keys[key] and (position.x, position.y) == (target_x, target_y):
                    target_x = max(0, min(position.x + dx, (self.world_size[0] - 1) * TILE_SIZE))
                    target_y = max(0, min(position.y + dy, (self.world_size[1] - 1) * TILE_SIZE))
                    self.target_positions[entity] = (target_x, target_y)

            # Smooth movement towards the target position
            if (position.x, position.y) != (target_x, target_y):
                x_modifier = -1 if target_x < position.x else 1
                y_modifier = -1 if target_y < position.y else 1
                position.x += x_modifier * min(max(self.move_speed, target_x - position.x), self.move_speed) if target_x != position.x else 0
                position.y += y_modifier * min(max(self.move_speed, target_y - position.y), self.move_speed) if target_y != position.y else 0


# Initialize Pygame
pygame.init()

# Load World Map
world_map = pygame.image.load(MAP_FILE)
world_size = world_map.get_size()
tiles = {color: [pygame.image.load(file) for file in files] for color, files in TILES.items()}

# Load Player
player_img_ = pygame.image.load(PLAYER_FILE)
player_img = pygame.Surface((16, 16), pygame.SRCALPHA)
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

def get_tile_from_name(name):
    return random.choice(tiles.get(name, tiles['unknown']))

def get_tile_from_color(color):
    for key, value in COLORS.items():
        if value == color:
            return get_tile_from_name(key)
    return tiles['unknown'][0]

# Create Tile Entities
for x in range(world_size[0]):
    for y in range(world_size[1]):
        grass = esper.create_entity()
        esper.add_component(grass, Renderable(get_tile_from_name('grass'), 0))
        esper.add_component(grass, Position(x * TILE_SIZE, y * TILE_SIZE))

        terrain_image = get_tile_from_color(world_map.get_at((x, y)))
        if terrain_image != get_tile_from_name('grass'):
            terrain = esper.create_entity()
            esper.add_component(terrain, Renderable(terrain_image, 2))
            esper.add_component(terrain, Position(x * TILE_SIZE, y * TILE_SIZE))

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
