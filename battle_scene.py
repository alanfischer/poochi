import esper
import pygame
import random
from components import *
from camera import *
from render import *
from battle_system import *
from enemy_system import *

# Battle map configuration
TILES = {
    'ledge': ['battle_grass.png'],
    'grass': ['battle_grass.png'],
    'grass_light': ['battle_grass.png'],
    'stone': ['battle_stone.png']
}

COLORS = {
    'ledge': (184, 19, 29, 255),
    'grass': (184, 19, 29, 255),
    'grass_light': (184, 19, 29, 255),
    'stone': (184, 255, 29, 255)
}

ENEMY_OFFSET = {
    1: (160, -60),  # Peeves in upper right
    2: (160, -8),    # Norris in middle right
    3: (160, 20)     # Quirl in lower right
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

# Load and process Quirl sprites
quirl_sheet = pygame.image.load('quirl.png')
quirl_images = {
    'left': [pygame.Surface((12, 32), pygame.SRCALPHA), pygame.Surface((12, 32), pygame.SRCALPHA)],
    'right': [pygame.Surface((12, 32), pygame.SRCALPHA), pygame.Surface((12, 32), pygame.SRCALPHA)],
}

# Extract Quirl sprites
quirl_images['right'][0].blit(quirl_sheet, (0, 0), (0, 0, 12, 32))
quirl_images['right'][1].blit(quirl_sheet, (0, 0), (12, 0, 12, 32))
quirl_images['left'][0] = pygame.transform.flip(quirl_images['right'][0], True, False)
quirl_images['left'][1] = pygame.transform.flip(quirl_images['right'][1], True, False)


# ===== Helper Functions =====

def get_tile_from_name(name):
    return random.choice(tiles.get(name, [None]))

def get_tile_name_from_color(color):
    for key, value in COLORS.items():
        if value == color:
            return key
    return None

# ===== Main Battle Creation =====

def create_battle(number, encounter_system, scene_surface, TILE_SIZE):
    try:
        esper.delete_world("battle")  # Attempt to delete if it exists
    except KeyError:
        pass  # World didn't exist, which is fine

    esper.switch_world("battle")

    # Load and scale background
    if number == 3:
        background = pygame.image.load("quirl_background.png")
    else:
        background = pygame.image.load("background.png")
    background = pygame.transform.scale(background, (scene_surface.get_width(), scene_surface.get_height()))

    # Choose map and enemy based on number
    battle_map = pygame.image.load(f"grass_map_{number}.png")
    enemy_images = peeves_images if number == 1 else norris_images if number == 2 else quirl_images

    battle_size = battle_map.get_size()
 
    # Calculate the total size of the battle map in pixels
    total_map_width = battle_size[0] * TILE_SIZE
    total_map_height = battle_size[1] * TILE_SIZE
    
    # Calculate offsets to center the battle map
    offset_x = TILE_SIZE // 2 - total_map_width // 2
    offset_y = TILE_SIZE // 2 - total_map_height // 2

    # Create battle system
    battle_system = BattleSystem(jump_strength=200)

    # Create player
    player_entity = esper.create_entity()
    esper.add_component(player_entity, Player(battle_player_images))
    esper.add_component(player_entity, Renderable(battle_player_images['left'][0], 2))
    esper.add_component(player_entity, Moveable(2))
    esper.add_component(player_entity, Position(0, battle_system.ground_y_position))
    esper.add_component(player_entity, PhysicsAffected())

    # Create enemy
    enemy_entity = esper.create_entity()
    esper.add_component(enemy_entity, Enemy(enemy_images, number == 3))
    esper.add_component(enemy_entity, Renderable(enemy_images['right'][0], 2))
    esper.add_component(enemy_entity, Moveable(1))
    # Add PhysicsAffected component if it's Quirl
    if number == 3: # Assuming Quirl is battle number 3
        esper.add_component(enemy_entity, PhysicsAffected())
        esper.add_component(enemy_entity, EnemyAI(move_speed=100, left_boundary=-100, right_boundary=100))
    else:
        esper.add_component(enemy_entity, EnemyAI())

    # Position enemy based on map dimensions
    enemy_x = ENEMY_OFFSET[number][0]
    enemy_y = ENEMY_OFFSET[number][1]

    esper.add_component(enemy_entity, Position(enemy_x, enemy_y))

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
    esper.add_processor(battle_system)
    esper.add_processor(encounter_system)
    esper.add_processor(EnemySystem())

    # Create terrain
    for x in range(battle_size[0]):
        for y in range(battle_size[1]):
            color = battle_map.get_at((x, y))
            name = get_tile_name_from_color(color)
            z = 0

            if name == 'ledge' or name == 'grass' or name == 'grass_light' or name == 'stone':
                terrain = esper.create_entity()
                esper.add_component(terrain, Renderable(get_tile_from_name(name), z))
                # Apply the offset to center the terrain
                terrain_x = offset_x + (x * TILE_SIZE)
                terrain_y = offset_y + (y * TILE_SIZE)
                esper.add_component(terrain, Position(terrain_x, terrain_y))
                esper.add_component(terrain, Terrain(name)) 