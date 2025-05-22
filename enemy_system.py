import esper
import pygame
from components import *
from battle_system import Projectile

QUIRL_JUMP_STRENGTH = 130 # Define jump strength for Quirl
QUIRL_CLOSE_DISTANCE = 60 # Define how close the player needs to be for Quirl to jump

class EnemySystem(esper.Processor):
    def __init__(self):
        super().__init__()
        self.current_time = 0
        self.battle_end_time = None
        self.player_entity_id = None # To store player entity ID

    def process(self, dt):
        self.current_time = pygame.time.get_ticks() / 1000

        # Find player entity if not already found (only needed for Quirl's AI and touch-death)
        if self.player_entity_id is None:
            for entity, _ in esper.get_components(Player):
                self.player_entity_id = entity
                break

        player_pos = None
        player_renderable = None
        if self.player_entity_id and esper.entity_exists(self.player_entity_id):
             # Check if player components still exist, BattleSystem might delete/recreate player on world changes.
            if esper.has_component(self.player_entity_id, Position) and esper.has_component(self.player_entity_id, Renderable):
                player_pos = esper.component_for_entity(self.player_entity_id, Position)
                player_renderable = esper.component_for_entity(self.player_entity_id, Renderable) # For bounding box
            else:
                self.player_entity_id = None # Player components gone, reset to find next time

        # Update enemies
        for entity, (enemy, position, moveable, renderable, ai) in esper.get_components(Enemy, Position, Moveable, Renderable, EnemyAI):
            is_quirl = enemy.quirl
            self.is_quirl = is_quirl

            if is_quirl:
                # Quirl's Flee AI
                if player_pos:
                    if player_pos.x < position.x:
                        ai.move_direction = 1  # Player is to the left, Quirl flees right
                    else:
                        ai.move_direction = -1 # Player is to the right, Quirl flees left
                
                    # Quirl Jump AI
                    horizontal_distance = abs(player_pos.x - position.x)
                    if horizontal_distance <= QUIRL_CLOSE_DISTANCE and moveable.on_ground:
                        moveable.velocity_y = -QUIRL_JUMP_STRENGTH
                        moveable.on_ground = False

                # Quirl's Death on Touch with Player
                if player_pos and player_renderable:
                    quirl_rect = pygame.Rect(
                        int(position.x - renderable.image.get_width() // 2),
                        int(position.y - renderable.image.get_height() // 2),
                        renderable.image.get_width(),
                        renderable.image.get_height()
                    )
                    player_image = esper.component_for_entity(self.player_entity_id, Player).images[esper.component_for_entity(self.player_entity_id, Player).direction][0]
                    player_bbox = player_image.get_bounding_rect()
                    player_rect = pygame.Rect(
                        int(player_pos.x - player_bbox.width // 2),
                        int(player_pos.y - player_bbox.height // 2),
                        player_bbox.width,
                        player_bbox.height
                    )
                    if quirl_rect.colliderect(player_rect):
                        esper.delete_entity(entity) # Quirl dies
                        self.battle_end_time = self.current_time # End battle after a delay
                        continue # Skip further processing for this (now deleted) Quirl
            
            # Animate enemy (all enemies, including Quirl if not dead)
            if self.current_time - enemy.last_frame_time > 0.15:
                enemy.frame = 1 - enemy.frame
                enemy.last_frame_time = self.current_time

            # Apply AI-driven horizontal movement (Quirl's direction is set by flee AI)
            # Physics (gravity, vertical movement) is handled by BattleSystem for PhysicsAffected entities
            if not esper.has_component(entity, PhysicsAffected): # Only apply AI horizontal move if not physics affected (or handle differently)
                position.x += ai.move_direction * ai.move_speed * dt
            elif is_quirl: # Quirl is physics affected, but its horizontal movement is AI driven
                position.x += ai.move_direction * ai.move_speed * dt

            # Boundary checks (all enemies)
            if position.x >= ai.right_boundary:
                position.x = ai.right_boundary
                if not (is_quirl and player_pos and player_pos.x < position.x): # Don't flip if Quirl is fleeing into boundary
                    ai.move_direction = -1
            elif position.x <= ai.left_boundary:
                position.x = ai.left_boundary
                if not (is_quirl and player_pos and player_pos.x > position.x):
                    ai.move_direction = 1
            
            # Update direction based on move_direction for animation
            if ai.move_direction == 1:
                enemy.direction = 'right'
            else:
                enemy.direction = 'left'

            # Update renderable (all enemies)
            if enemy.frame < len(enemy.images[enemy.direction]):
                 renderable.image = enemy.images[enemy.direction][enemy.frame]
            else:
                 # Handle cases where frame index might be out of bounds if images have different frame counts
                 enemy.frame = 0 
                 renderable.image = enemy.images[enemy.direction][enemy.frame]

       # Check for battle end timer
        if self.battle_end_time is not None:
            if self.current_time - self.battle_end_time >= 1.0:
                if self.is_quirl:
                    # Stop any playing music
                    pygame.mixer.music.stop()
                    # Draw end screen
                    end_image = pygame.image.load("end.png")
                    end_image = pygame.transform.scale(end_image, (320, 240))  # Scale to screen size
                    pygame.display.get_surface().blit(end_image, (0,0))
                    pygame.display.flip()
                    # Wait for ESC
                    waiting = True
                    while waiting:
                        for event in pygame.event.get():
                            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                                pygame.quit()
                                exit()
                else:
                    esper.switch_world('map')
                self.battle_end_time = None
                self.player_entity_id = None # Reset player ID on world switch
                return

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