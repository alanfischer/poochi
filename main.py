import esper
import pygame
import random
import asyncio
from components import *
from camera import *
from render import *
from encounter import *
from movement import *
from battle_system import *
from music_system import MusicSystem

# Game Constants
TILE_SIZE = 16
MAP_FILE = 'hogwarts.png'
TILES = {
    # World
    'grass': ['grass.png'],
    'water': ['water.png'],
    'mountain': ['mountain_1.png', 'mountain_2.png', 'mountain_3.png'],
    'town': ['town.png'],
    'forest': ['tree.png'],
    'hill': ['hill_1.png', 'hill_2.png'],
    'hut': ['hut.png'],
    'flute': ['flute.png'],
    'pillar': ['pillar.png'],
    'hogwarts_castle': ['hogwart_castle.png'],
}
PLAYER_FILE = 'harry.png'

BACKGROUND_FILE = 'background.png'

COLORS = {
    # World
    'grass': (0, 249, 0, 255),
    'water': (4, 51, 255, 255),
    'hill': (219, 116, 114, 255),
    'forest': (0, 143, 0, 255),
    'mountain': (48, 48, 48, 255),
    'town': (0, 82, 0, 255),
    'path': (148, 82, 0, 255),
    'start': (182, 234, 255, 255),
    'track': (198, 203, 135, 255),
    'hut': (100, 100, 100, 255),
    'flute': (0, 0, 200, 255),
    'pillar': (165, 165, 165, 255),
    'hogwarts_castle': (255, 0, 0, 255),
}

# Cache path sprites
PATH_SPRITES = {
    'horizontal': pygame.image.load('path-horizontal.png'),
    'vertical': pygame.image.load('path-vertical.png'),
    'split_up': pygame.image.load('3_split_up.png'),
    'split_down': pygame.image.load('3_split_down.png'),
    'split_left': pygame.image.load('3_split_left.png'),
    'split_right': pygame.image.load('3_split_right.png'),
    'left_to_bottom': pygame.image.load('left_to_bottom_path.png'),
    'bottom_to_right': pygame.image.load('bottom_to_right_path.png'),
    'right_to_top': pygame.image.load('right_to_top_path.png'),
    'top_to_left': pygame.image.load('top_to_left_path.png'),
    'top_end': pygame.image.load('top_path_end.png'),
    'bottom_end': pygame.image.load('bottom_path_end.png'),
    'left_end': pygame.image.load('left_path_end.png'),
    'right_end': pygame.image.load('right_path_end.png')
}

TRACK_SPRITES = {
    'horizontal': pygame.image.load('track_horizontal.png'),
    'vertical': pygame.image.load('track_vertical.png'),
    #'split_up': pygame.image.load('track_3_split_up.png'),
    #'split_left': pygame.image.load('track_3_split_left.png'),
    #'split_right': pygame.image.load('track_3_split_right.png'),
    'left_to_bottom': pygame.image.load('left_to_bottom_track.png'),
    'bottom_to_right': pygame.image.load('bottom_to_right_track.png'),
    'right_to_top': pygame.image.load('right_to_top_track.png'),
    'top_to_left': pygame.image.load('top_to_left_track.png'),
    #'top_end': pygame.image.load('track_top_end.png'),
    #'bottom_end': pygame.image.load('track_bottom_end.png'),
    #'left_end': pygame.image.load('track_left_end.png'),
    #'right_end': pygame.image.load('track_right_end.png')
}

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Load World Map
world_map = pygame.image.load(MAP_FILE)
world_size = world_map.get_size()
tiles = {color: [pygame.image.load(file) for file in files] for color, files in TILES.items()}

# Load Player
player_sheet = pygame.image.load(PLAYER_FILE)
player_images = {
    'left': [pygame.Surface((6, 16), pygame.SRCALPHA), pygame.Surface((6, 16), pygame.SRCALPHA)],
    'up': [pygame.Surface((8, 16), pygame.SRCALPHA), pygame.Surface((8, 16), pygame.SRCALPHA)],
    'down': [pygame.Surface((8, 16), pygame.SRCALPHA), pygame.Surface((8, 16), pygame.SRCALPHA)],
    'right': [pygame.Surface((6, 16), pygame.SRCALPHA), pygame.Surface((6, 16), pygame.SRCALPHA)]
}

# Extract each image
player_images['right'][0].blit(player_sheet, (0, 0), (32, 0, 6, 16))
player_images['right'][1].blit(player_sheet, (0, 0), (38, 0, 6, 16))
player_images['up'][0].blit(player_sheet, (0, 0), (16, 0, 8, 16))
player_images['up'][1].blit(player_sheet, (0, 0), (24, 0, 8, 16))
player_images['down'][0].blit(player_sheet, (0, 0), (0, 0, 8, 16))
player_images['down'][1].blit(player_sheet, (0, 0), (8, 0, 8, 16))
player_images['left'][0] = pygame.transform.flip(player_images['right'][0], True, False)
player_images['left'][1] = pygame.transform.flip(player_images['right'][1], True, False)

