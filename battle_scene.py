import esper
import pygame
import random
from components import *
from camera import *
from render import *
from battle_movement import *

# ===== Constants =====

# Battle map configuration
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

ENEMY_OFFSET = {
    1: (160, -60),  # Peeves in upper right
    2: (160, -8)    # Norris in middle right
}

# ===== Asset Loading =====

# Load battle tiles
tiles = {color: [pygame.image.load(file) for file in files] for color, files in TILES.items()}

# Load and process player sprites
battle_player_sheet = pygame.image.load('harry_battle.png')
battle_player_images = {
    'left': [pygame.Surface((15, 32), pygame.SRCALPHA), pygame.Surface((15, 32), pygame.SRCALPHA)],
    'right': [pygame.Surface((15, 32), pygame.SRCALPHA), pygame.Surface((15, 32), pygame.SRCALPHA)],
    'jump_left': [pygame.Surface((15, 32), pygame.SRCALPHA)],
    'jump_right': [pygame.Surface((15, 32), pygame.SRCALPHA)],
    'fire_left': [pygame.Surface((21, 32), pygame.SRCALPHA)],
    'fire_right': [pygame.Surface((21, 32), pygame.SRCALPHA)],
}

# Extract player sprites
battle_player_images['right'][0].blit(battle_player_sheet, (0, 0), (0, 0, 15, 32))
battle_player_images['right'][1].blit(battle_player_sheet, (0, 0), (16, 0, 15, 32))
battle_player_images['left'][0] = pygame.transform.flip(battle_player_images['right'][0], True, False)
battle_player_images['left'][1] = pygame.transform.flip(battle_player_images['right'][1], True, False)
battle_player_images['jump_right'][0].blit(battle_player_sheet, (0, 0), (53, 0, 15, 32))
battle_player_images['jump_left'][0] = pygame.transform.flip(battle_player_images['jump_right'][0], True, False)
battle_player_images['fire_right'][0].blit(battle_player_sheet, (0, 0), (32, 0, 21, 32))
battle_player_images['fire_left'][0] = pygame.transform.flip(battle_player_images['fire_right'][0], True, False)

# Load and process Peeves sprites
peeves_sheet = pygame.image.load('peeves.png')
peeves_images = {
    'left': [pygame.Surface((24, 24), pygame.SRCALPHA), pygame.Surface((24, 24), pygame.SRCALPHA)],
    'right': [pygame.Surface((24, 24), pygame.SRCALPHA), pygame.Surface((24, 24), pygame.SRCALPHA)],
}

# Extract and scale Peeves sprites
peeves_base_right_0 = pygame.Surface((16, 16), pygame.SRCALPHA)
peeves_base_right_1 = pygame.Surface((16, 16), pygame.SRCALPHA)
peeves_base_right_0.blit(peeves_sheet, (0, 0), (0, 0, 16, 16))
peeves_base_right_1.blit(peeves_sheet, (0, 0), (16, 0, 16, 16))

peeves_images['right'][0] = pygame.transform.scale(peeves_base_right_0, (24, 24))
peeves_images['right'][1] = pygame.transform.scale(peeves_base_right_1, (24, 24))
peeves_images['left'][0] = pygame.transform.flip(peeves_images['right'][0], True, False)
peeves_images['left'][1] = pygame.transform.flip(peeves_images['right'][1], True, False)

# Load and process Norris sprites
norris_sheet = pygame.image.load('norris.png')
norris_images = {
    'left': [pygame.Surface((16, 16), pygame.SRCALPHA), pygame.Surface((16, 16), pygame.SRCALPHA)],
    'right': [pygame.Surface((16, 16), pygame.SRCALPHA), pygame.Surface((16, 16), pygame.SRCALPHA)],
}

# Extract Norris sprites
norris_images['left'][0].blit(norris_sheet, (0, 0), (0, 0, 16, 16))
norris_images['left'][1].blit(norris_sheet, (0, 0), (16, 0, 16, 16))
norris_images['right'][0] = pygame.transform.flip(norris_images['left'][0], True, False)
norris_images['right'][1] = pygame.transform.flip(norris_images['left'][1], True, False)

# ===== Helper Functions =====

def get_tile_from_name(name):
    return random.choice(tiles.get(name, [None]))

def get_tile_name_from_color(color):
    for key, value in COLORS.items():
        if value == color:
            return key
    return None

# ===== Main Battle Creation =====

def create_battle(number, encounter_system, scene_surface, TILE_SIZE, battle_player_images):
    battle_world_name = f"battle_{number}"
    try:
        esper.delete_world(battle_world_name)  # Attempt to delete if it exists
    except KeyError:
        pass  # World didn't exist, which is fine

    esper.switch_world(battle_world_name) # Switch to the world (creates if it doesn't exist)

    # Load and scale background
    background = pygame.image.load("background.png")
    background = pygame.transform.scale(background, (scene_surface.get_width(), scene_surface.get_height()))

    # Choose map and enemy based on number
    battle_map = pygame.image.load(f"grass_map_{number}.png")
    enemy_images = peeves_images if number == 1 else norris_images

    battle_size = battle_map.get_size()

    # Calculate the total size of the battle map in pixels
    total_map_width = battle_size[0] * TILE_SIZE
    total_map_height = battle_size[1] * TILE_SIZE
    
    # Calculate offsets to center the battle map
    offset_x = TILE_SIZE // 2 - total_map_width // 2
    offset_y = TILE_SIZE // 2 - total_map_height // 2

    # Create movement system
    movement_system = BattleMovementSystem(jump_strength=200)

    # Create player
    player_entity = esper.create_entity()
    esper.add_component(player_entity, Player(battle_player_images))
    esper.add_component(player_entity, Renderable(battle_player_images['left'][0], 2))
    esper.add_component(player_entity, Moveable(2))
    esper.add_component(player_entity, Position(0, movement_system.ground_y_position))

    # Create enemy
    enemy_entity = esper.create_entity()
    esper.add_component(enemy_entity, Enemy(enemy_images))
    esper.add_component(enemy_entity, Renderable(enemy_images['right'][0], 2))
    esper.add_component(enemy_entity, Moveable(1))

    # Position enemy based on map dimensions
    enemy_x = ENEMY_OFFSET[number][0]
    enemy_y = ENEMY_OFFSET[number][1]

    esper.add_component(enemy_entity, Position(enemy_x, enemy_y))
    esper.add_component(enemy_entity, EnemyAI())  # New component for enemy behavior

    # Create and add systems
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
    esper.add_processor(EnemySystem())  # Add enemy system

    # Create terrain
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