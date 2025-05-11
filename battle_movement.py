import pygame
import esper
import time
from components import *


class BattleMovementSystem(esper.Processor):
    def __init__(self, gravity=200, jump_strength=120, move_speed=2):
        super().__init__()
        self.gravity = gravity
        self.jump_strength = jump_strength
        self.move_speed = move_speed
        self.ground_y_position = 16*5

    def animate(self, player):
        time = pygame.time.get_ticks() / 1000
        if time - player.last_frame_time > 0.15:
            player.frame = 1 - player.frame  # Toggle between 0 and 1
            player.last_frame_time = time  # Update the last frame switch time

    def process(self, dt):
        keys = pygame.key.get_pressed()

        for entity, (player, position, moveable, renderable) in esper.get_components(Player, Position, Moveable, Renderable):
            # Horizontal Movement
            if keys[pygame.K_LEFT]:
                position.x -= self.move_speed
                player.direction = 'left'
                self.animate(player)
            elif keys[pygame.K_RIGHT]:
                position.x += self.move_speed
                player.direction = 'right'
                self.animate(player)

            # Jumping
            if keys[pygame.K_SPACE] and moveable.on_ground:
                moveable.velocity_y = -self.jump_strength
                moveable.on_ground = False

            # Apply Gravity
            moveable.velocity_y += self.gravity * dt
            position.y += moveable.velocity_y * dt

            # Collision Detection and Handling
            # This is simplified; you'll need to add your terrain collision logic here
            if position.y >= self.ground_y_position:
                position.y = self.ground_y_position
                moveable.velocity_y = 0
                moveable.on_ground = True

            renderable.image = player.images[player.direction][player.frame]
