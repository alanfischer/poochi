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
            y = position.y * self.camera.zoom + self.camera.offset_y - position.z
            if image:
                self.screen.blit(image, (x, y))

class RandomEncounterSystem(esper.Processor):
    def __init__(self, encounter_chance=0.05):
        self.encounter_chance = encounter_chance

    def process(self):
        # Check for player movement here
        # If player moved:
        if random.random() < self.encounter_chance:
            self.start_encounter()

    def start_encounter(self):
        # Start the battle sequence
        print("You ran into a slime!")
        # Transition to battle mode

def terrain_at(x, y):
    result = None
    for _, (terrain, pos) in esper.get_components(Terrain, Position):
        if pos.x == x and pos.y == y:
            result = terrain
    return result

class MovementSystem(esper.Processor):
    def __init__(self, random_encounter_system):
        super().__init__()
        self.random_encounter_system = random_encounter_system
        self.move_map = {
            pygame.K_LEFT: ((-TILE_SIZE, 0), 'left'),
            pygame.K_RIGHT: ((TILE_SIZE, 0), 'right'),
            pygame.K_UP: ((0, -TILE_SIZE), 'up'),
            pygame.K_DOWN: ((0, TILE_SIZE), 'down')
        }

    def process(self):
        time = pygame.time.get_ticks()  # Get the current time in milliseconds
        keys = pygame.key.get_pressed()
        for entity, (player, position, moveable, renderable) in esper.get_components(Player, Position, Moveable, Renderable):
            if time - player.last_frame_time > 300:
                player.frame = 1 - player.frame  # Toggle between 0 and 1
                player.last_frame_time = time  # Update the last frame switch time

            if moveable.target_x == None or moveable.target_y == None:
                moveable.target_x = position.x
                moveable.target_y = position.y

            # If we are are not moving moving, find next step
            if moveable.target_x == position.x and moveable.target_y == position.y:
                target_x, target_y = position.x, position.y
                for key, ((dx, dy), direction) in self.move_map.items():
                    if keys[key]:
                        target_x, target_y = target_x + dx, target_y + dy
                        player.direction = direction
                        break

                collision = False
                if (terrain := terrain_at(target_x, target_y)) is not None:
                    collision = (terrain.type == 'mountain' or terrain.type == 'water')

                if collision == False:
                    moveable.target_x = target_x
                    moveable.target_y = target_y

            move_speed = moveable.speed
            on_hill = False
            if (terrain := terrain_at(moveable.target_x, moveable.target_y)) is not None:
                if terrain.type == 'forest':
                    move_speed = move_speed * 0.75
                elif terrain.type == 'hill':
                    move_speed = move_speed * 0.5
                    on_hill = True

            # Smooth movement towards the target position
            if (position.x, position.y) != (moveable.target_x, moveable.target_y):
                x_diff = moveable.target_x - position.x
                y_diff = moveable.target_y - position.y
                
                dt = (abs(x_diff) + abs(y_diff)) / TILE_SIZE
                if on_hill:
                    if dt < 0.5:
                        position.z = dt * TILE_SIZE / 2
                    else:
                        position.z = (1 - dt) * TILE_SIZE / 2
                
                x_move = min(abs(x_diff), move_speed) * (1 if x_diff > 0 else -1)
                y_move = min(abs(y_diff), move_speed) * (1 if y_diff > 0 else -1)

                position.x += x_move if moveable.target_x != position.x else 0
                position.y += y_move if moveable.target_y != position.y else 0

            renderable.image = player.images[player.direction][player.frame]
     
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
random_encounter_system = RandomEncounterSystem()
movement_system = MovementSystem(random_encounter_system)
esper.add_processor(render_system)
esper.add_processor(movement_system)

# Create Player Entity
player_entity = esper.create_entity()
esper.add_component(player_entity, Player(player_images))
esper.add_component(player_entity, Renderable(player_images['left'][0], 2))
esper.add_component(player_entity, Moveable())
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

        color = world_map.get_at((x, y))
        name = get_name_from_color(color)

        z = 0
        # Add grass if necessary
        if name == 'grass' or name == 'mountain' or name == 'town' or name == 'forest' or name == 'hill' or get_tile_from_name(name) == None:
            grass = esper.create_entity()
            esper.add_component(grass, Renderable(get_tile_from_name('grass'), 0))
            esper.add_component(grass, Position(x * TILE_SIZE, y * TILE_SIZE))
            esper.add_component(grass, Terrain('grass'))
            if name == 'hill' or name == 'town':
                z = 1
            else:
                z = 3

        if name != 'grass':
            terrain = esper.create_entity()
            esper.add_component(terrain, Renderable(get_tile_from_name(name), z))
            esper.add_component(terrain, Position(x * TILE_SIZE, y * TILE_SIZE))
            esper.add_component(terrain, Terrain(name))

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
