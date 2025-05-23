from player import Player

import json

class Party:
    def __init__(self):
        self.players = []
        size = 1 # int(input("Party size > "))
        for i in range(size):
            print(f"Player {i + 1}")
            self.players.append(Player())
    
    def json(self):
        return json.dumps([{"name": p.name, "class": p.class_, "race": p.race} for p in self.players])
