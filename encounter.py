import esper
import random
import pygame
from components import *


class EncounterSystem(esper.Processor):
    def __init__(self, encounter_chance=0.05):
        self.encounter_chance = encounter_chance
        self.in_encounter = False

    def process(self, dt):
        _, (player, moveable) = esper.get_components(Player, Moveable)[0]
        if moveable and moveable.moved:
            moveable.moved = False
            if random.random() < self.encounter_chance:
                self.start_encounter()

    def start_encounter(self):
        pygame.mixer.music.pause()
        esper.switch_world('battle_grass')
        self.in_encounter = True

    def end_encounter(self):
        pygame.mixer.music.unpause()
        esper.switch_world('map')
        self.in_encounter = False
