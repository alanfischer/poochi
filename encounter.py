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
        self.music_pos = 0  # Added to store current music position

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
                    create_battle("background", self, self.scene_surface, self.TILE_SIZE, self.battle_player_images)
                    esper.switch_world('battle_background')

    def handle_world_change(self, new_world):
        if new_world.startswith("battle_"):
            # Store current music position and pause
            self.music_pos = pygame.mixer.music.get_pos()
            pygame.mixer.music.pause()
            # Play battle music
            pygame.mixer.music.load('battle.mp3')
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely
            self.in_encounter = True
        elif new_world == "map":
            # Stop battle music
            pygame.mixer.music.stop()
            # Resume main music from where it left off
            pygame.mixer.music.load('main.mp3')
            pygame.mixer.music.play(-1, start=self.music_pos / 1000.0)  # Convert ms to seconds
            esper.delete_world("battle_background")
            self.in_encounter = False

