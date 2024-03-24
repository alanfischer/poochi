import esper


class EncounterSystem(esper.Processor):
    def __init__(self, encounter_chance=0.05):
        self.encounter_chance = encounter_chance

    def process(self):
        # Check for player movement here
        # If player moved:
        if random.random() < self.encounter_chance:
            self.start_encounter()

    def start_encounter(self):
        # Start the battle sequence
        print("You ran into a slime!")
        # Transition to battle mode