start_pos = None
for x in range(world_size[0]):
    for y in range(world_size[1]):
        if world_map.get_at((x, y)) == COLORS['start']:
            start_pos = (x * TILE_SIZE, y * TILE_SIZE)
            break
    if start_pos:
        break

# Create Game Window
screen = pygame.display.set_mode((320, 240), pygame.RESIZABLE | pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SCALED, vsync=1)
pygame.display.set_caption('Adventures of Poochi')
scene_surface = pygame.Surface((320, 240), pygame.SRCALPHA)

# Enable vsync
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.VIDEORESIZE])

def get_tile_from_name(name):
    return random.choice(tiles.get(name, [None]))

def get_tile_name_from_color(color):
    for key, value in COLORS.items():
        if value == color:
            return key
    return None

def get_path_connections(x, y, world_map):
    connections = PathConnections()
    path_color = COLORS['path']
    
    # Check adjacent tiles
    if y > 0 and world_map.get_at((x, y - 1)) == path_color:
        connections.up = True
    if y < world_map.get_height() - 1 and world_map.get_at((x, y + 1)) == path_color:
        connections.down = True
    if x > 0 and world_map.get_at((x - 1, y)) == path_color:
        connections.left = True
    if x < world_map.get_width() - 1 and world_map.get_at((x + 1, y)) == path_color:
        connections.right = True
        
    return connections

def get_path_sprite(connections):
    # Check for 3-way splits first
    if connections.left and connections.right:
        if connections.up and not connections.down:
            return PATH_SPRITES['split_up']
        elif connections.down and not connections.up:
            return PATH_SPRITES['split_down']
    if connections.up and connections.down:
        if connections.left and not connections.right:
            return PATH_SPRITES['split_left']
        elif connections.right and not connections.left:
            return PATH_SPRITES['split_right']
    
    # Check for curved paths (corners)
    if connections.left and connections.down and not connections.right and not connections.up:
        return PATH_SPRITES['left_to_bottom']
    if connections.down and connections.right and not connections.left and not connections.up:
        return PATH_SPRITES['bottom_to_right']
    if connections.right and connections.up and not connections.left and not connections.down:
        return PATH_SPRITES['right_to_top']
    if connections.up and connections.left and not connections.right and not connections.down:
        return PATH_SPRITES['top_to_left']
    
    # Check for path ends (only one connection)
    if connections.up and not (connections.down or connections.left or connections.right):
        return PATH_SPRITES['bottom_end']  # Path ends at bottom, connects upward
    if connections.down and not (connections.up or connections.left or connections.right):
        return PATH_SPRITES['top_end']  # Path ends at top, connects downward
    if connections.left and not (connections.up or connections.down or connections.right):
        return PATH_SPRITES['right_end']  # Path ends at right, connects leftward
    if connections.right and not (connections.up or connections.down or connections.left):
        return PATH_SPRITES['left_end']  # Path ends at left, connects rightward
    
    # If connected only vertically (up/down), use vertical sprite
    if (connections.up or connections.down) and not (connections.left or connections.right):
        return PATH_SPRITES['vertical']
    
    # Otherwise use horizontal sprite (default)
    return PATH_SPRITES['horizontal']

def get_track_connections(x, y, world_map):
    connections = TrackConnections()
    track_color = COLORS['track']
    # Check adjacent tiles
    if y > 0 and world_map.get_at((x, y - 1)) == track_color:
        connections.up = True
    if y < world_map.get_height() - 1 and world_map.get_at((x, y + 1)) == track_color:
        connections.down = True
    if x > 0 and world_map.get_at((x - 1, y)) == track_color:
        connections.left = True
    if x < world_map.get_width() - 1 and world_map.get_at((x + 1, y)) == track_color:
        connections.right = True

    return connections

