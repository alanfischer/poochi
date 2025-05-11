import esper
import pygame
import random
from components import *
from camera import *
from render import *
from encounter import *
from movement import *
from battle_movement import *

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

BACKGROUND_FILE = 'grass_background.png'

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

# Create Game Window
screen = pygame.display.set_mode((1600, 1000), pygame.RESIZABLE)
pygame.display.set_caption('Adventures of Poochi')
scene_surface = pygame.Surface((320, 240), pygame.SRCALPHA)

def setup_map():
    esper.switch_world("map")

    player_entity = esper.create_entity()
    esper.add_component(player_entity, Player(player_images))
    esper.add_component(player_entity, Renderable(player_images['left'][0], 2))
    esper.add_component(player_entity, Moveable())
    esper.add_component(player_entity, Position(*start_pos))

    camera_system = CameraSystem(esper.component_for_entity(player_entity, Position), scene_surface.get_width(), scene_surface.get_height())
    render_system = RenderSystem(scene_surface, camera_system)
    encounter_system = EncounterSystem(.5)
    movement_system = MovementSystem(camera_system, TILE_SIZE)
    esper.add_processor(camera_system)
    esper.add_processor(render_system)
    esper.add_processor(movement_system)
    esper.add_processor(encounter_system)


def setup_battle():
    esper.switch_world("battle")

    background = pygame.image.load(BACKGROUND_FILE)
    background = pygame.transform.scale(background, (scene_surface.get_width(), scene_surface.get_height()))

    player_entity = esper.create_entity()
    esper.add_component(player_entity, Player(player_images))
    esper.add_component(player_entity, Renderable(player_images['left'][0], 2))
    esper.add_component(player_entity, Moveable())
    esper.add_component(player_entity, Position(0,0))

    camera_system = CameraSystem(esper.component_for_entity(player_entity, Position), scene_surface.get_width(), scene_surface.get_height(), inner_rect_factor = 1.0)
    render_system = RenderSystem(scene_surface, camera_system, background)
    movement_system = BattleMovementSystem()
    esper.add_processor(camera_system)
    esper.add_processor(render_system)
    esper.add_processor(movement_system)


def get_tile_from_name(name):
    return random.choice(tiles.get(name, [None]))

def get_name_from_color(color):
    for key, value in COLORS.items():
        if value == color:
            return key
    return None

setup_map()
setup_battle()

esper.switch_world("map")

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

clock = pygame.time.Clock()

def game_loop():
    global screen
    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # Time elapsed in seconds since last tick
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                # Update the screen surface to the new size
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

        # Update ECS world
        esper.process(dt)

        scaled_surface = pygame.transform.scale(scene_surface, (screen.get_width(), screen.get_height()))
        screen.blit(scaled_surface, (0, 0))
    
        # Flip display
        pygame.display.flip()

    pygame.quit()

# Start the game
game_loop()
