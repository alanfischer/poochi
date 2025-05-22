import pygame
import esper
from components import *

class Projectile:
    def __init__(self, direction, speed, created_at):
        self.direction = direction
        self.speed = speed
        self.created_at = created_at

class BattleSystem(esper.Processor):
    def __init__(self, gravity=200, jump_strength=120, move_speed=2):
        super().__init__()
        self.gravity = gravity
        self.jump_strength = jump_strength
        self.move_speed = move_speed * 60  # Scale for pixels per second
        self.ground_y_position = 16*5
        # Add boundary constraints
        self.left_boundary = -140
        self.right_boundary = 140

    def animate(self, player):
        time = pygame.time.get_ticks() / 1000
        if time - player.last_frame_time > 0.15:
            player.frame = 1 - player.frame  # Toggle between 0 and 1
            player.last_frame_time = time  # Update the last frame switch time

    def create_projectile(self, x, y, direction):
        # Create a new entity for the projectile
        projectile = esper.create_entity()
        # Add components
        esper.add_component(projectile, Position(x=x, y=y))
        esper.add_component(projectile, Projectile(
            direction=direction,
            speed=200,  # units per second
            created_at=pygame.time.get_ticks() / 1000
        ))
        # Add a renderable component for the projectile
        surface = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(surface, (255, 0, 0), (4, 4), 4)
        esper.add_component(projectile, Renderable(image=surface, z=1))

    def process(self, dt):
        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks() / 1000

        # Update projectiles
        for entity, (position, projectile) in esper.get_components(Position, Projectile):
            # Remove expired projectiles
            if current_time - projectile.created_at >= 1.0:
                esper.delete_entity(entity)
                continue
            
            # Update projectile position
            if projectile.direction == 'right':
                position.x += projectile.speed * dt
            else:
                position.x -= projectile.speed * dt

        # Process entities with physics (Player and PhysicsAffected enemies like Quirl)
        for entity, (pos, moveable, renderable, _) in esper.get_components(Position, Moveable, Renderable, PhysicsAffected):
            is_player_entity = esper.has_component(entity, Player)
            
            entity_width = 0
            entity_height = 0

            if is_player_entity:
                player = esper.component_for_entity(entity, Player)
                base_image = player.images[player.direction][0]
                bbox = base_image.get_bounding_rect()
                entity_width = bbox.width
                entity_height = bbox.height
                
                # Player-specific input and actions
                # Handle firing
                if keys[pygame.K_f] and player.firing_start_time is None:
                    player.firing_start_time = current_time
                    self.create_projectile(pos.x, pos.y, player.direction)
                elif player.firing_start_time is not None and current_time - player.firing_start_time >= 0.25:
                    player.firing_start_time = None

                # Horizontal movement for player
                dx = 0
                if keys[pygame.K_LEFT]:
                    dx = -self.move_speed * dt
                    player.direction = 'left'
                    self.animate(player)
                elif keys[pygame.K_RIGHT]:
                    dx = self.move_speed * dt
                    player.direction = 'right'
                    self.animate(player)

                if dx != 0:
                    remaining_dx = dx
                    step_size = 1 if dx > 0 else -1
                    while abs(remaining_dx) > 0:
                        this_step = step_size if abs(remaining_dx) > 1 else remaining_dx
                        pos.x += this_step
                        entity_rect = pygame.Rect(
                            int(pos.x - entity_width // 2), int(pos.y - entity_height // 2),
                            entity_width, entity_height
                        )
                        if self.get_colliding_tiles(entity_rect):
                            pos.x -= this_step
                            break
                        remaining_dx -= this_step
                    moveable.on_ground = self.check_if_on_ground(pos, entity_width, entity_height, is_player_entity)

                # Enforce horizontal boundaries for Player
                if pos.x < self.left_boundary:
                    pos.x = self.left_boundary
                elif pos.x > self.right_boundary:
                    pos.x = self.right_boundary
                
                # Player Jumping
                if keys[pygame.K_SPACE] and moveable.on_ground:
                    moveable.velocity_y = -self.jump_strength
                    moveable.on_ground = False
                
                if keys[pygame.K_ESCAPE]:
                    esper.switch_world('map')

            else: # For non-player PhysicsAffected entities (e.g., Quirl)
                # AI or other non-player movement will be handled by EnemySystem for Quirl
                # Here we just need to get its dimensions for physics
                enemy_comp = esper.component_for_entity(entity, Enemy) # Assuming Quirl has Enemy component
                base_image = enemy_comp.images[enemy_comp.direction][0] # Use current direction/frame
                bbox = base_image.get_bounding_rect()
                entity_width = bbox.width
                entity_height = bbox.height


            # Common Physics: Gravity and Vertical Collision for all PhysicsAffected entities
            moveable.velocity_y += self.gravity * dt
            max_fall_speed = 300
            moveable.velocity_y = min(moveable.velocity_y, max_fall_speed)
            
            dy = moveable.velocity_y * dt
            
            was_on_ground = moveable.on_ground
            
            if dy != 0:
                remaining_dy = dy
                step_size = 1 if dy > 0 else -1
                
                if step_size < 0 or not was_on_ground:
                    moveable.on_ground = False
                
                while abs(remaining_dy) > 0:
                    this_step = step_size if abs(remaining_dy) > 1 else remaining_dy
                    pos.y += this_step
                    entity_rect = pygame.Rect(
                        int(pos.x - entity_width // 2), int(pos.y - entity_height // 2),
                        entity_width, entity_height
                    )
                    if entity_width > 0 and entity_height > 0: # Only check collision for valid rects
                        if self.get_colliding_tiles(entity_rect): # Pass entity_rect for collision
                            pos.y -= this_step
                            moveable.velocity_y = 0
                            if step_size > 0:
                                moveable.on_ground = True
                            break
                    remaining_dy -= this_step
                
                if not moveable.on_ground and entity_width > 0 and entity_height > 0:
                    moveable.on_ground = self.check_if_on_ground(pos, entity_width, entity_height, is_player_entity)

            # Ground collision as fallback
            if pos.y >= self.ground_y_position:
                pos.y = self.ground_y_position
                moveable.velocity_y = 0
                moveable.on_ground = True

            # Update renderable image for Player
            if is_player_entity:
                player = esper.component_for_entity(entity, Player)
                if player.firing_start_time is not None:
                    image_key = 'fire_' + player.direction
                elif not moveable.on_ground:
                    image_key = 'jump_' + player.direction
                else:
                    image_key = player.direction
                
                if image_key in player.images:
                    if player.frame >= len(player.images[image_key]):
                        player.frame = 0
                    renderable.image = player.images[image_key][player.frame]
            # For Quirl, its animation (direction/frame) is handled in EnemySystem based on its AI

    def get_colliding_tiles(self, entity_rect): # Changed player_rect to entity_rect
        colliding_tiles = []
        for _, (renderable, position) in esper.get_components(Renderable, Position):
            # Skip if this is a player, an enemy (handled by AI/other checks), or projectile
            if esper.has_component(_, Player) or esper.has_component(_, Enemy) or esper.has_component(_, Projectile):
                continue
                
            image = renderable.image
            if image is None: continue
            bbox = image.get_bounding_rect()
            tile_rect = pygame.Rect(
                int(position.x - bbox.width // 2), int(position.y - bbox.height // 2),
                bbox.width, bbox.height
            )
            if entity_rect.colliderect(tile_rect):
                colliding_tiles.append((position, tile_rect))
        return colliding_tiles

    def check_if_on_ground(self, position, entity_width, entity_height, is_player): # Changed player_width/height
        # For non-player entities, simpler ground check might be needed if tile collision is too complex or not desired
        # For now, using the same detailed check.
        # If entity_width or entity_height is 0, it means we couldn't get dimensions (e.g., non-player without Enemy component)
        if entity_width == 0 or entity_height == 0:
             # Fallback to simple y-position check if dimensions are zero
            return position.y >= self.ground_y_position

        ground_check_rect = pygame.Rect(
            int(position.x - entity_width // 2),
            int(position.y - entity_height // 2) + 1,
            entity_width,
            entity_height
        )
        
        # Check for tile collisions
        # If it's not a player, we might want to simplify this or ensure enemies don't collide with all tiles.
        # For now, using the same logic.
        collisions = self.get_colliding_tiles(ground_check_rect)
        
        return bool(collisions) or position.y >= self.ground_y_position
