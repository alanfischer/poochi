import esper
import pygame
from components import Enemy
class MusicSystem(esper.Processor):
    def __init__(self, cutscene_system_ref, map_music_path='main.mp3', battle_music_path='battle.mp3'):
        self.cutscene_system = cutscene_system_ref  # Reference to get cutscene specific music
        self.map_music_path = map_music_path
        self.battle_music_path = battle_music_path
        
        self.current_music_path = None
        self.map_music_resume_pos_ms = 0
        
        self.world = None # Stores the string name of the current esper world

    def _play_music(self, music_path, loop=-1, start_ms=0):
        """
        Internal method to load and play music. Stops any currently playing music.
        """
        # Stop currently playing music cleanly before starting a new one.
        pygame.mixer.music.stop() 
        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(loop, start=start_ms / 1000.0) # Pygame play start is in seconds
            self.current_music_path = music_path
        except pygame.error as e:
            print(f"Error loading/playing music {music_path}: {e}")
            self.current_music_path = None

    def process(self, dt):
        new_world_name = esper.current_world # esper.current_world is the string name

        if self.world != new_world_name:
            print("World changed")
            previous_world_name = self.world
            self.world = new_world_name

            # Store map music position if we are leaving the map and map music was playing
            if previous_world_name == "map" and \
               self.current_music_path == self.map_music_path and \
               pygame.mixer.music.get_busy():
                self.map_music_resume_pos_ms = pygame.mixer.music.get_pos()
            
            # Handle music for the new world
            if new_world_name == "map":
                self._play_music(self.map_music_path, start_ms=self.map_music_resume_pos_ms)
            elif new_world_name == "battle":
                # Check if fighting Quirl by looking for Enemy component with quirl=True
                fighting_quirl = False
                for _, [enemy]in esper.get_components(Enemy):
                    if enemy.quirl:
                        fighting_quirl = True
                        break
                
                if fighting_quirl:
                    print("Fighting Quirl")
                    self._play_music('quirl.mp3')
                else:
                    self._play_music(self.battle_music_path)
            elif new_world_name == "cutscene":
                # cutscene_music attribute in CutsceneSystem holds the path string
                cutscene_music_path = self.cutscene_system.cutscene_music 
                if cutscene_music_path:
                    self._play_music(cutscene_music_path)
                else: 
                    # No specific music for this cutscene, or cutscene_music not set yet. Stop any playing music.
                    pygame.mixer.music.stop()
                    self.current_music_path = None
            # Add other world music handling here if needed 