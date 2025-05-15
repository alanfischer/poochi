import esper
import random
import pygame
from components import *
from battle_scene import create_battle

class EncounterSystem(esper.Processor):
    def __init__(self, encounter_chance=0.05):
        self.encounter_chance = encounter_chance
        self.in_encounter = False
        self.current_world = "map"  # Track current world
        self.scene_surface = None
        self.TILE_SIZE = None
        self.battle_player_images = None

    def set_battle_params(self, scene_surface, TILE_SIZE, battle_player_images):
        self.scene_surface = scene_surface
        self.TILE_SIZE = TILE_SIZE
        self.battle_player_images = battle_player_images

    def process(self, dt):
        # Check for world changes
        if esper.current_world != self.current_world:
            self.handle_world_change(esper.current_world)
            self.current_world = esper.current_world

        # Only check for encounters in the map world
        if self.current_world == "map":
            _, (player, moveable) = esper.get_components(Player, Moveable)[0]
            if moveable and moveable.moved:
                moveable.moved = False
                if random.random() < self.encounter_chance:
                    # Create the battle scene before switching worlds
                    create_battle("grass", self, self.scene_surface, self.TILE_SIZE, self.battle_player_images)
                    esper.switch_world('battle_grass')

    def handle_world_change(self, new_world):
        if new_world.startswith("battle_"):
            pygame.mixer.music.pause()
            self.in_encounter = True
        elif new_world == "map":
            esper.delete_world("battle_grass")
            pygame.mixer.music.unpause()
            self.in_encounter = False

