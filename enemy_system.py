import esper
import pygame
from components import *
from battle_system import Projectile

class Enemy:
    def __init__(self, images):
        self.images = images
        self.direction = 'right'
        self.frame = 0
        self.last_frame_time = 0


class EnemyAI:
    def __init__(self):
        self.move_direction = 1  # 1 for right, -1 for left
        self.move_speed = 60  # pixels per second
        self.right_boundary = 100  # Same as player's right boundary
        self.left_boundary = 10  # Middle of screen


class EnemySystem(esper.Processor):
    def __init__(self):
        super().__init__()
        self.current_time = 0
        self.battle_end_time = None

    def process(self, dt):
        self.current_time = pygame.time.get_ticks() / 1000

        # Check for battle end timer
        if self.battle_end_time is not None:
            if self.current_time - self.battle_end_time >= 1.0:
                esper.switch_world('map')
                self.battle_end_time = None
                return

        # Update enemies
        for entity, (enemy, position, moveable, renderable, ai) in esper.get_components(Enemy, Position, Moveable, Renderable, EnemyAI):
            # Animate enemy
            if self.current_time - enemy.last_frame_time > 0.15:
                enemy.frame = 1 - enemy.frame
                enemy.last_frame_time = self.current_time

            # Move enemy
            position.x += ai.move_direction * ai.move_speed * dt

            # Check boundaries and reverse direction if needed
            if position.x >= ai.right_boundary:
                position.x = ai.right_boundary
                ai.move_direction = -1
                enemy.direction = 'left'
            elif position.x <= ai.left_boundary:
                position.x = ai.left_boundary
                ai.move_direction = 1
                enemy.direction = 'right'

            # Update renderable
            renderable.image = enemy.images[enemy.direction][enemy.frame]

        # Check for projectile collisions with enemies
        for projectile_entity, (proj_pos, projectile) in esper.get_components(Position, Projectile):
            for enemy_entity, (enemy, enemy_pos, enemy_renderable) in esper.get_components(Enemy, Position, Renderable):
                # Get projectile bounds
                proj_rect = pygame.Rect(
                    int(proj_pos.x - 4),  # Projectile is 8x8, centered
                    int(proj_pos.y - 4),
                    8, 8
                )

                # Get enemy bounds
                enemy_image = enemy_renderable.image
                enemy_bbox = enemy_image.get_bounding_rect()
                enemy_rect = pygame.Rect(
                    int(enemy_pos.x - enemy_bbox.width // 2),
                    int(enemy_pos.y - enemy_bbox.height // 2),
                    enemy_bbox.width,
                    enemy_bbox.height
                )
                
                # Check collision
                if proj_rect.colliderect(enemy_rect):
                    # Remove both the enemy and the projectile
                    esper.delete_entity(enemy_entity)
                    esper.delete_entity(projectile_entity)
                    # Set the battle end time
                    self.battle_end_time = self.current_time
                    break