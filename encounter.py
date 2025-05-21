import esper
import random
import pygame
from components import *
from battle_scene import create_battle
from cutscene_system import *

class EncounterSystem(esper.Processor):
    def __init__(self, scene_surface, cutscene_system, tile_size, encounter_chance):
        self.encounter_chance = encounter_chance
        self.in_encounter = False
        self.current_world_name_for_cleanup = "map"  # Tracks the world name for cleanup logic
        self.scene_surface = scene_surface
        self.TILE_SIZE = tile_size
        self.cutscene_system = cutscene_system

    def start_world_cutscene(self, cutscene_data):
        """Called by MovementSystem to initiate a cutscene triggered by world interaction."""
        # Set the music path in CutsceneSystem for MusicSystem to pick up
        self.cutscene_system.cutscene_music = cutscene_data.music_path
        
        esper.switch_world("cutscene")
        
        esper.add_processor(self.cutscene_system)

        self.cutscene_system.start_cutscene(cutscene_data.image_path)

    def process(self, dt):
        new_world_name = esper.current_world

        # If world changed, handle cleanup of old world
        if new_world_name != self.current_world_name_for_cleanup:
            if self.current_world_name_for_cleanup == "battle" or self.current_world_name_for_cleanup == "cutscene":
                if new_world_name == "map": # Only delete if returning to map
                    esper.delete_world(self.current_world_name_for_cleanup)
            self.current_world_name_for_cleanup = new_world_name
        
        # Only check for encounters and cutscenes in the map world
        if new_world_name == "map":
            # Get player components only if they exist to prevent crashes during transitions
            player_components = esper.get_components(Player, Moveable, Position)
            if not player_components:
                return 
            _, (player, moveable, position) = player_components[0]
            
            # Check for random encounters
            if moveable and moveable.moved:
                moveable.moved = False
                if random.random() < self.encounter_chance:
                    battle_number = random.randint(1, 2)
                    create_battle(battle_number, self, self.scene_surface, self.TILE_SIZE)
                    esper.switch_world(f'battle')
                    self.in_encounter = True # Set encounter flag
        elif new_world_name == "battle":
            if not self.in_encounter: # Ensure this is set only once per battle entry
                self.in_encounter = True
        elif new_world_name != "map" and new_world_name != "battle": # e.g. cutscene
            self.in_encounter = False
