#!/usr/bin/env python3

from aidm import AIDM
from party import Party
from dungeon import Dungeon

if __name__ == "__main__":
    # dungeon = Dungeon()
    # import json
    # print(json.dumps(dungeon.to_dict()))
      # Gets the start room at origin on floor 0
    # random_room = dungeon.get_room((2, -1, 0))  # Gets room at x=2, y=-1 on floor 0
    # nonexistent = dungeon.get_room((0, 0, 1))  # Returns None (floor 1 not generated yet)
    
    party = Party()
    dungeon = Dungeon()

    AIDM(party, dungeon).run()
