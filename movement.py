import esper
import pygame
from components import *
from cutscene_system import *

def terrain_at(x, y):
    result = None
    for _, (terrain, pos) in esper.get_components(Terrain, Position):
        if pos.x == x and pos.y == y:
            result = terrain
    return result


class MovementSystem(esper.Processor):
    def __init__(self, camera, tile_size, cutscene_system):
        super().__init__()
        self.camera = camera
        self.tile_size = tile_size
        self.cutscene_system = cutscene_system
        self.move_map = {
            pygame.K_LEFT: ((-tile_size, 0), 'left'),
            pygame.K_RIGHT: ((tile_size, 0), 'right'),
            pygame.K_UP: ((0, -tile_size), 'up'),
            pygame.K_DOWN: ((0, tile_size), 'down')
        }

    def process(self, dt):
        if self.camera.sliding:
            return

        time = pygame.time.get_ticks() / 1000
        keys = pygame.key.get_pressed()
        for entity, (player, position, moveable, renderable) in esper.get_components(Player, Position, Moveable, Renderable):
            if time - player.last_frame_time > 0.3:
                player.frame = 1 - player.frame  # Toggle between 0 and 1
                player.last_frame_time = time  # Update the last frame switch time

            if moveable.target_x == None or moveable.target_y == None:
                moveable.target_x = position.x
                moveable.target_y = position.y

            # If we are are not moving, find next step
            if moveable.target_x == position.x and moveable.target_y == position.y:
                target_x, target_y = position.x, position.y
                for key, ((dx, dy), direction) in self.move_map.items():
                    if keys[key]:
                        target_x, target_y = target_x + dx, target_y + dy
                        player.direction = direction
                        break

                collision = False
                if (terrain := terrain_at(target_x, target_y)) is not None:
                    collision = (terrain.type == 'mountain' or terrain.type == 'water' or terrain.type == 'pillar')
                    
                    # Check for cutscene trigger
                    for entity, (cutscene, pos) in esper.get_components(Cutscene, Position):
                        if pos.x == target_x and pos.y == target_y:
                            self.cutscene_system.start_cutscene(cutscene.image_path, cutscene.music_path)
                            return

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
                elif terrain.type == 'track':
                    move_speed = move_speed * 0.6

            # Smooth movement towards the target position
            if (position.x, position.y) != (moveable.target_x, moveable.target_y):
                x_diff = moveable.target_x - position.x
                y_diff = moveable.target_y - position.y

                dt = (abs(x_diff) + abs(y_diff)) / self.tile_size
                if on_hill:
                    if dt < 0.5:
                        position.z = dt * self.tile_size / 2
                    else:
                        position.z = (1 - dt) * self.tile_size / 2

                x_move = min(abs(x_diff), move_speed) * \
                    (1 if x_diff > 0 else -1)
                y_move = min(abs(y_diff), move_speed) * \
                    (1 if y_diff > 0 else -1)

                position.x += x_move if moveable.target_x != position.x else 0
                position.y += y_move if moveable.target_y != position.y else 0

                if position.x == moveable.target_x and position.y == moveable.target_y:
                    moveable.moved = True

            renderable.image = player.images[player.direction][player.frame]
