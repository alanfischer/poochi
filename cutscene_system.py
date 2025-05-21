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
    def __init__(self, scene_surface):
        super().__init__()
        self.scene_surface = scene_surface
        self.in_cutscene = False
        self.cutscene_image = None
        self.cutscene_music = None

    def start_cutscene(self, image_path):
        if self.in_cutscene:
            return

        # Load cutscene image
        self.cutscene_image = pygame.image.load(image_path)
        self.cutscene_image = pygame.transform.scale(self.cutscene_image, 
                                                   (self.scene_surface.get_width(), 
                                                    self.scene_surface.get_height()))
        self.in_cutscene = True

    def end_cutscene(self):
        if not self.in_cutscene:
            return

        self.in_cutscene = False
        self.cutscene_image = None
        esper.switch_world("map") # Switch back to map world

    def process(self, dt):
        if not self.in_cutscene:
            return

        # Check for space bar to end cutscene
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.end_cutscene()
            return

        # Draw cutscene image
        self.scene_surface.blit(self.cutscene_image, (0, 0)) 