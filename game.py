import pygame
import numpy as np

# Initialize Pygame
pygame.init()

# Game Constants
TILE_SIZE = 16
MAP_FILE = 'Dad map.png'
TILES = {
    'green': 'Grass.png',
    'blue': 'water.png',
    'gray': 'mountain.png',
    'brown': 'town.png',
    'unknown': 'unknown.png'
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

# Load World Map
world_map = pygame.image.load(MAP_FILE)
world_size = world_map.get_size()
tiles = {}

# Load Tiles
for color, file in TILES.items():
    tiles[color] = pygame.image.load(file)

# Load Player
player_img_ = pygame.image.load(PLAYER_FILE)
player_img = pygame.Surface((16, 16))
player_img.blit(player_img_, (0, 0), (0, 0, 16, 16))
player_pos = [0, 0]

# Create Game Window
screen = pygame.display.set_mode((world_size[0]*TILE_SIZE, world_size[1]*TILE_SIZE))
pygame.display.set_caption('Tile Based Game')

def get_tile(color):
    for key, value in COLORS.items():
        if value == color:
            return tiles.get(key)
    return tiles.get('unknown')

def can_move(pos):
    x, y = pos
    if x < 0 or y < 0 or x >= world_size[0] or y >= world_size[1]:
        return False
    color = world_map.get_at((x, y))
    return color != COLORS['blue'] and color != COLORS['gray']

def find_player_start():
    for x in range(world_size[0]):
        for y in range(world_size[1]):
            if world_map.get_at((x, y)) == COLORS['pink']:
                return [x, y]

    return [0, 0]

def game_loop():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                x, y = player_pos
                if event.key == pygame.K_LEFT:
                    if can_move((x - 1, y)):
                        player_pos[0] -= 1
                elif event.key == pygame.K_RIGHT:
                    if can_move((x + 1, y)):
                        player_pos[0] += 1
                elif event.key == pygame.K_UP:
                    if can_move((x, y - 1)):
                        player_pos[1] -= 1
                elif event.key == pygame.K_DOWN:
                    if can_move((x, y + 1)):
                        player_pos[1] += 1

        # Render
        screen.fill((0, 0, 0))
        for x in range(world_size[0]):
            for y in range(world_size[1]):
                tile_color = world_map.get_at((x, y))
                tile = get_tile(tile_color)
                if tile:
                    screen.blit(tile, (x * TILE_SIZE, (y - 32) * TILE_SIZE))
        screen.blit(player_img, (player_pos[0] * TILE_SIZE, (player_pos[1] - 32) * TILE_SIZE))
        pygame.display.flip()

    pygame.quit()

player_pos = find_player_start()
game_loop()

