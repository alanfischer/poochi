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
    'hill': ['hill_1.png', 'hill_2.png']
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

class Player:
    def __init__(self, images):
        self.images = images
        self.direction = 'left'
        self.frame = 0

class Collision:
    pass

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Camera:
    def __init__(self, follow_target, width, height, zoom=1.0):
        self.follow_target = follow_target
        self.width, self.height = width, height
        self.zoom = zoom
        self.offset_x, self.offset_y = 0, 0

    def update(self):
        if self.follow_target:
            self.offset_x = -self.follow_target.x * self.zoom + self.width // 2
            self.offset_y = -self.follow_target.y * self.zoom + self.height // 2

# Systems
class RenderSystem(esper.Processor):
    def __init__(self, screen, camera):
        super().__init__()
        self.screen = screen
        self.camera = camera

    def process(self):
        entities = esper.get_components(Position, Renderable)

        entities.sort(key=lambda ent: ent[1][1].z)
        
        for entity, (position, renderable) in entities:
            image = renderable.image
            
            x = position.x * self.camera.zoom + self.camera.offset_x
            y = position.y * self.camera.zoom + self.camera.offset_y
            if image:
                self.screen.blit(image, (x, y))
            else:
                pygame.draw.rect(self.screen, (0,0,0), (x, y, TILE_SIZE, TILE_SIZE))

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
        for entity, (player, position, renderable) in esper.get_components(Player, Position, Renderable):
            if entity not in self.target_positions:
                self.target_positions[entity] = (position.x, position.y)

            target_x, target_y = self.target_positions[entity]
            for key, (dx, dy) in self.move_map.items():
                if keys[key] and (position.x, position.y) == (target_x, target_y):
                    new_x = max(0, min(position.x + dx, (self.world_size[0] - 1) * TILE_SIZE))
                    new_y = max(0, min(position.y + dy, (self.world_size[1] - 1) * TILE_SIZE))

                    # Check for collision at the new position
                    collision = False
                    for _, (collidable, pos) in esper.get_components(Collision, Position):
                        if pos.x == new_x and pos.y == new_y:
                            collision = True
                            break

                    if not collision:
                        self.target_positions[entity] = (new_x, new_y)

            # Smooth movement towards the target position
            if (position.x, position.y) != (target_x, target_y):
                x_modifier = -1 if target_x < position.x else 1
                y_modifier = -1 if target_y < position.y else 1
                position.x += x_modifier * min(max(self.move_speed, target_x - position.x), self.move_speed) if target_x != position.x else 0
                position.y += y_modifier * min(max(self.move_speed, target_y - position.y), self.move_speed) if target_y != position.y else 0

            if position.x != target_x or position.y != target_y:
                player.frame = 1 - player.frame  # Toggle between 0 and 1

            if keys[pygame.K_RIGHT]:
                player.direction = 'right'
                renderable.image = player.images['right'][player.frame]
            elif keys[pygame.K_LEFT]:
                player.direction = 'left'
                renderable.image = player.images['left'][player.frame]
            elif keys[pygame.K_UP]:
                player.direction = 'up'
                renderable.image = player.images['up'][player.frame]
            elif keys[pygame.K_DOWN]:
                player.direction = 'down'
                renderable.image = player.images['down'][player.frame]

# Initialize Pygame
pygame.init()

# Load World Map
world_map = pygame.image.load(MAP_FILE)
world_size = world_map.get_size()
tiles = {color: [pygame.image.load(file) for file in files] for color, files in TILES.items()}

# Load Player
player_sheet = pygame.image.load(PLAYER_FILE)
player_images = {
    'left': [pygame.Surface((16, 16), pygame.SRCALPHA), pygame.Surface((16, 16), pygame.SRCALPHA)],
    'up': [pygame.Surface((16, 16), pygame.SRCALPHA), pygame.Surface((16, 16), pygame.SRCALPHA)],
    'down': [pygame.Surface((16, 16), pygame.SRCALPHA), pygame.Surface((16, 16), pygame.SRCALPHA)],
    'right': [pygame.Surface((16, 16), pygame.SRCALPHA), pygame.Surface((16, 16), pygame.SRCALPHA)]
}

# Extract each image
player_images['left'][0].blit(player_sheet, (0, 0), (0, 0, 16, 16))
player_images['left'][1].blit(player_sheet, (0, 0), (16, 0, 16, 16))
player_images['up'][0].blit(player_sheet, (0, 0), (32, 0, 16, 16))
player_images['up'][1] = pygame.transform.flip(player_images['up'][0], True, False)
player_images['down'][0].blit(player_sheet, (0, 0), (48, 0, 16, 16))
player_images['down'][1] = pygame.transform.flip(player_images['down'][0], True, False)
player_images['right'][0] = pygame.transform.flip(player_images['left'][0], True, False)
player_images['right'][1] = pygame.transform.flip(player_images['left'][1], True, False)

start_pos = None
for x in range(world_size[0]):
    for y in range(world_size[1]):
        if world_map.get_at((x, y)) == COLORS['start']:
            start_pos = (x * TILE_SIZE, y * TILE_SIZE)
            break
    if start_pos:
        break
player_pos_component = Position(*start_pos)

# Create Game Window
screen = pygame.display.set_mode((1600, 1000), pygame.RESIZABLE)
pygame.display.set_caption('Adventures of Poochi')
scene_surface = pygame.Surface((640, 480), pygame.SRCALPHA)

# Setup ECS
camera = Camera(player_pos_component, scene_surface.get_width(), scene_surface.get_height())
render_system = RenderSystem(scene_surface, camera)
movement_system = MovementSystem(world_map, world_size)
esper.add_processor(render_system)
esper.add_processor(movement_system)

# Create Player Entity
player_entity = esper.create_entity()
esper.add_component(player_entity, Player(player_images))
esper.add_component(player_entity, Renderable(player_images['left'][0], 1))
esper.add_component(player_entity, player_pos_component)

def get_tile_from_name(name):
    return random.choice(tiles.get(name, [None]))

def get_name_from_color(color):
    for key, value in COLORS.items():
        if value == color:
            return key
    return None

# Create Tile Entities
for x in range(world_size[0]):
    for y in range(world_size[1]):
        grass = esper.create_entity()

        name = get_name_from_color(world_map.get_at((x, y)))

        z = 0
        # Add grass if necessary
        if name == 'grass' or name == 'mountain' or name == 'town' or name == 'forest' or name == 'hill':
            grass = esper.create_entity()
            esper.add_component(grass, Renderable(get_tile_from_name('grass'), 0))
            esper.add_component(grass, Position(x * TILE_SIZE, y * TILE_SIZE))
            z = 2

        if name != 'grass':
            terrain = esper.create_entity()
            esper.add_component(terrain, Renderable(get_tile_from_name(name), z))
            esper.add_component(terrain, Position(x * TILE_SIZE, y * TILE_SIZE))

            if name == 'water' or name == 'mountain':
                esper.add_component(terrain, Collision())

def game_loop():
    global screen
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                # Update the screen surface to the new size
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

        # Rest of your game loop logic, such as rendering
        camera.update()

        # Update ECS world
        esper.process()

        scaled_surface = pygame.transform.scale(scene_surface, (screen.get_width(), screen.get_height()))
        screen.blit(scaled_surface, (0, 0))
    
        # Flip display
        pygame.display.flip()

    pygame.quit()

# Start the game
game_loop()
