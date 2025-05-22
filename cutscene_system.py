import pygame
import esper
from components import *

# Moved from main.py
CUTSCENES = {
    "intro_cutscene": {"image": "cutscene1.png", "music": "cutscene1_music.mp3"}
    # Add more cutscenes here
}

# Moved from components.py
class Cutscene:
    def __init__(self, image_path, music_path, name):
        self.image_path = image_path
        self.music_path = music_path
        self.name = name # A unique name for this cutscene
        self.image = None # Loaded image
        self.loaded = False

# Moved and modified from main.py
class CutsceneSystem(esper.Processor):
    def __init__(self, scene_surface, render_system):
        super().__init__()
        self.scene_surface = scene_surface
        self.render_system = render_system
        self.in_cutscene = None
        self.cutscene_image = None
        self.cutscene_music = None
        self.cutscene_start_time = None # Added to track cutscene start time

    def start_cutscene(self, cutscene):
        if self.in_cutscene is not None:
            return

        if cutscene.name == 'hogwarts_cutscene':
            for entity, [player] in esper.get_components(Player):
                if player.flute:
                    if player.fluffy == 0:
                        cutscene.music_path = "hagrid.mp3"
                        cutscene.image_path = "fluffy1_cutscene.png"
                        player.fluffy = 1
                    elif player.fluffy == 1:
                        cutscene.music_path = "hagrid.mp3"
                        cutscene.image_path = "fluffy2_cutscene.png"
                        player.fluffy = 2
                    elif player.fluffy == 2:
                        cutscene.music_path = "hagrid.mp3"
                        cutscene.image_path = "fluffy3_cutscene.png"
                        player.fluffy = 3
                break

        self.cutscene_music = cutscene.music_path

        # Load cutscene image
        self.cutscene_image = pygame.image.load(cutscene.image_path)
        self.cutscene_image = pygame.transform.scale(self.cutscene_image, 
                                                   (self.scene_surface.get_width(), 
                                                    self.scene_surface.get_height()))
        self.in_cutscene = cutscene
        self.cutscene_start_time = pygame.time.get_ticks() # Record start time

        esper.switch_world("cutscene")
        esper.add_processor(self)

    def end_cutscene(self):
        if not self.in_cutscene:
            return
        
        esper.switch_world("map")

        cutscene = self.in_cutscene

        self.in_cutscene = None
        self.cutscene_image = None
        self.cutscene_start_time = None # Reset start time

        if cutscene.name == 'flute_cutscene':
            # Find and delete the flute entity
            for entity, [terrain] in esper.get_components(Terrain):
                if terrain.type == 'flute':
                    esper.delete_entity(entity)
                    self.render_system.remove_entity(entity)

                    for entity, [player] in esper.get_components(Player):
                        player.flute = True
                        break
                    break
        elif cutscene.name == 'hogwarts_cutscene':
            for entity, [player] in esper.get_components(Player):
                print("PLAYER FLUFFY: ", player.fluffy)
                if player.fluffy == 1:
                    self.start_cutscene(cutscene)
                    return
                elif player.fluffy == 2:
                    self.start_cutscene(cutscene)
                    return
                elif player.fluffy == 3:
                    from battle_scene import create_battle
                    create_battle(3, self, self.scene_surface, 16)  # Using battle #3 for flute battle
                    esper.switch_world('battle')
                    return
                break


    def process(self, dt):
        if not self.in_cutscene:
            return

        # Check for space bar to end cutscene after a delay
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and self.cutscene_start_time is not None and \
           (pygame.time.get_ticks() - self.cutscene_start_time >= 1000):
            self.end_cutscene()
            return

        # Draw cutscene image
        self.scene_surface.blit(self.cutscene_image, (0, 0)) 