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
        self.current_world = "map"  # Track current world
        self.scene_surface = scene_surface
        self.TILE_SIZE = tile_size
        self.music_pos = 0  # Added to store current music position
        self.cutscene_system = cutscene_system
        self.cutscene_music_path = None # Added to store cutscene music path

    def process(self, dt):
        # Check for world changes
        if esper.current_world != self.current_world:
            self.handle_world_change(esper.current_world)
            self.current_world = esper.current_world

        # Only check for encounters and cutscenes in the map world
        if self.current_world == "map":
            _, (player, moveable, position) = esper.get_components(Player, Moveable, Position)[0]
            
            # Check for cutscene triggers
            if moveable and moveable.moved:
                for entity, (cutscene, pos) in esper.get_components(Cutscene, Position):
                    if pos.x == position.x and pos.y == position.y:
                        self.music_pos = pygame.mixer.music.get_pos()
                        pygame.mixer.music.pause()
                        self.cutscene_music_path = cutscene.music_path # Store music path for handle_world_change

                        esper.switch_world("cutscene") # Switch to cutscene world
                        
                        # Add necessary systems to the "cutscene" world
                        esper.add_processor(self.cutscene_system)

                        # Start cutscene visuals (music is handled by handle_world_change)
                        self.cutscene_system.start_cutscene(cutscene.image_path, cutscene.music_path)
                        return

            # Check for random encounters
            if moveable and moveable.moved:
                moveable.moved = False
                if random.random() < self.encounter_chance:
                    # Randomly choose between battle 1 and 2
                    battle_number = random.randint(1, 2)
                    # Create the battle scene before switching worlds
                    create_battle(battle_number, self, self.scene_surface, self.TILE_SIZE)
                    esper.switch_world(f'battle')

    def handle_world_change(self, new_world):
        if new_world == "battle":
            # Store current music position and pause
            self.music_pos = pygame.mixer.music.get_pos()
            pygame.mixer.music.pause()
            # Play battle music
            pygame.mixer.music.load('battle.mp3')
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely
            self.in_encounter = True
        elif new_world == "map":
            # Stop battle music or cutscene music
            pygame.mixer.music.stop()
            # Resume main music from where it left off
            pygame.mixer.music.load('main.mp3')
            pygame.mixer.music.play(-1, start=self.music_pos / 1000.0)  # Convert ms to seconds
            # Delete the current battle world or cutscene world
            if self.current_world == "battle" or self.current_world == "cutscene":
                esper.delete_world(self.current_world)
            self.in_encounter = False
        elif new_world == "cutscene":
            # Store current music position and pause
            self.music_pos = pygame.mixer.music.get_pos()
            pygame.mixer.music.pause()
            # Play cutscene music if path is available
            if self.cutscene_music_path:
                pygame.mixer.music.load(self.cutscene_music_path)
                pygame.mixer.music.play(-1)  # -1 means loop indefinitely
            # No need to set self.in_encounter as it's not an encounter

