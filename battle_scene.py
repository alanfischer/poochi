import esper
import pygame
import random
from components import *
from camera import *
from render import *
from battle_movement import *

# Battle Tiles
TILES = {
    'ledge': ['battle_grass.png'],
    'grass': ['battle_grass.png'],
    'grass_light': ['battle_grass.png']
}

COLORS = {
    'ledge': (184, 19, 29, 255),
    'grass': (184, 19, 29, 255),
    'grass_light': (184, 19, 29, 255)
}

# Load battle tiles
tiles = {color: [pygame.image.load(file) for file in files] for color, files in TILES.items()}

# Battle sprites
battle_player_sheet = pygame.image.load('harry_battle.png')
battle_player_images = {
    'left': [pygame.Surface((15, 32), pygame.SRCALPHA), pygame.Surface((15, 32), pygame.SRCALPHA)],
    'right': [pygame.Surface((15, 32), pygame.SRCALPHA), pygame.Surface((15, 32), pygame.SRCALPHA)],
    'jump_left': [pygame.Surface((15, 32), pygame.SRCALPHA)],
    'jump_right': [pygame.Surface((15, 32), pygame.SRCALPHA)],
    'fire_left': [pygame.Surface((21, 32), pygame.SRCALPHA)],
    'fire_right': [pygame.Surface((21, 32), pygame.SRCALPHA)],
}

peeves_sheet = pygame.image.load('peeves.png')
peeves_images = {
    'left': [pygame.Surface((16, 16), pygame.SRCALPHA), pygame.Surface((16, 16), pygame.SRCALPHA)],
    'right': [pygame.Surface((16, 16), pygame.SRCALPHA), pygame.Surface((16, 16), pygame.SRCALPHA)],
}

norris_sheet = pygame.image.load('norris.png')
norris_images = {
    'left': [pygame.Surface((16, 16), pygame.SRCALPHA), pygame.Surface((16, 16), pygame.SRCALPHA)],
    'right': [pygame.Surface((16, 16), pygame.SRCALPHA), pygame.Surface((16, 16), pygame.SRCALPHA)],
}

# Extract each image
battle_player_images['right'][0].blit(battle_player_sheet, (0, 0), (0, 0, 15, 32))
battle_player_images['right'][1].blit(battle_player_sheet, (0, 0), (16, 0, 15, 32))
battle_player_images['left'][0] = pygame.transform.flip(battle_player_images['right'][0], True, False)
battle_player_images['left'][1] = pygame.transform.flip(battle_player_images['right'][1], True, False)
battle_player_images['jump_right'][0].blit(battle_player_sheet, (0, 0), (53, 0, 15, 32))
battle_player_images['jump_left'][0] = pygame.transform.flip(battle_player_images['jump_right'][0], True, False)
battle_player_images['fire_right'][0].blit(battle_player_sheet, (0, 0), (32, 0, 21, 32))
battle_player_images['fire_left'][0] = pygame.transform.flip(battle_player_images['fire_right'][0], True, False)

peeves_images['right'][0].blit(peeves_sheet, (0, 0), (0, 0, 16, 16))
peeves_images['right'][1].blit(peeves_sheet, (0, 0), (16, 0, 16, 16))
peeves_images['left'][0] = pygame.transform.flip(peeves_images['right'][0], True, False)
peeves_images['left'][1] = pygame.transform.flip(peeves_images['right'][1], True, False)

norris_images['left'][0].blit(norris_sheet, (0, 0), (0, 0, 16, 16))
norris_images['left'][1].blit(norris_sheet, (0, 0), (16, 0, 16, 16))
norris_images['right'][0] = pygame.transform.flip(norris_images['left'][0], True, False)
norris_images['right'][1] = pygame.transform.flip(norris_images['left'][1], True, False)

def get_tile_from_name(name):
    return random.choice(tiles.get(name, [None]))

def get_tile_name_from_color(color):
    for key, value in COLORS.items():
        if value == color:
            return key
    return None

def create_battle(name, encounter_system, scene_surface, TILE_SIZE, battle_player_images):
    battle_world_name = "battle_" + name
    try:
        esper.delete_world(battle_world_name)  # Attempt to delete if it exists
    except KeyError:
        pass  # World didn't exist, which is fine

    esper.switch_world(battle_world_name) # Switch to the world (creates if it doesn't exist)

    background = pygame.image.load("background.png")
    background = pygame.transform.scale(background, (scene_surface.get_width(), scene_surface.get_height()))

    battle_map = pygame.image.load("grass_map_1.png")
    battle_size = battle_map.get_size()

    # Calculate the total size of the battle map in pixels
    total_map_width = battle_size[0] * TILE_SIZE
    total_map_height = battle_size[1] * TILE_SIZE
    
    # Calculate offsets to center the battle map
    offset_x = TILE_SIZE // 2 - total_map_width // 2
    offset_y = TILE_SIZE // 2 - total_map_height // 2

    movement_system = BattleMovementSystem(jump_strength=200)

    player_entity = esper.create_entity()
    esper.add_component(player_entity, Player(battle_player_images))
    esper.add_component(player_entity, Renderable(battle_player_images['left'][0], 2))
    esper.add_component(player_entity, Moveable(2))
    esper.add_component(player_entity, Position(0, movement_system.ground_y_position))

    camera_system = CameraSystem(esper.component_for_entity(player_entity, Position),
                                 scene_surface.get_width(),
                                 scene_surface.get_height(),
                                 start_offset=(0, 16*5),
                                 inner_rect_factor = 1.0,
                                 live_follow=False)
    render_system = RenderSystem(scene_surface, camera_system, TILE_SIZE, background)
    esper.add_processor(camera_system)
    esper.add_processor(render_system)
    esper.add_processor(movement_system)
    esper.add_processor(encounter_system)

    for x in range(battle_size[0]):
        for y in range(battle_size[1]):
            color = battle_map.get_at((x, y))
            name = get_tile_name_from_color(color)

            z = 0

            if name == 'ledge' or name == 'grass' or name == 'grass_light':
                terrain = esper.create_entity()
                esper.add_component(terrain, Renderable(get_tile_from_name(name), z))
                # Apply the offset to center the terrain
                terrain_x = offset_x + (x * TILE_SIZE)
                terrain_y = offset_y + (y * TILE_SIZE)
                esper.add_component(terrain, Position(terrain_x, terrain_y))
                esper.add_component(terrain, Terrain(name)) 