def get_track_sprite(connections):
    # Check for 3-way splits first
    #if connections.left and connections.right:
        #if connections.up and not connections.down:
            #return TRACK_SPRITES['split_up']
        #elif connections.down and not connections.up:
            #return TRACK_SPRITES['split_down']
    # if connections.up and connections.down:
        # if connections.left and not connections.right:
            # return TRACK_SPRITES['split_left']
        # elif connections.right and not connections.left:
            # return TRACK_SPRITES['split_right']
    # Check for curved tracks (corners)
    if connections.left and connections.down and not connections.right and not connections.up:
        return TRACK_SPRITES['left_to_bottom']
    if connections.down and connections.right and not connections.left and not connections.up:
        return TRACK_SPRITES['bottom_to_right']
    if connections.right and connections.up and not connections.left and not connections.down:
        return TRACK_SPRITES['right_to_top']
    if connections.up and connections.left and not connections.right and not connections.down:
        return TRACK_SPRITES['top_to_left']
    # Check for track ends (only one connection)
    #if connections.up and not (connections.down or connections.left or connections.right):
        #return TRACK_SPRITES['bottom_end']
    #if connections.down and not (connections.up or connections.left or connections.right):
        #return TRACK_SPRITES['top_end']
    #if connections.left and not (connections.up or connections.down or connections.right):
        #return TRACK_SPRITES['right_end']
    #if connections.right and not (connections.up or connections.down or connections.left):
        #return TRACK_SPRITES['left_end']
    # If connected only vertically (up/down), use vertical sprite
    if (connections.up or connections.down) and not (connections.left or connections.right):
        return TRACK_SPRITES['vertical']
    # Otherwise use horizontal sprite (default)
    return TRACK_SPRITES['horizontal']

def setup_map():
    esper.switch_world("map")

    player_entity = esper.create_entity()
    esper.add_component(player_entity, Player(player_images))
    esper.add_component(player_entity, Renderable(player_images['left'][0], 2))
    esper.add_component(player_entity, Moveable(1))
    esper.add_component(player_entity, Position(*start_pos))

    camera_system = CameraSystem(esper.component_for_entity(player_entity, Position), scene_surface.get_width(), scene_surface.get_height())
    render_system = RenderSystem(scene_surface, camera_system, TILE_SIZE)
    cutscene_system = CutsceneSystem(scene_surface, render_system)
    encounter_system = EncounterSystem(scene_surface, cutscene_system, TILE_SIZE, 0.05)
    movement_system = MovementSystem(camera_system, cutscene_system, TILE_SIZE, encounter_system)
    music_system = MusicSystem(cutscene_system)
    cutscene_system.set_music_system(music_system)

    esper.add_processor(camera_system)
    esper.add_processor(render_system)
    esper.add_processor(movement_system)
    esper.add_processor(encounter_system)
    esper.add_processor(cutscene_system)
    esper.add_processor(music_system)

    for x in range(world_size[0]):
        for y in range(world_size[1]):
            # Always create grass first
            grass = esper.create_entity()
            esper.add_component(grass, Renderable(get_tile_from_name('grass'), 0))
            esper.add_component(grass, Position(x * TILE_SIZE, y * TILE_SIZE))
            esper.add_component(grass, Terrain('grass'))

            color = world_map.get_at((x, y))
            name = get_tile_name_from_color(color)

            z = 0
            if name == 'grass':
                z = 0
            elif name == 'hogwarts_castle' or name == 'hill' or name == 'town' or name == 'path' or name == 'track' or name == 'hut' or name == 'flute':
                z = 1
            else:
                z = 3

            if name != 'grass':
                terrain = esper.create_entity()
                # Special handling for path tiles
                if name == 'path':
                    connections = get_path_connections(x, y, world_map)
                    path_sprite = get_path_sprite(connections)
                    esper.add_component(terrain, Renderable(path_sprite, z))
                    esper.add_component(terrain, connections)
                elif name == 'track':
                    connections = get_track_connections(x, y, world_map)
                    track_sprite = get_track_sprite(connections)
                    esper.add_component(terrain, Renderable(track_sprite, z))
                    esper.add_component(terrain, connections)
                elif name == 'hogwarts_castle':
                    esper.add_component(terrain, Cutscene('hogwarts_cutscene.png', 'hogwarts.mp3', 'hogwarts_cutscene'))
                    esper.add_component(terrain, Renderable(get_tile_from_name(name), z))
                elif name == 'hut':
                    esper.add_component(terrain, Cutscene('hagrid_cutscene.png', 'hagrid.mp3', 'hagrid_cutscene'))
                    esper.add_component(terrain, Renderable(get_tile_from_name(name), z))
                elif name == 'flute':
                    esper.add_component(terrain, Cutscene('flute_cutscene.png', 'flute.mp3', 'flute_cutscene'))
                    esper.add_component(terrain, Renderable(get_tile_from_name(name), z))
                else:
                    esper.add_component(terrain, Renderable(get_tile_from_name(name), z))
                esper.add_component(terrain, Position(x * TILE_SIZE, y * TILE_SIZE))
                esper.add_component(terrain, Terrain(name))

setup_map()

esper.switch_world("map")

clock = pygame.time.Clock()

async def main():
    global screen
    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # Time elapsed in seconds since last tick
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update ECS world
        esper.process(dt)

        screen.blit(scene_surface, (0,0)) # Blit the 320x240 scene_surface to the 320x240 logical screen
    
        # Flip display
        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())