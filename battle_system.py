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

        for entity, (player, position, moveable, renderable) in esper.get_components(Player, Position, Moveable, Renderable):
            # Get the actual bounds of the player sprite
            # Use the base image for collision detection
            base_image = player.images[player.direction][0]
            bbox = base_image.get_bounding_rect()
            player_width = bbox.width
            player_height = bbox.height
            
            # Handle firing
            if keys[pygame.K_f] and player.firing_start_time is None:
                player.firing_start_time = current_time
                # Create projectile at player's position
                self.create_projectile(position.x, position.y, player.direction)
            elif player.firing_start_time is not None and current_time - player.firing_start_time >= 0.25:
                player.firing_start_time = None

            # Store original position
            original_x = position.x
            original_y = position.y
            
            # Calculate movement deltas with delta time
            dx = 0
            if keys[pygame.K_LEFT]:
                dx = -self.move_speed * dt
                player.direction = 'left'
                self.animate(player)
            elif keys[pygame.K_RIGHT]:
                dx = self.move_speed * dt
                player.direction = 'right'
                self.animate(player)

            # Apply horizontal movement with continuous collision check
            if dx != 0:
                # Move in smaller steps to prevent tunneling
                remaining_dx = dx
                step_size = 1 if dx > 0 else -1
                
                while abs(remaining_dx) > 0:
                    # Calculate step size for this iteration
                    this_step = step_size if abs(remaining_dx) > 1 else remaining_dx
                    
                    # Try to move
                    position.x += this_step
                    
                    # Check collision at new position
                    player_rect = pygame.Rect(
                        int(position.x - player_width // 2),
                        int(position.y - player_height // 2),
                        player_width,
                        player_height
                    )
                    
                    # If collision occurred, revert the step and stop
                    collisions = self.get_colliding_tiles(player_rect)
                    if collisions:
                        position.x -= this_step
                        break
                    
                    remaining_dx -= this_step
                
                # After horizontal movement, verify if we're still on ground
                moveable.on_ground = self.check_if_on_ground(position, player_width, player_height)

            # Enforce horizontal boundaries
            if position.x < self.left_boundary:
                position.x = self.left_boundary
            elif position.x > self.right_boundary:
                position.x = self.right_boundary

            # Handle jumping
            if keys[pygame.K_SPACE] and moveable.on_ground:
                moveable.velocity_y = -self.jump_strength
                moveable.on_ground = False

            if keys[pygame.K_ESCAPE]:
                esper.switch_world('map')

            # Apply gravity with delta time
            moveable.velocity_y += self.gravity * dt
            
            # Clamp maximum fall speed to prevent tunneling
            max_fall_speed = 300
            moveable.velocity_y = min(moveable.velocity_y, max_fall_speed)
            
            # Calculate vertical movement
            dy = moveable.velocity_y * dt
            
            # Check if we're still on ground before moving
            was_on_ground = moveable.on_ground
            
            # Apply vertical movement with continuous collision check
            if dy != 0:
                # Move in smaller steps to prevent tunneling
                remaining_dy = dy
                step_size = 1 if dy > 0 else -1
                
                # Only reset on_ground if we're moving upward or were already in the air
                if step_size < 0 or not was_on_ground:
                    moveable.on_ground = False
                
                while abs(remaining_dy) > 0:
                    # Calculate step size for this iteration
                    this_step = step_size if abs(remaining_dy) > 1 else remaining_dy
                    
                    # Try to move
                    position.y += this_step
                    
                    # Check collision at new position
                    player_rect = pygame.Rect(
                        int(position.x - player_width // 2),
                        int(position.y - player_height // 2),
                        player_width,
                        player_height
                    )
                    
                    # If collision occurred, handle it and stop
                    collisions = self.get_colliding_tiles(player_rect)
                    if collisions:
                        position.y -= this_step  # Revert the step
                        moveable.velocity_y = 0  # Stop vertical movement
                        
                        if step_size > 0:  # Moving down
                            moveable.on_ground = True
                        break
                    
                    remaining_dy -= this_step
                
                # After vertical movement, verify if we're still on ground
                if not moveable.on_ground:  # Only check if we're not already known to be on ground
                    moveable.on_ground = self.check_if_on_ground(position, player_width, player_height)

            # Ground collision as fallback
            if position.y >= self.ground_y_position:
                position.y = self.ground_y_position
                moveable.velocity_y = 0
                moveable.on_ground = True

            # Update image based on movement and firing state
            if player.firing_start_time is not None:
                image = 'fire_' + player.direction
            elif not moveable.on_ground:
                image = 'jump_' + player.direction
            else:
                image = player.direction

            if player.frame >= len(player.images[image]):
                player.frame = 0

            renderable.image = player.images[image][player.frame]

    def get_colliding_tiles(self, player_rect):
        colliding_tiles = []
        
        for _, (renderable, position) in esper.get_components(Renderable, Position):
            # Skip if this is a player or projectile
            if esper.has_component(_, Player) or esper.has_component(_, Projectile):
                continue
                
            # Get the actual bounds of the non-transparent pixels
            image = renderable.image
            if image is None:  # Skip if no image
                continue
                
            # Get the bounding box of non-transparent pixels
            bbox = image.get_bounding_rect()
            
            # Create a rect for the tile, accounting for centered position and actual bounds
            tile_rect = pygame.Rect(
                int(position.x - bbox.width // 2),  # Center based on actual visible width
                int(position.y - bbox.height // 2),  # Center based on actual visible height
                bbox.width,
                bbox.height
            )
            
            if player_rect.colliderect(tile_rect):
                colliding_tiles.append((position, tile_rect))
        
        return colliding_tiles

    def check_if_on_ground(self, position, player_width, player_height):
        # Check one pixel below the player for ground
        ground_check_rect = pygame.Rect(
            int(position.x - player_width // 2),
            int(position.y - player_height // 2) + 1,  # Check one pixel below
            player_width,
            player_height
        )
        
        # Check for tile collisions
        collisions = self.get_colliding_tiles(ground_check_rect)
        
        # Also check for world ground
        return bool(collisions) or position.y >= self.ground_y_position
